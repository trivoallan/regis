"""Tests for the AnalyzeImage use-case (the analyzer loop)."""

from __future__ import annotations

import logging
import re

import pytest

from regis.core.application.analyze_image import AnalyzeImage, AnalyzerOutcome
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import AnalyzerError, RegistryError, ToolError
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner

IMAGE = ImageReference(registry="reg.example", repository="ns/app", tag="1.0")


def _make_use_case(*, tools=None):
    """Build an AnalyzeImage with in-memory factories."""
    return AnalyzeImage(
        tools=tools or FakeToolRunner(),
        inspector_factory=lambda image: FakeImageInspector(),
    )


class _CtxAnalyzer:
    """Ctx-based analyzer; reads tools + image from the context."""

    name = "ctxone"

    def analyze(self, ctx: AnalysisContext) -> dict:
        assert isinstance(ctx, AnalysisContext)
        return {
            "analyzer": self.name,
            "repository": ctx.image.repository,
            "vulns": ctx.tools.scan_vulnerabilities(ctx.image).get("count", 0),
        }

    def validate(self, report: dict) -> None:
        pass


class _SimpleAnalyzer:
    """Minimal ctx-based analyzer returning a fixed report."""

    name = "simpleone"

    def analyze(self, ctx: AnalysisContext) -> dict:
        return {"analyzer": self.name, "repository": ctx.image.repository}

    def validate(self, report: dict) -> None:
        pass


def _raiser(name, exc):
    class _Boom:
        def analyze(self, ctx):
            raise exc

        def validate(self, report):
            pass

    _Boom.name = name
    return _Boom


def test_dispatch_context_branch_uses_tools_and_image():
    uc = _make_use_case(tools=FakeToolRunner(scan_vulnerabilities={"count": 7}))
    reports = uc.run(IMAGE, {"ctxone": _CtxAnalyzer})
    assert reports["ctxone"] == {
        "analyzer": "ctxone",
        "repository": "ns/app",
        "vulns": 7,
    }


def test_run_collects_multiple_and_keys_by_selected_name():
    uc = _make_use_case(tools=FakeToolRunner(scan_vulnerabilities={"count": 1}))
    reports = uc.run(IMAGE, {"a": _CtxAnalyzer, "b": _SimpleAnalyzer})
    assert set(reports) == {"a", "b"}


def test_validate_is_called_and_failure_is_captured():
    class _BadValidate:
        name = "bad"

        def analyze(self, ctx):
            return {"x": 1}

        def validate(self, report):
            raise AnalyzerError("schema nope")

    uc = _make_use_case()
    reports = uc.run(IMAGE, {"bad": _BadValidate})
    assert reports["bad"] == {
        "analyzer": "bad",
        "error": {"type": "analysis", "message": "schema nope"},
    }


@pytest.mark.parametrize(
    ("exc", "etype"),
    [
        (RegistryError("reg down"), "registry"),
        (AnalyzerError("bad data"), "analysis"),
        (ToolError("grype missing"), "tool"),
        (RuntimeError("???"), "unexpected"),
    ],
)
def test_errors_are_classified_into_stubs(exc, etype):
    uc = _make_use_case()
    reports = uc.run(IMAGE, {"boom": _raiser("boom", exc)})
    assert reports["boom"]["analyzer"] == "boom"
    assert reports["boom"]["error"]["type"] == etype
    assert reports["boom"]["error"]["message"] == str(exc)


def test_failing_analyzer_does_not_abort_others():
    uc = _make_use_case()
    selected = {"ok": _SimpleAnalyzer, "boom": _raiser("boom", ToolError("x"))}
    reports = uc.run(IMAGE, selected)
    assert reports["ok"]["analyzer"] == "simpleone"
    assert reports["boom"]["error"]["type"] == "tool"


def test_on_progress_receives_one_outcome_per_analyzer():
    uc = _make_use_case()
    seen: list[AnalyzerOutcome] = []
    selected = {"ok": _SimpleAnalyzer, "boom": _raiser("boom", ToolError("x"))}
    uc.run(IMAGE, selected, on_progress=seen.append)
    by_name = {o.name: o for o in seen}
    assert set(by_name) == {"ok", "boom"}
    assert by_name["ok"].error_type is None
    assert by_name["boom"].error_type == "tool"
    assert by_name["boom"].error_message == "x"
    assert all(o.elapsed >= 0.0 for o in seen)


def test_run_one_returns_report_and_reraises():
    uc = _make_use_case(tools=FakeToolRunner(scan_vulnerabilities={"count": 3}))
    assert uc.run_one(IMAGE, _CtxAnalyzer)["vulns"] == 3
    with pytest.raises(ToolError, match="x"):
        uc.run_one(IMAGE, _raiser("boom", ToolError("x")))


def test_run_one_logs_debug_timing(caplog):
    uc = _make_use_case()
    with caplog.at_level(logging.DEBUG, logger="regis.core.application.analyze_image"):
        uc.run_one(IMAGE, _SimpleAnalyzer)
    recs = [
        r
        for r in caplog.records
        if "simpleone" in r.getMessage() and "finished in" in r.getMessage()
    ]
    assert len(recs) == 1
    assert recs[0].levelno == logging.DEBUG
    assert re.search(r"finished in \d+\.\d{2}s", recs[0].getMessage())


def test_run_logs_timing_even_on_failure(caplog):
    uc = _make_use_case()
    with caplog.at_level(logging.DEBUG, logger="regis.core.application.analyze_image"):
        uc.run(IMAGE, {"boom": _raiser("boom", AnalyzerError("kaboom"))})
    recs = [
        r
        for r in caplog.records
        if "boom" in r.getMessage() and "finished in" in r.getMessage()
    ]
    assert len(recs) == 1


def test_run_caps_workers_at_selection_size_and_runs_serially():
    # max_workers larger than selection must still succeed (no crash, all run).
    uc = _make_use_case()
    reports = uc.run(IMAGE, {"a": _SimpleAnalyzer}, max_workers=10)
    assert set(reports) == {"a"}
    reports = uc.run(IMAGE, {"a": _SimpleAnalyzer}, max_workers=1)
    assert set(reports) == {"a"}
    reports = uc.run(IMAGE, {"a": _SimpleAnalyzer}, max_workers=0)
    assert set(reports) == {"a"}


def test_run_empty_selection_returns_empty():
    uc = _make_use_case()
    assert uc.run(IMAGE, {}) == {}
