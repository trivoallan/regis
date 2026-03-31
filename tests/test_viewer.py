"""Tests for commands/viewer.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from regis_cli.commands.viewer import (
    _parse_archives,
    get_viewer_assets_dir,
    viewer_group,
)


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


class TestParseArchives:
    """Tests for _parse_archives()."""

    def test_single_archive_local_path(self) -> None:
        result = _parse_archives(("My Archive:archives/import/manifest.json",))
        assert result == [
            {"name": "My Archive", "path": "archives/import/manifest.json"}
        ]

    def test_single_archive_url(self) -> None:
        result = _parse_archives(("Production:https://host/prod/manifest.json",))
        assert result == [
            {"name": "Production", "path": "https://host/prod/manifest.json"}
        ]

    def test_multiple_archives(self) -> None:
        result = _parse_archives(
            (
                "Import Auth:archives/import/manifest.json",
                "Prod Catalog:https://host/prod/manifest.json",
            )
        )
        assert len(result) == 2
        assert result[0] == {
            "name": "Import Auth",
            "path": "archives/import/manifest.json",
        }
        assert result[1] == {
            "name": "Prod Catalog",
            "path": "https://host/prod/manifest.json",
        }

    def test_splits_on_first_colon_only(self) -> None:
        result = _parse_archives(("Name:https://host:8080/path",))
        assert result == [{"name": "Name", "path": "https://host:8080/path"}]

    def test_empty_tuple_returns_empty_list(self) -> None:
        assert _parse_archives(()) == []

    def test_raises_bad_parameter_when_no_colon(self) -> None:
        import click

        with pytest.raises(click.BadParameter) as exc_info:
            _parse_archives(("InvalidEntry",))
        assert "InvalidEntry" in str(exc_info.value)
        assert "--archive" in exc_info.value.format_message()

    def test_raises_bad_parameter_when_name_is_empty(self) -> None:
        import click

        with pytest.raises(click.BadParameter) as exc_info:
            _parse_archives((":path/to/manifest.json",))
        assert ":path/to/manifest.json" in str(exc_info.value)
        assert "--archive" in exc_info.value.format_message()

    def test_raises_bad_parameter_when_path_is_empty(self) -> None:
        import click

        with pytest.raises(click.BadParameter) as exc_info:
            _parse_archives(("name:",))
        assert "name:" in str(exc_info.value)
        assert "--archive" in exc_info.value.format_message()


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

    @patch("regis_cli.commands.viewer.get_viewer_assets_dir")
    @patch("regis_cli.commands.viewer.shutil.copytree")
    def test_export_with_archives_writes_archives_json(
        self, mock_copytree, mock_get_dir, tmp_path: Path
    ) -> None:
        mock_get_dir.return_value = tmp_path / "assets"
        output_dir = tmp_path / "output"
        runner = CliRunner()
        result = runner.invoke(
            viewer_group,
            [
                "export",
                "-o",
                str(output_dir),
                "-a",
                "Import Auth:archives/import/manifest.json",
                "-a",
                "Prod:https://host/prod/manifest.json",
            ],
        )
        assert result.exit_code == 0, result.output
        archives_file = output_dir / "archives.json"
        assert archives_file.exists()
        data = json.loads(archives_file.read_text())
        assert data == {
            "archives": [
                {"name": "Import Auth", "path": "archives/import/manifest.json"},
                {"name": "Prod", "path": "https://host/prod/manifest.json"},
            ]
        }
        assert "Archives config written" in result.output

    @patch("regis_cli.commands.viewer.get_viewer_assets_dir")
    @patch("regis_cli.commands.viewer.shutil.copytree")
    def test_export_without_archives_does_not_write_archives_json(
        self, mock_copytree, mock_get_dir, tmp_path: Path
    ) -> None:
        mock_get_dir.return_value = tmp_path / "assets"
        output_dir = tmp_path / "output"
        runner = CliRunner()
        result = runner.invoke(
            viewer_group,
            ["export", "-o", str(output_dir)],
        )
        assert result.exit_code == 0, result.output
        assert not (output_dir / "archives.json").exists()
        assert "Archives config written" not in result.output

    @patch("regis_cli.commands.viewer.get_viewer_assets_dir")
    @patch("regis_cli.commands.viewer.shutil.copytree")
    def test_export_bad_archive_format_fails(
        self, mock_copytree, mock_get_dir, tmp_path: Path
    ) -> None:
        mock_get_dir.return_value = tmp_path / "assets"
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                viewer_group,
                ["export", "-o", "output", "-a", "BadEntry"],
            )
        assert result.exit_code != 0

    def test_viewer_group_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(viewer_group, ["--help"])
        assert result.exit_code == 0
        assert "export" in result.output
        assert "serve" in result.output
