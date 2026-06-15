"""Tests for regis.utils.process helpers."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import click
import pytest

from regis.core.domain.errors import ToolError
from regis.utils.process import (
    _default_fetcher,
    _manifest_names,
    ensure_tool,
    require_tool,
    run_cmd,
)


class TestRunCmd:
    def test_returns_completed_process_on_success(self):
        result = subprocess.CompletedProcess(
            ["echo", "hi"], 0, stdout="hi\n", stderr=""
        )
        with patch("regis.utils.process.subprocess.run", return_value=result):
            out = run_cmd(["echo", "hi"])
        assert out.returncode == 0

    def test_raises_on_nonzero_with_stderr(self):
        result = subprocess.CompletedProcess(["x"], 1, stdout="", stderr="boom")
        with patch("regis.utils.process.subprocess.run", return_value=result):
            with pytest.raises(click.ClickException) as exc:
                run_cmd(["x"], check=True)
        assert "boom" in exc.value.message

    def test_raises_on_nonzero_falls_back_to_stdout_when_no_stderr(self):
        result = subprocess.CompletedProcess(["x"], 1, stdout="out msg", stderr="")
        with patch("regis.utils.process.subprocess.run", return_value=result):
            with pytest.raises(click.ClickException) as exc:
                run_cmd(["x"], check=True)
        assert "out msg" in exc.value.message

    def test_no_raise_when_check_false(self):
        result = subprocess.CompletedProcess(["x"], 1, stdout="", stderr="boom")
        with patch("regis.utils.process.subprocess.run", return_value=result):
            out = run_cmd(["x"], check=False)
        assert out.returncode == 1

    def test_raises_on_missing_binary(self):
        with patch("regis.utils.process.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(click.ClickException) as exc:
                run_cmd(["nope"], check=True)
        assert "not found in PATH" in exc.value.message

    def test_step_label_appears_in_error_message(self):
        result = subprocess.CompletedProcess(["x"], 2, stdout="", stderr="err")
        with patch("regis.utils.process.subprocess.run", return_value=result):
            with pytest.raises(click.ClickException) as exc:
                run_cmd(["x"], check=True, step_label="my-step")
        assert "my-step" in exc.value.message

    def test_cwd_is_forwarded(self):
        result = subprocess.CompletedProcess(["x"], 0, stdout="", stderr="")
        with patch(
            "regis.utils.process.subprocess.run", return_value=result
        ) as mock_run:
            run_cmd(["x"], cwd="/tmp")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == "/tmp"


class TestRequireTool:
    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/git")
    def test_returns_path_when_tool_present(self, _mock_which):
        assert require_tool("git") == "/usr/bin/git"

    @patch("regis.utils.process.shutil.which", return_value=None)
    def test_raises_with_default_message_when_missing(self, _mock_which):
        with pytest.raises(click.ClickException) as exc_info:
            require_tool("nonexistent")
        assert "'nonexistent' not found in PATH" in exc_info.value.message

    @patch("regis.utils.process.shutil.which", return_value=None)
    def test_raises_with_install_hint_when_provided(self, _mock_which):
        hint = "Install via: brew install foo"
        with pytest.raises(click.ClickException) as exc_info:
            require_tool("foo", install_hint=hint)
        assert "'foo' not found in PATH" in exc_info.value.message
        assert hint in exc_info.value.message


class TestLazyHelpers:
    def setup_method(self):
        # lru_cache must be cleared so patching takes effect each test
        _default_fetcher.cache_clear()
        _manifest_names.cache_clear()

    def test_default_fetcher_returns_tool_fetcher_instance(self):
        mock_fetcher_cls = MagicMock()
        mock_instance = MagicMock()
        mock_fetcher_cls.return_value = mock_instance
        with patch("regis.tools.fetcher.ToolFetcher", mock_fetcher_cls):
            fetcher = _default_fetcher()
        assert fetcher is mock_instance

    def test_manifest_names_returns_frozenset(self):
        with patch(
            "regis.tools.manifest.load_manifest", return_value={"grype": {}, "syft": {}}
        ):
            names = _manifest_names()
        assert isinstance(names, frozenset)
        assert "grype" in names
        assert "syft" in names


class TestEnsureTool:
    def setup_method(self):
        _default_fetcher.cache_clear()
        _manifest_names.cache_clear()

    def test_returns_path_when_found_in_host(self):
        with patch(
            "regis.utils.process.shutil.which", return_value="/usr/local/bin/grype"
        ):
            result = ensure_tool("grype")
        assert result == "/usr/local/bin/grype"

    def test_fetches_from_manifest_when_not_in_path(self):
        mock_fetcher = MagicMock()
        mock_fetcher.ensure.return_value = "/cache/grype"
        with (
            patch("regis.utils.process.shutil.which", return_value=None),
            patch(
                "regis.utils.process._manifest_names", return_value=frozenset({"grype"})
            ),
            patch("regis.utils.process._default_fetcher", return_value=mock_fetcher),
        ):
            result = ensure_tool("grype")
        assert result == "/cache/grype"

    def test_wraps_fetch_error_as_tool_error(self):
        from regis.tools.fetcher import ToolFetchError

        mock_fetcher = MagicMock()
        mock_fetcher.ensure.side_effect = ToolFetchError("dl failed")
        with (
            patch("regis.utils.process.shutil.which", return_value=None),
            patch(
                "regis.utils.process._manifest_names", return_value=frozenset({"grype"})
            ),
            patch("regis.utils.process._default_fetcher", return_value=mock_fetcher),
        ):
            with pytest.raises(ToolError) as exc:
                ensure_tool("grype")
        assert "dl failed" in str(exc.value)

    def test_raises_when_not_in_path_and_not_in_manifest(self):
        with (
            patch("regis.utils.process.shutil.which", return_value=None),
            patch("regis.utils.process._manifest_names", return_value=frozenset()),
        ):
            with pytest.raises(ToolError) as exc:
                ensure_tool("ghost")
        assert "not found in PATH" in str(exc.value)

    def test_raises_with_install_hint_when_not_in_manifest(self):
        with (
            patch("regis.utils.process.shutil.which", return_value=None),
            patch("regis.utils.process._manifest_names", return_value=frozenset()),
        ):
            with pytest.raises(ToolError) as exc:
                ensure_tool("ghost", install_hint="brew install ghost")
        assert "brew install ghost" in str(exc.value)
