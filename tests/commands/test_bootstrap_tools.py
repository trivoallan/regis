from __future__ import annotations

from click.testing import CliRunner

from regis.cli import main


def test_bootstrap_tools_check_lists_status(monkeypatch, tmp_path):
    monkeypatch.setenv("REGIS_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("REGIS_OFFLINE", "1")
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "tools", "--check"])
    assert result.exit_code == 0
    assert "grype" in result.output


def test_bootstrap_tools_single_tool(monkeypatch, tmp_path):
    monkeypatch.setenv("REGIS_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("REGIS_OFFLINE", "1")
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "tools", "--tool", "grype"])
    # offline + empty cache → expected failure with a clear message
    assert result.exit_code != 0
    assert "grype" in result.output
    assert "offline" in result.output.lower()
