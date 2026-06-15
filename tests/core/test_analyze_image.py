"""Tests for the AnalyzeImage use-case (the analyzer loop)."""

from __future__ import annotations

import logging
import re

import pytest

from regis.core.application.analyze_image import (
    AnalysisResult,
    AnalyzeImage,
    AnalyzerOutcome,
)
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import (
    AnalyzerError,
    PlaybookError,
    RegistryError,
    ToolError,
)
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeReportSink, FakeToolRunner

IMAGE = ImageReference(registry="reg.example", repository="ns/app", tag="1.0")


def _make_use_case(*, tools=None, sink=None):
    """Build an AnalyzeImage with in-memory factories."""
    return AnalyzeImage(
        tools=tools or FakeToolRunner(),
        inspector_factory=lambda image: FakeImageInspector(),
        sink=sink or FakeReportSink(),
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


# ---------------------------------------------------------------------------
# run_and_evaluate tests
# ---------------------------------------------------------------------------


class _SimpleCtxAnalyzer:
    """Minimal ctx-based analyzer for run_and_evaluate tests."""

    name = "a"

    def analyze(self, ctx: AnalysisContext) -> dict:
        return {"analyzer": self.name, "ok": True}

    def validate(self, report: dict) -> None:
        pass


def test_run_and_evaluate_happy_path(monkeypatch):
    """Happy path: run_and_evaluate returns an AnalysisResult with correct shape."""
    sink = FakeReportSink()
    uc = _make_use_case(sink=sink)

    # Monkeypatch validate_report to be a no-op (avoids schema validation).
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )
    # Monkeypatch run_playbooks to return the envelope unchanged (no playbook files).
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        lambda paths, report, show_rules=False, on_progress=None: dict(report),
    )

    result = uc.run_and_evaluate(
        IMAGE,
        {"a": _SimpleCtxAnalyzer},
        url="nginx:latest",
        digest="sha256:d",
        formats=["json"],
    )

    assert isinstance(result, AnalysisResult)
    assert result.report["results"]["a"] == {"analyzer": "a", "ok": True}
    assert result.report["schemaVersion"] is not None
    assert result.report["request"]["url"] == "nginx:latest"
    assert result.report["request"]["digest"] == "sha256:d"
    assert result.report["request"]["registry"] == IMAGE.registry
    assert result.report["request"]["repository"] == IMAGE.repository
    assert result.report["request"]["tag"] == IMAGE.tag
    assert result.report["request"]["analyzers"] == sorted(["a"])
    # Sink received exactly one emission with the right formats.
    assert len(sink.emitted) == 1
    _report_obj, fmt_tuple = sink.emitted[0]
    assert fmt_tuple == ("json",)


def test_run_and_evaluate_metadata_included(monkeypatch):
    """metadata kwarg is forwarded into the envelope."""
    sink = FakeReportSink()
    uc = _make_use_case(sink=sink)
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        lambda paths, report, show_rules=False, on_progress=None: dict(report),
    )

    result = uc.run_and_evaluate(
        IMAGE,
        {"a": _SimpleCtxAnalyzer},
        url="nginx:latest",
        digest="sha256:d",
        formats=["json"],
        metadata={"ci": {"x": "1"}},
    )
    assert result.report["metadata"] == {"ci": {"x": "1"}}


def test_run_and_evaluate_no_metadata_key_absent(monkeypatch):
    """Without metadata kwarg, 'metadata' key must be absent from the envelope."""
    sink = FakeReportSink()
    uc = _make_use_case(sink=sink)
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        lambda paths, report, show_rules=False, on_progress=None: dict(report),
    )

    result = uc.run_and_evaluate(
        IMAGE,
        {"a": _SimpleCtxAnalyzer},
        url="nginx:latest",
        digest="sha256:d",
        formats=["json"],
    )
    assert "metadata" not in result.report


def test_run_and_evaluate_on_playbook_progress_callback(monkeypatch):
    """on_playbook_progress callback is forwarded and invoked by run_playbooks."""
    sink = FakeReportSink()
    uc = _make_use_case(sink=sink)
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )

    progress_calls: list[str] = []

    def _fake_run_playbooks(paths, report, show_rules=False, on_progress=None):
        if on_progress is not None:
            on_progress("step1")
            on_progress("step2")
        return dict(report)

    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        _fake_run_playbooks,
    )

    uc.run_and_evaluate(
        IMAGE,
        {"a": _SimpleCtxAnalyzer},
        url="nginx:latest",
        digest="sha256:d",
        formats=["json"],
        on_playbook_progress=progress_calls.append,
    )
    assert progress_calls == ["step1", "step2"]


def _fake_run_playbooks_with_rules(paths, report, show_rules=False, on_progress=None):
    """Shared fake run_playbooks: returns a report with playbooks[0] containing
    one failed critical rule (x), one failed warning rule (z), one failed info
    rule (i), and one passed critical rule (y — must never breach)."""
    merged = dict(report)
    merged["playbooks"] = [
        {
            "rules": [
                {"slug": "x", "passed": False, "level": "critical"},
                {"slug": "z", "passed": False, "level": "warning"},
                {"slug": "i", "passed": False, "level": "info"},
                {"slug": "y", "passed": True, "level": "critical"},
            ],
            "rules_summary": {"critical": 1, "warning": 1, "info": 1},
            "tier": "bronze",
            "badges": ["badge-a"],
        }
    ]
    return merged


