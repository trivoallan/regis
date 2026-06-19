from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from regis.adapters.driving.cli.cli import main


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


def test_bootstrap_tools_wires_click_reporter():
    import regis.utils.tool_progress as tp

    captured = {}

    class FakeFetcher:
        def __init__(self, *a, on_event=None, **kw):  # noqa: ANN001
            captured["on_event"] = on_event

        def fetch_all(self, names=None):  # noqa: ANN001
            return {}

    with patch(
        "regis.adapters.driving.cli.commands.bootstrap.ToolFetcher", FakeFetcher
    ):
        result = CliRunner().invoke(main, ["bootstrap", "tools"])

    assert result.exit_code == 0, result.output
    assert captured["on_event"] is tp.click_reporter
