"""Tests for report/docusaurus.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from regis.report.docusaurus import build_report_site


class TestBuildReportSite:
    """Tests for build_report_site()."""

    def test_dashboard_dir_not_found_raises(self, tmp_path: Path) -> None:
        with patch("regis.report.docusaurus._VIEWER_DIR", tmp_path / "nonexistent"):
            with pytest.raises(RuntimeError, match="Dashboard app not found"):
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
