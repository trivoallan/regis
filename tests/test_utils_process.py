"""Tests for regis.utils.process helpers."""

from unittest.mock import patch

import click
import pytest

from regis.utils.process import require_tool


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
