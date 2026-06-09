"""Unit tests for the per-file coverage gate logic."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests import _per_file_coverage


def test_evaluate_coverage_flags_files_below_threshold():
    stats = {"regis/a.py": (10, 0), "regis/b.py": (10, 2), "regis/c.py": (100, 11)}
    assert _per_file_coverage.evaluate_coverage(stats, 90.0) == [
        ("regis/b.py", 80.0),
        ("regis/c.py", 89.0),
    ]


def test_evaluate_coverage_passes_at_exact_threshold():
    assert _per_file_coverage.evaluate_coverage({"ok.py": (10, 1)}, 90.0) == []


def test_evaluate_coverage_skips_zero_statement_files():
    assert _per_file_coverage.evaluate_coverage({"x/__init__.py": (0, 0)}, 90.0) == []


def test_read_threshold_reads_fail_under(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.report]\nfail_under = 90\n", encoding="utf-8"
    )
    assert _per_file_coverage.read_threshold(tmp_path) == 90.0


def _session(no_cov, cov_source):
    return SimpleNamespace(
        config=SimpleNamespace(
            option=SimpleNamespace(no_cov=no_cov, cov_source=cov_source),
            rootpath=Path("."),
        ),
        exitstatus=0,
    )


def test_enforce_is_noop_when_coverage_disabled(monkeypatch):
    monkeypatch.setattr(
        _per_file_coverage,
        "_collect_stats",
        lambda _r: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    session = _session(no_cov=True, cov_source=[])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == 0


def test_enforce_fails_session_for_low_file(monkeypatch, capsys):
    monkeypatch.setattr(_per_file_coverage, "read_threshold", lambda _r: 90.0)
    monkeypatch.setattr(
        _per_file_coverage, "_collect_stats", lambda _r: {"regis/bad.py": (10, 5)}
    )
    session = _session(no_cov=False, cov_source=["regis"])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    err = capsys.readouterr().err
    assert "regis/bad.py" in err and "below 90.0%" in err


def test_enforce_passes_when_all_meet_threshold(monkeypatch):
    monkeypatch.setattr(_per_file_coverage, "read_threshold", lambda _r: 90.0)
    monkeypatch.setattr(
        _per_file_coverage, "_collect_stats", lambda _r: {"regis/good.py": (10, 0)}
    )
    session = _session(no_cov=False, cov_source=["regis"])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == 0


def test_enforce_is_noop_when_cov_source_empty(monkeypatch):
    """Gate no-ops when coverage is disabled by absence of --cov (cov_source=[])."""
    monkeypatch.setattr(
        _per_file_coverage,
        "_collect_stats",
        lambda _r: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    session = _session(no_cov=False, cov_source=[])
    _per_file_coverage.enforce(session)
    assert session.exitstatus == 0


def test_read_threshold_reads_real_pyproject():
    """read_threshold returns 90.0 reading the actual project pyproject.toml."""
    repo_root = Path(__file__).resolve().parents[1]
    assert _per_file_coverage.read_threshold(repo_root) == 90.0
