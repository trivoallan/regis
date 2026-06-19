"""Exhaustive tests for the hadolint analyzer (ctx-based)."""

from __future__ import annotations

from typing import Any

import pytest

from regis.core.domain.analyzers.hadolint import HadolintAnalyzer
from regis.core.domain.errors import ToolError
from tests.fakes import FakeImageInspector, FakeToolRunner, make_ctx

_MANIFEST_SINGLE = {"mediaType": "single", "config": {"digest": "sha256:c"}}
_HISTORY_SIMPLE = [{"created_by": "RUN echo 1"}]
_HISTORY_MIXED = [
    {"created_by": '/bin/sh -c #(nop) CMD ["python3"]'},
    {"created_by": "/bin/sh -c RUN echo 1"},
]


class _ErrorLintToolRunner(FakeToolRunner):
    """FakeToolRunner whose lint_dockerfile always raises ToolError."""

    def lint_dockerfile(self, dockerfile: str) -> list[dict[str, Any]]:
        raise ToolError("hadolint binary not found")


class TestHadolintAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return HadolintAnalyzer()

    def _simple_ctx(
        self,
        history=None,
        issues=None,
        platform=None,
    ):
        inspector = FakeImageInspector(
            manifest=_MANIFEST_SINGLE,
            blob={"history": history if history is not None else _HISTORY_SIMPLE},
        )
        tools = FakeToolRunner(lint_dockerfile=issues if issues is not None else [])
        return make_ctx(inspector=inspector, tools=tools, platform=platform)

    def test_hadolint_logic(self, analyzer):
        # Platform split: explicit linux/amd64
        ctx = self._simple_ctx(
            history=_HISTORY_MIXED,
            issues=[{"level": "warning", "message": "m"}],
            platform="linux/amd64",
        )
        res = analyzer.analyze(ctx)
        assert 'CMD ["python3"]' in res["dockerfile"]
        assert "RUN echo 1" in res["dockerfile"]

        # Platform split: bare arch → fallback to linux/<arch>
        ctx2 = self._simple_ctx(
            history=_HISTORY_MIXED,
            issues=[{"level": "warning", "message": "m"}],
            platform="amd64",
        )
        res2 = analyzer.analyze(ctx2)
        assert res2["issues_count"] == 1

    def test_hadolint_errors_exhaustive(self, analyzer):
        # Hadolint binary missing — ToolError propagates (not caught in analyzer).
        inspector = FakeImageInspector(
            manifest=_MANIFEST_SINGLE,
            blob={"history": _HISTORY_SIMPLE},
        )
        ctx = make_ctx(
            inspector=inspector,
            tools=_ErrorLintToolRunner(),
        )
        with pytest.raises(ToolError):
            analyzer.analyze(ctx)

        # Hadolint command failure but valid output (empty list = 0 violations).
        ctx_ok = self._simple_ctx(history=_HISTORY_SIMPLE, issues=[])
        res = analyzer.analyze(ctx_ok)
        assert res["issues_count"] == 0

        # Empty history → only "FROM scratch" in dockerfile.
        ctx_empty = self._simple_ctx(history=[{"created_by": ""}], issues=[])
        res_empty = analyzer.analyze(ctx_empty)
        assert "FROM scratch" in res_empty["dockerfile"]

    def test_tool_error_propagates(self, analyzer):
        """ToolError from lint_dockerfile must propagate unchanged."""
        inspector = FakeImageInspector(
            manifest=_MANIFEST_SINGLE,
            blob={"history": _HISTORY_SIMPLE},
        )
        ctx = make_ctx(inspector=inspector, tools=_ErrorLintToolRunner())
        with pytest.raises(ToolError, match="hadolint binary not found"):
            analyzer.analyze(ctx)

    def test_unrecognized_issue_level(self, analyzer):
        """Unrecognized hadolint levels are stored in issues_by_level as-is."""
        issues = [{"code": "DL9999", "level": "custom", "message": "m", "line": 1}]
        ctx = self._simple_ctx(history=_HISTORY_SIMPLE, issues=issues)
        res = analyzer.analyze(ctx)
        assert res["issues_by_level"].get("custom") == 1
        assert res["issues_count"] == 1

    def test_registry_error_propagates(self, analyzer):
        """RegistryError from config fetch must propagate unchanged out of analyze()."""
        from regis.core.domain.errors import RegistryError

        class _FailingInspector(FakeImageInspector):
            def get_manifest(self, reference: str) -> dict:  # type: ignore[override]
                raise RegistryError("connection refused")

        ctx = make_ctx(inspector=_FailingInspector())
        with pytest.raises(RegistryError, match="connection refused"):
            analyzer.analyze(ctx)
