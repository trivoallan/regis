"""Tests for the syft subprocess wrapper."""

import subprocess
from unittest.mock import MagicMock, patch

import click
import pytest

from regis.analyzers.base import AnalyzerError
from regis.utils.syft import run_syft


def _missing(_name):
    raise click.ClickException("syft not found")


_SAMPLE = '{"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}'


class TestRunSyft:
    def test_not_found(self):
        with patch("regis.utils.syft.ensure_tool", _missing):
            with pytest.raises(AnalyzerError, match="not found"):
                run_syft("alpine:3.20")

    @patch("regis.utils.syft.ensure_tool")
    @patch("regis.utils.syft.subprocess.run")
    def test_success_and_args(self, mock_run, mock_ensure):
        mock_ensure.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)

        result = run_syft("alpine:3.20")
        assert result["bomFormat"] == "CycloneDX"

        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/local/bin/syft"
        assert "cyclonedx-json" in args
        kwargs = mock_run.call_args[1]
        assert kwargs["check"] is True
        assert kwargs["env"] is not None

    @patch("regis.utils.syft.ensure_tool")
    @patch("regis.utils.syft.subprocess.run")
    def test_creds_and_platform(self, mock_run, mock_ensure):
        mock_ensure.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)

        run_syft("alpine:3.20", username="u", password="p", platform="linux/arm64")

        args = mock_run.call_args[0][0]
        env = mock_run.call_args[1]["env"]
        assert "--platform" in args and "linux/arm64" in args
        assert env["SYFT_REGISTRY_AUTH_USERNAME"] == "u"
        assert env["SYFT_REGISTRY_AUTH_PASSWORD"] == "p"

    @patch("regis.utils.syft.ensure_tool")
    @patch("regis.utils.syft.subprocess.run")
    def test_creds_from_regis_env_fallback(self, mock_run, mock_ensure, monkeypatch):
        mock_ensure.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)
        monkeypatch.setenv("REGIS_USERNAME", "envuser")
        monkeypatch.setenv("REGIS_PASSWORD", "envpass")

        run_syft("alpine:3.20")

        env = mock_run.call_args[1]["env"]
        assert env["SYFT_REGISTRY_AUTH_USERNAME"] == "envuser"
        assert env["SYFT_REGISTRY_AUTH_PASSWORD"] == "envpass"

    @patch("regis.utils.syft.ensure_tool")
    @patch("regis.utils.syft.subprocess.run")
    def test_called_process_error(self, mock_run, mock_ensure):
        mock_ensure.return_value = "/usr/local/bin/syft"
        mock_run.side_effect = subprocess.CalledProcessError(1, ["syft"], stderr="boom")
        with pytest.raises(AnalyzerError, match="syft failed: boom"):
            run_syft("alpine:3.20")

    @patch("regis.utils.syft.ensure_tool")
    @patch("regis.utils.syft.subprocess.run")
    def test_invalid_json(self, mock_run, mock_ensure):
        mock_ensure.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout="not-json")
        with pytest.raises(AnalyzerError, match="syft produced invalid"):
            run_syft("alpine:3.20")
