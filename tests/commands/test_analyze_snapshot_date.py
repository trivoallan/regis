"""Unit tests for snapshot_date injection in analyze.py."""

import json
from unittest.mock import MagicMock, patch


def _make_files_mock(json_content: str):
    """Return a mock for importlib.resources.files() that serves json_content."""
    mock_path = MagicMock()
    mock_path.read_text.return_value = json_content
    mock_files = MagicMock(return_value=MagicMock())
    mock_files.return_value.joinpath.return_value = mock_path
    return mock_files


def _run_injection(files_mock, version_str: str) -> dict:
    """Execute the snapshot_date injection block in isolation."""
    analysis_report: dict = {}
    with (
        patch("importlib.resources.files", files_mock),
        patch("importlib.metadata.version", return_value=version_str),
    ):
        try:
            from importlib.resources import files as _res_files

            _dates_text = (
                _res_files("regis")
                .joinpath("data/snapshot_dates.json")
                .read_text(encoding="utf-8")
            )
            _dates = json.loads(_dates_text)
            from importlib.metadata import version as _version

            _pkg_version = _version("regis")
            _entry = _dates.get(f"v{_pkg_version}") or _dates.get(_pkg_version)
            if _entry and _entry.get("date"):
                analysis_report["snapshot_date"] = _entry["date"]
        except Exception:
            pass
    return analysis_report


def test_snapshot_date_injected():
    payload = json.dumps({"v1.2.3": {"date": "2026-04-22"}})
    files_mock = _make_files_mock(payload)
    report = _run_injection(files_mock, "1.2.3")
    assert report.get("snapshot_date") == "2026-04-22"


def test_snapshot_date_absent_when_no_file():
    files_mock = MagicMock()
    files_mock.return_value.joinpath.return_value.read_text.side_effect = (
        FileNotFoundError("snapshot_dates.json not found")
    )
    report = _run_injection(files_mock, "1.2.3")
    assert "snapshot_date" not in report


def test_snapshot_date_absent_when_version_not_in_file():
    payload = json.dumps({"v9.9.9": {"date": "2025-01-01"}})
    files_mock = _make_files_mock(payload)
    report = _run_injection(files_mock, "1.2.3")
    assert "snapshot_date" not in report


def test_snapshot_date_absent_when_date_is_empty_string():
    payload = json.dumps({"v1.2.3": {"date": ""}})
    files_mock = _make_files_mock(payload)
    report = _run_injection(files_mock, "1.2.3")
    assert "snapshot_date" not in report
