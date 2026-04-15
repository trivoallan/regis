"""Tests for report/docusaurus.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from regis.report.docusaurus import build_report_site


class TestBuildReportSite:
    """Tests for build_report_site()."""

    def test_neither_source_nor_bundled_assets_raises(self, tmp_path: Path) -> None:
        """Raises when both source and bundled assets are missing."""
        with patch("regis.report.docusaurus._VIEWER_DIR", tmp_path / "nonexistent"):
            with patch("regis.report.docusaurus._get_bundled_assets_dir", return_value=None):
                with pytest.raises(RuntimeError, match="Dashboard assets not found"):
                    build_report_site({"key": "val"}, tmp_path / "output")

    def test_no_package_manager_raises(self, tmp_path: Path) -> None:
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch("regis.report.docusaurus.shutil.which", return_value=None):
                with pytest.raises(RuntimeError, match="Neither pnpm nor npm"):
                    build_report_site({"key": "val"}, tmp_path / "output")

    def test_build_failure_raises(self, tmp_path: Path) -> None:
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        result = MagicMock(returncode=1, stderr="Build error", stdout="")
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ):
                    with pytest.raises(RuntimeError, match="Docusaurus build failed"):
                        build_report_site({"key": "val"}, tmp_path / "output")

    def test_build_timeout_raises(self, tmp_path: Path) -> None:
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["pnpm"], 120),
                ):
                    with pytest.raises(RuntimeError, match="timed out"):
                        build_report_site({"key": "val"}, tmp_path / "output")

    def test_build_output_dir_missing_raises(self, tmp_path: Path) -> None:
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        result = MagicMock(returncode=0, stdout="OK", stderr="")
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ):
                    with pytest.raises(RuntimeError, match="build directory not found"):
                        build_report_site({"key": "val"}, tmp_path / "output")

    def test_successful_build_with_pnpm(self, tmp_path: Path) -> None:
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        (dashboard_dir / "node_modules").mkdir()
        build_dir = dashboard_dir / "build"
        build_dir.mkdir()
        (build_dir / "index.html").write_text("<html/>")
        result = MagicMock(returncode=0, stdout="Build OK", stderr="")
        output_dir = tmp_path / "output"
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ) as mock_run:
                    ret = build_report_site({"data": "value"}, output_dir)
        assert ret == output_dir
        assert (output_dir / "index.html").exists()
        assert (output_dir / "report.json").exists()
        call_cmd = mock_run.call_args[0][0]
        assert "/usr/bin/pnpm" in call_cmd

    def test_successful_build_with_npm_fallback(self, tmp_path: Path) -> None:
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        build_dir = dashboard_dir / "build"
        build_dir.mkdir()
        (build_dir / "index.html").write_text("<html/>")
        result = MagicMock(returncode=0, stdout="Build OK", stderr="")
        output_dir = tmp_path / "output"

        def which_side_effect(cmd: str) -> str | None:
            return None if cmd == "pnpm" else "/usr/bin/npm"

        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which",
                side_effect=which_side_effect,
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ) as mock_run:
                    ret = build_report_site({"data": "value"}, output_dir)
        assert ret == output_dir
        call_cmd = mock_run.call_args[0][0]
        assert "/usr/bin/npm" in call_cmd

    def test_report_json_copied_when_absent_from_build(self, tmp_path: Path) -> None:
        """report.json is explicitly copied to output if not present after copytree."""
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        build_dir = dashboard_dir / "build"
        build_dir.mkdir()
        # No report.json in build output — function should copy it separately.
        result = MagicMock(returncode=0, stdout="OK", stderr="")
        output_dir = tmp_path / "output"
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ):
                    build_report_site({"data": "value"}, output_dir)
        assert (output_dir / "report.json").exists()

    def test_base_url_trailing_slash_added(self, tmp_path: Path) -> None:
        """base_url without trailing slash gets one appended."""
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        build_dir = dashboard_dir / "build"
        build_dir.mkdir()
        result = MagicMock(returncode=0, stdout="OK", stderr="")
        output_dir = tmp_path / "output"
        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ) as mock_run:
                    build_report_site({"data": "value"}, output_dir, base_url="/sub")
        env = mock_run.call_args.kwargs["env"]
        assert env["REPORT_BASE_URL"] == "/sub/"

    def test_bundled_assets_fallback_when_source_missing(self, tmp_path: Path) -> None:
        """Falls back to bundled assets when source directory doesn't exist."""
        # Set up bundled assets directory with some files
        bundled_dir = tmp_path / "bundled_assets"
        bundled_dir.mkdir()
        (bundled_dir / "index.html").write_text("<html>Bundled</html>")
        (bundled_dir / "styles.css").write_text("body { color: blue; }")
        assets_subdir = bundled_dir / "assets"
        assets_subdir.mkdir()
        (assets_subdir / "app.js").write_text("console.log('hello');")

        output_dir = tmp_path / "output"
        report_data = {"image": "test:latest", "findings": []}

        # Mock source dir as nonexistent, bundled assets as existing
        with patch("regis.report.docusaurus._VIEWER_DIR", tmp_path / "nonexistent"):
            with patch(
                "regis.report.docusaurus._get_bundled_assets_dir",
                return_value=bundled_dir,
            ):
                ret = build_report_site(report_data, output_dir)

        # Verify output contains all bundled files plus report.json
        assert ret == output_dir
        assert (output_dir / "index.html").read_text() == "<html>Bundled</html>"
        assert (output_dir / "styles.css").read_text() == "body { color: blue; }"
        assert (output_dir / "assets" / "app.js").exists()
        assert (output_dir / "report.json").exists()
        # Verify report.json contains our data
        import json

        report_json = json.loads((output_dir / "report.json").read_text())
        assert report_json == report_data

    def test_bundled_assets_fallback_respects_pretty_flag(self, tmp_path: Path) -> None:
        """Bundled assets mode respects pretty JSON formatting."""
        bundled_dir = tmp_path / "bundled_assets"
        bundled_dir.mkdir()
        (bundled_dir / "index.html").write_text("<html/>")

        output_dir = tmp_path / "output"
        output_dir_compact = tmp_path / "output_compact"
        report_data = {"key": "value"}

        with patch("regis.report.docusaurus._VIEWER_DIR", tmp_path / "nonexistent"):
            with patch(
                "regis.report.docusaurus._get_bundled_assets_dir",
                return_value=bundled_dir,
            ):
                # Test with pretty=True (default)
                build_report_site(report_data, output_dir, pretty=True)
                report_text = (output_dir / "report.json").read_text()
                # Pretty JSON should have newlines and indentation
                assert "\n" in report_text
                assert "  " in report_text  # indentation

        with patch("regis.report.docusaurus._VIEWER_DIR", tmp_path / "nonexistent"):
            with patch(
                "regis.report.docusaurus._get_bundled_assets_dir",
                return_value=bundled_dir,
            ):
                # Test with pretty=False
                build_report_site(report_data, output_dir_compact, pretty=False)
                report_text = (output_dir_compact / "report.json").read_text()
                # Compact JSON should have no extra whitespace
                assert "\n" not in report_text

    def test_source_mode_preferred_over_bundled(self, tmp_path: Path) -> None:
        """Source mode is used when available, even if bundled assets exist."""
        # Set up both source and bundled directories
        dashboard_dir = tmp_path / "dashboard"
        dashboard_dir.mkdir()
        (dashboard_dir / "build").mkdir()
        (dashboard_dir / "build" / "index.html").write_text("<html>Source</html>")

        bundled_dir = tmp_path / "bundled_assets"
        bundled_dir.mkdir()
        (bundled_dir / "index.html").write_text("<html>Bundled</html>")

        output_dir = tmp_path / "output"
        result = MagicMock(returncode=0, stdout="OK", stderr="")

        with patch("regis.report.docusaurus._VIEWER_DIR", dashboard_dir):
            with patch(
                "regis.report.docusaurus.shutil.which", return_value="/usr/bin/pnpm"
            ):
                with patch(
                    "regis.report.docusaurus.subprocess.run", return_value=result
                ):
                    build_report_site({"data": "value"}, output_dir)

        # Should have source mode's output, not bundled
        assert (output_dir / "index.html").read_text() == "<html>Source</html>"
