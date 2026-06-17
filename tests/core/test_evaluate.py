"""Tests for the Evaluate dry-run use-case."""

from __future__ import annotations

import pytest

from regis.core.application.evaluate import Evaluate
from regis.core.domain.errors import PlaybookError
from tests.fakes import FakePresentationRenderer, FakeReportSink


def test_evaluate_runs_playbooks_validates_and_emits(monkeypatch):
    sink = FakeReportSink()
    presentation = FakePresentationRenderer()
    captured: dict = {}

    def fake_run_playbooks(paths, report, *, show_rules=False, on_progress=None):
        captured["paths"] = paths
        captured["show_rules"] = show_rules
        return {**report, "playbooks": []}

    def fake_validate(report):
        captured["validated"] = report

    monkeypatch.setattr(
        "regis.core.application.evaluate.run_playbooks", fake_run_playbooks
    )
    monkeypatch.setattr(
        "regis.core.application.evaluate.validate_report", fake_validate
    )

    report = {"results": {}, "request": {}}
    result = Evaluate(sink=sink, presentation=presentation).run(
        report, formats=["json"], playbook_paths=("pb.yaml",)
    )

    assert captured["paths"] == ("pb.yaml",)
    assert captured["show_rules"] is False  # evaluate never promotes top-level rules
    assert result == {"results": {}, "request": {}, "playbooks": []}
    assert captured["validated"] == result
    assert len(sink.emitted) == 1
    emitted_report, emitted_formats = sink.emitted[0]
    assert emitted_report.payload == result
    assert emitted_formats == ("json",)
    assert len(presentation.rendered) == 1
    assert presentation.rendered[0].payload == result


def test_evaluate_propagates_playbook_error_without_emitting(monkeypatch):
    sink = FakeReportSink()
    presentation = FakePresentationRenderer()
    monkeypatch.setattr(
        "regis.core.application.evaluate.run_playbooks",
        lambda *a, **k: {"x": 1},
    )

    def boom(report):
        raise PlaybookError("bad schema")

    monkeypatch.setattr("regis.core.application.evaluate.validate_report", boom)

    with pytest.raises(PlaybookError, match="bad schema"):
        Evaluate(sink=sink, presentation=presentation).run(
            {"results": {}}, formats=["json"]
        )
    assert sink.emitted == []  # validation failure short-circuits emission
    assert presentation.rendered == []


def test_evaluate_forwards_progress_callback(monkeypatch):
    sink = FakeReportSink()
    seen: list[str] = []

    def fake_run_playbooks(paths, report, *, show_rules=False, on_progress=None):
        if on_progress is not None:
            on_progress("Playbook · default")
        return report

    monkeypatch.setattr(
        "regis.core.application.evaluate.run_playbooks", fake_run_playbooks
    )
    monkeypatch.setattr(
        "regis.core.application.evaluate.validate_report", lambda r: None
    )

    Evaluate(sink=sink, presentation=FakePresentationRenderer()).run(
        {"results": {}}, formats=["json"], on_playbook_progress=seen.append
    )
    assert seen == ["Playbook · default"]
