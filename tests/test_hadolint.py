"""Tests for the hadolint analyzer."""

import pytest

from regis.analyzers.hadolint import HadolintAnalyzer
from tests.fakes import FakeImageInspector, FakeToolRunner, make_ctx

_HISTORY_WITH_ENTRIES = [
    {"created_by": '/bin/sh -c #(nop)  CMD ["python3"]'},
    {"created_by": "bazel build //common:rootfs"},
]

_MANIFEST = {"mediaType": "single", "config": {"digest": "sha256:c"}}


class TestHadolintAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return HadolintAnalyzer()

    def _make_ctx(self, history, issues, platform=None):
        inspector = FakeImageInspector(
            manifest=_MANIFEST,
            blob={"history": history},
        )
        tools = FakeToolRunner(lint_dockerfile=issues)
        return make_ctx(inspector=inspector, tools=tools, platform=platform)

    def test_hadolint_uses_context(self, analyzer):
        assert HadolintAnalyzer.uses_context is True

    def test_hadolint_passes(self, analyzer):
        ctx = self._make_ctx(_HISTORY_WITH_ENTRIES, [])
        report = analyzer.analyze(ctx)

        analyzer.validate(report)
        assert report["passed"] is True
        assert report["issues_count"] == 0
        assert report["issues_by_level"]["error"] == 0
        assert report["issues_by_level"]["warning"] == 0

    def test_hadolint_fails(self, analyzer):
        issues = [
            {
                "code": "DL3008",
                "column": 1,
                "file": "-",
                "level": "warning",
                "line": 2,
                "message": "Pin versions in apt get install.",
            }
        ]
        ctx = self._make_ctx(
            [{"created_by": "apt-get install curl"}],
            issues,
        )
        report = analyzer.analyze(ctx)

        analyzer.validate(report)
        assert report["passed"] is False
        assert report["issues_count"] == 1
        assert report["issues_by_level"]["warning"] == 1
        assert report["issues_by_level"]["error"] == 0
        assert report["issues"][0]["code"] == "DL3008"
        assert report["issues"][0]["level"] == "warning"