def test_run_and_evaluate_breach_computation(monkeypatch):
    """Breach computation: rules are promoted and filtered by fail_level."""
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        _fake_run_playbooks_with_rules,
    )

    def _run(**kwargs):
        sink = FakeReportSink()
        uc = _make_use_case(sink=sink)
        return uc.run_and_evaluate(
            IMAGE,
            {"a": _SimpleCtxAnalyzer},
            url="nginx:latest",
            digest="sha256:d",
            formats=["json"],
            show_rules=True,
            **kwargs,
        )

    # fail_level="critical" — only the failed critical rule (x) breaches.
    result = _run(fail_level="critical")
    assert result.has_breaches is True
    assert result.breach_count == 1
    assert result.breached_slugs == ["x"]

    # fail_level="warning" — failed critical (x) and failed warning (z) breach.
    result = _run(fail_level="warning")
    assert result.has_breaches is True
    assert result.breach_count == 2
    assert result.breached_slugs == ["x", "z"]

    # fail_level="info" — all three failed rules (x, z, i) breach.
    result = _run(fail_level="info")
    assert result.has_breaches is True
    assert result.breach_count == 3
    assert result.breached_slugs == ["x", "z", "i"]

    # fail_level="none" — nothing breaches regardless of rule failures.
    result = _run(fail_level="none")
    assert result.has_breaches is False
    assert result.breach_count == 0


def test_run_and_evaluate_passed_rule_not_breached(monkeypatch):
    """Passed rules (even critical) are never counted as breaches."""
    sink = FakeReportSink()
    uc = _make_use_case(sink=sink)
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )

    def _fake_run_playbooks(paths, report, show_rules=False, on_progress=None):
        merged = dict(report)
        merged["playbooks"] = [
            {
                "rules": [
                    {"slug": "ok", "passed": True, "level": "critical"},
                ],
                "rules_summary": {},
            }
        ]
        return merged

    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        _fake_run_playbooks,
    )

    result = uc.run_and_evaluate(
        IMAGE,
        {"a": _SimpleCtxAnalyzer},
        url="nginx:latest",
        digest="sha256:d",
        formats=["json"],
        show_rules=True,
        fail_level="critical",
    )
    assert result.has_breaches is False
    assert result.breach_count == 0
    assert result.breached_slugs == []


def test_run_and_evaluate_show_rules_gating(monkeypatch):
    """Top-level rules/tier/badges/rules_summary are promoted only when show_rules=True."""
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        _fake_run_playbooks_with_rules,
    )

    def _run(show_rules):
        sink = FakeReportSink()
        uc = _make_use_case(sink=sink)
        return uc.run_and_evaluate(
            IMAGE,
            {"a": _SimpleCtxAnalyzer},
            url="nginx:latest",
            digest="sha256:d",
            formats=["json"],
            show_rules=show_rules,
        )

    # show_rules=False (default) — top-level keys must be absent.
    result_no = _run(show_rules=False)
    assert "rules" not in result_no.report
    assert "tier" not in result_no.report
    assert "badges" not in result_no.report
    assert "rules_summary" not in result_no.report
    # No rules promoted → no breaches.
    assert result_no.has_breaches is False
    assert result_no.breach_count == 0

    # show_rules=True — top-level keys must be present and equal playbooks[0] values.
    result_yes = _run(show_rules=True)
    pb0 = result_yes.report["playbooks"][0]
    assert result_yes.report["rules"] == pb0["rules"]
    assert result_yes.report["rules_summary"] == pb0["rules_summary"]
    assert result_yes.report["tier"] == pb0["tier"]
    assert result_yes.report["badges"] == pb0["badges"]


def test_run_and_evaluate_empty_selected_raises(monkeypatch):
    """Empty selected dict raises AnalyzerError (all analyzers 'failed')."""
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: None,
    )
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        lambda paths, report, show_rules=False, on_progress=None: dict(report),
    )
    uc = _make_use_case()
    with pytest.raises(AnalyzerError):
        uc.run_and_evaluate(
            IMAGE,
            {},
            url="nginx:latest",
            digest="sha256:d",
            formats=["json"],
        )


def test_run_and_evaluate_validate_failure_propagates(monkeypatch):
    """PlaybookError from validate_report propagates to the caller."""
    monkeypatch.setattr(
        "regis.core.application.analyze_image.validate_report",
        lambda report: (_ for _ in ()).throw(PlaybookError("bad")),
    )
    monkeypatch.setattr(
        "regis.core.application.analyze_image.run_playbooks",
        lambda paths, report, show_rules=False, on_progress=None: dict(report),
    )
    uc = _make_use_case()
    with pytest.raises(PlaybookError, match="bad"):
        uc.run_and_evaluate(
            IMAGE,
            {"a": _SimpleCtxAnalyzer},
            url="nginx:latest",
            digest="sha256:d",
            formats=["json"],
        )
