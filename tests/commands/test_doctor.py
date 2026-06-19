"""Tests for `regis doctor` command."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis.adapters.driven.tools.fetcher import ToolStatus
from regis.adapters.driving.cli.cli import main
from regis.adapters.driving.cli.commands.doctor import _get_version, doctor


def _which_all(name: str) -> str:
    return f"/usr/bin/{name}"


def _which_none(_name: str) -> None:
    return None


def test_all_tools_present_exits_zero():
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_all,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version",
            return_value="Version: 1.0.0",
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 0
    assert "✓" in result.output


def test_all_tools_present_shows_each_tool():
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_all,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version",
            return_value="Version: 1.0.0",
        ),
    ):
        result = runner.invoke(doctor)
    for tool in ("grype", "syft", "trufflehog", "regctl", "hadolint", "dockle"):
        assert tool in result.output


def test_missing_tool_exits_nonzero():
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_none,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version", return_value=None
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 1


def test_missing_tool_shows_cross():
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_none,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version", return_value=None
        ),
    ):
        result = runner.invoke(doctor)
    assert "✗" in result.output


def test_partial_tools_missing_exits_nonzero():
    def which_partial(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in ("grype", "regctl") else None

    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=which_partial,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version",
            return_value="Version: 1.0.0",
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 1
    assert "✓" in result.output
    assert "✗" in result.output


def test_version_unknown_when_subprocess_returns_nothing():
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_all,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version", return_value=None
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 0
    assert "version unknown" in result.output


def test_doctor_lists_tools_section(monkeypatch, tmp_path):
    """`regis doctor` prints a Tools (manifest) section listing each entry."""
    monkeypatch.setenv("REGIS_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(shutil, "which", lambda _n: None)
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    # doctor may exit non-zero because no required tools are on PATH,
    # but the new Tools section must still print.
    assert "Tools" in result.output or "grype" in result.output
    assert "grype" in result.output
    assert "not cached" in result.output  # all 6 tools are missing under tmp_path cache


# ---------------------------------------------------------------------------
# _get_version exception paths (lines 45-56)
# ---------------------------------------------------------------------------


def test_get_version_returns_output_line(monkeypatch):
    """Normal success path: returns the first line of stdout."""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.stdout = "grype 0.78.0\nextra line\n"
    mock_result.stderr = ""
    monkeypatch.setattr(
        "regis.adapters.driving.cli.commands.doctor.subprocess.run",
        lambda *a, **k: mock_result,
    )
    assert _get_version("/usr/bin/grype", "version") == "grype 0.78.0"


def test_get_version_returns_none_when_output_empty(monkeypatch):
    """Success path with empty output → None."""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.stderr = ""
    monkeypatch.setattr(
        "regis.adapters.driving.cli.commands.doctor.subprocess.run",
        lambda *a, **k: mock_result,
    )
    assert _get_version("/usr/bin/grype", "version") is None


def test_get_version_returns_none_on_filenotfound(monkeypatch):
    def _raise(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(
        "regis.adapters.driving.cli.commands.doctor.subprocess.run", _raise
    )
    assert _get_version("/no/such/tool", "--version") is None


def test_get_version_returns_none_on_timeout(monkeypatch):
    def _raise(*a, **k):
        raise subprocess.TimeoutExpired(cmd="tool", timeout=5)

    monkeypatch.setattr(
        "regis.adapters.driving.cli.commands.doctor.subprocess.run", _raise
    )
    assert _get_version("/usr/bin/tool", "--version") is None


def test_get_version_returns_none_on_oserror(monkeypatch):
    def _raise(*a, **k):
        raise OSError("denied")

    monkeypatch.setattr(
        "regis.adapters.driving.cli.commands.doctor.subprocess.run", _raise
    )
    assert _get_version("/usr/bin/tool", "--version") is None


# ---------------------------------------------------------------------------
# _print_tools_section cached+sha256_ok and cached+sha256 mismatch (lines 29-35)
# ---------------------------------------------------------------------------


def _make_statuses(*, mismatch: bool) -> list[ToolStatus]:
    """Return one cached-ok and optionally one cached-mismatch ToolStatus."""
    statuses = [
        ToolStatus(
            name="grype",
            version="0.1.0",
            cached=True,
            path=Path("/cache/grype"),
            sha256_ok=True,
        ),
    ]
    if mismatch:
        statuses.append(
            ToolStatus(
                name="syft",
                version="0.2.0",
                cached=True,
                path=Path("/cache/syft"),
                sha256_ok=False,
            )
        )
    return statuses


def test_tools_section_cached_ok_shows_checkmark(monkeypatch):
    """cached + sha256_ok=True → ✓ marker and exit 0 (PATH tools all present)."""
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_all,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version",
            return_value="1.0.0",
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor.ToolFetcher.status",
            return_value=_make_statuses(mismatch=False),
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 0
    assert "✓" in result.output
    assert "cached @" in result.output


def test_tools_section_sha256_mismatch_exits_nonzero(monkeypatch):
    """cached + sha256_ok=False → ✗ MISMATCH marker and non-zero exit."""
    runner = CliRunner()
    with (
        patch(
            "regis.adapters.driving.cli.commands.doctor.shutil.which",
            side_effect=_which_all,
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor._get_version",
            return_value="1.0.0",
        ),
        patch(
            "regis.adapters.driving.cli.commands.doctor.ToolFetcher.status",
            return_value=_make_statuses(mismatch=True),
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 1
    assert "MISMATCH" in result.output
