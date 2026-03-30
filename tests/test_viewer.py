"""Tests for commands/viewer.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from regis_cli.commands.viewer import get_viewer_assets_dir, viewer_group


class TestGetViewerAssetsDir:
    """Tests for get_viewer_assets_dir()."""

    def test_returns_path_when_dir_exists(self) -> None:
        with patch.object(Path, "exists", return_value=True):
            result = get_viewer_assets_dir()
        assert result.name == "viewer_assets"

    def test_exits_when_dir_missing(self) -> None:
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                get_viewer_assets_dir()
        assert exc_info.value.code == 1


class TestViewerExportCmd:
    """Tests for the `viewer export` subcommand."""

    @patch("regis_cli.commands.viewer.get_viewer_assets_dir")
    @patch("regis_cli.commands.viewer.shutil.copytree")
    def test_export_without_report(
        self, mock_copytree, mock_get_dir, tmp_path: Path
    ) -> None:
        mock_get_dir.return_value = tmp_path / "assets"
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(viewer_group, ["export", "-o", "output"])
        assert result.exit_code == 0
        assert "Successfully exported" in result.output
        mock_copytree.assert_called_once()

    @patch("regis_cli.commands.viewer.get_viewer_assets_dir")
    @patch("regis_cli.commands.viewer.shutil.copytree")
    @patch("regis_cli.commands.viewer.shutil.copy2")
    def test_export_with_report(
        self, mock_copy2, mock_copytree, mock_get_dir, tmp_path: Path
    ) -> None:
        mock_get_dir.return_value = tmp_path / "assets"
        report_file = tmp_path / "report.json"
        report_file.write_text('{"results": {}}')
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                viewer_group,
                ["export", "-o", "output", str(report_file)],
            )
        assert result.exit_code == 0
        assert "Successfully exported" in result.output
        mock_copy2.assert_called_once()

    def test_viewer_group_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(viewer_group, ["--help"])
        assert result.exit_code == 0
        assert "export" in result.output
        assert "serve" in result.output
