"""Tests for the click-free core playbook runner + validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from regis.core.application.playbook_runner import run_playbooks, validate_report
from regis.core.domain.errors import PlaybookError

_REPORT = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "report.v3.json").read_text(
        encoding="utf-8"
    )
)


def _envelope() -> dict:
    # a minimal analyzer envelope (results-only) the default playbook can evaluate
    return {
        k: v
        for k, v in _REPORT.items()
        if k in ("schemaVersion", "version", "request", "results", "metadata")
    }


def test_run_playbooks_default_playbook_adds_playbooks_key():
    out = run_playbooks((), _envelope())
    assert "playbooks" in out and out["playbooks"]


def test_run_playbooks_invokes_on_progress():
    seen: list[str] = []
    run_playbooks((), _envelope(), on_progress=seen.append)
    assert seen  # at least one progress message


def test_run_playbooks_unknown_path_raises_playbook_error():
    with pytest.raises(PlaybookError):
        run_playbooks(("/no/such/playbook.yaml",), _envelope())


def test_validate_report_raises_playbook_error_on_invalid():
    with pytest.raises(PlaybookError):
        validate_report({"not": "a regis report"})
