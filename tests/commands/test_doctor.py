"""Tests for `regis doctor` command."""

from __future__ import annotations

import shutil
from unittest.mock import patch

from click.testing import CliRunner

from regis.cli import main
from regis.commands.doctor import doctor


def _which_all(name: str) -> str:
    return f"/usr/bin/{name}"


def _which_none(_name: str) -> None:
    return None


def test_all_tools_present_exits_zero():
    runner = CliRunner()
    with (
        patch("regis.commands.doctor.shutil.which", side_effect=_which_all),
        patch(
            "regis.commands.doctor._get_version",
            return_value="Version: 1.0.0",
        ),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 0
    assert "✓" in result.output


def test_all_tools_present_shows_each_tool():
    runner = CliRunner()
    with (
        patch("regis.commands.doctor.shutil.which", side_effect=_which_all),
        patch(
            "regis.commands.doctor._get_version",
            return_value="Version: 1.0.0",
        ),
    ):
        result = runner.invoke(doctor)
    for tool in ("grype", "syft", "trufflehog", "regctl", "hadolint", "dockle"):
        assert tool in result.output


def test_missing_tool_exits_nonzero():
    runner = CliRunner()
    with (
        patch("regis.commands.doctor.shutil.which", side_effect=_which_none),
        patch("regis.commands.doctor._get_version", return_value=None),
    ):
        result = runner.invoke(doctor)
    assert result.exit_code == 1


def test_missing_tool_shows_cross():
    runner = CliRunner()
    with (
        patch("regis.commands.doctor.shutil.which", side_effect=_which_none),
        patch("regis.commands.doctor._get_version", return_value=None),
    ):
        result = runner.invoke(doctor)
    assert "✗" in result.output


def test_partial_tools_missing_exits_nonzero():
    def which_partial(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in ("grype", "regctl") else None

    runner = CliRunner()
    with (
        patch("regis.commands.doctor.shutil.which", side_effect=which_partial),
        patch(
            "regis.commands.doctor._get_version",
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
        patch("regis.commands.doctor.shutil.which", side_effect=_which_all),
        patch("regis.commands.doctor._get_version", return_value=None),
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
