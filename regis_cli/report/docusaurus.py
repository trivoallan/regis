"""Docusaurus-based report site builder for regis-cli.

Replaces the previous Jinja2 HTML renderer. Copies report.json
into the Docusaurus static directory, runs `pnpm build`, and
copies the output to the desired location.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# The report-viewer Docusaurus app lives relative to the package root
_VIEWER_DIR = Path(__file__).resolve().parent.parent.parent / "apps" / "report-viewer"


def build_report_site(
    report: dict[str, Any],
    output_dir: Path,
    base_url: str = "/",
    pretty: bool = True,
) -> Path:
    """Build the Docusaurus report site and copy to output_dir.

    Args:
        report: Full report dict to embed as report.json.
        output_dir: Where to copy the built static site.
        base_url: Base URL for the site (for GitLab Pages paths).
        pretty: Whether to pretty-print the report JSON.

    Returns:
        Path to the output directory.

    Raises:
        RuntimeError: If the Docusaurus build fails.
    """
    if not _VIEWER_DIR.is_dir():
        raise RuntimeError(
            f"Report viewer app not found at {_VIEWER_DIR}. "
            "Make sure the apps/report-viewer directory exists and "
            "dependencies are installed (pnpm install)."
        )

    static_dir = _VIEWER_DIR / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Write report.json into the viewer's static directory
    report_path = static_dir / "report.json"
    indent = 2 if pretty else None
    report_path.write_text(
        json.dumps(report, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.debug("Wrote report.json to %s", report_path)

    # Run the Docusaurus build
    env = {
        "REPORT_BASE_URL": base_url,
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "NODE_ENV": "production",
    }

    # Prefer pnpm, fall back to npx
    pnpm_path = shutil.which("pnpm")
    if pnpm_path:
        build_cmd = [pnpm_path, "docusaurus", "build"]
    else:
        npx_path = shutil.which("npx")
        if not npx_path:
            raise RuntimeError(
                "Neither pnpm nor npx found in PATH. "
                "Install Node.js and pnpm to build report sites."
            )
        build_cmd = [npx_path, "docusaurus", "build"]

    logger.info("Building report site with: %s", " ".join(build_cmd))

    try:
        result = subprocess.run(
            build_cmd,  # nosec B603
            cwd=str(_VIEWER_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Docusaurus build timed out after 120s") from exc

    if result.returncode != 0:
        logger.error("Docusaurus build failed:\n%s", result.stderr)
        raise RuntimeError(
            f"Docusaurus build failed (exit {result.returncode}):\n{result.stderr}"
        )

    logger.debug("Docusaurus build output:\n%s", result.stdout)

    # Copy build output to the target directory
    build_output = _VIEWER_DIR / "build"
    if not build_output.is_dir():
        raise RuntimeError(f"Docusaurus build directory not found at {build_output}")

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(build_output), str(output_dir), dirs_exist_ok=True)
    logger.info("Report site copied to %s", output_dir)

    # Also ensure report.json is in the output (Docusaurus copies static/)
    output_report = output_dir / "report.json"
    if not output_report.exists():
        shutil.copy2(str(report_path), str(output_report))

    return output_dir
