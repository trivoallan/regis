"""Docusaurus-based report site builder for regis.

Replaces the previous Jinja2 HTML renderer. Copies report.json
into the Docusaurus static directory, runs `pnpm build`, and
copies the output to the desired location.

Supports two modes:
- Source mode: Dynamically builds from apps/dashboard (requires Node.js)
- Bundled mode: Uses pre-built dashboard_assets (no external dependencies)
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

# The dashboard Docusaurus app lives relative to the package root
_VIEWER_DIR = Path(__file__).resolve().parent.parent.parent / "apps" / "dashboard"


def _get_bundled_assets_dir() -> Path | None:
    """Get path to pre-built bundled dashboard assets.

    Returns the path to the installed dashboard assets directory,
    used as a fallback when the source apps/dashboard is not available.
    This is the normal case for pip-installed packages and Docker images.

    Returns:
        Path to dashboard_assets directory, or None if not found.
    """
    assets_dir = Path(__file__).parent.parent / "dashboard_assets"
    if assets_dir.is_dir():
        return assets_dir
    return None


def build_report_site(
    report: dict[str, Any],
    output_dir: Path,
    base_url: str = "/",
    pretty: bool = True,
) -> Path:
    """Build the Docusaurus report site and copy to output_dir.

    Supports two modes:
    1. Source mode: If apps/dashboard exists, dynamically builds with pnpm/npm
       (requires Node.js, pnpm/npm, and source code)
    2. Bundled mode: If apps/dashboard doesn't exist, uses pre-built dashboard_assets
       (no external dependencies, used in Docker images and pip-installed packages)

    Args:
        report: Full report dict to embed as report.json.
        output_dir: Where to copy the built static site.
        base_url: Base URL for the site (for GitLab Pages paths).
        pretty: Whether to pretty-print the report JSON.

    Returns:
        Path to the output directory.

    Raises:
        RuntimeError: If the build fails in source mode or assets are missing in bundled mode.
    """
    # Ensure base_url ends with a slash for Docusaurus
    if not base_url.endswith("/"):
        base_url += "/"

    # Try source mode first (for development)
    if _VIEWER_DIR.is_dir():
        return _build_from_source(_VIEWER_DIR, report, output_dir, base_url, pretty)

    # Fall back to bundled mode (for installed packages/Docker images)
    bundled_assets = _get_bundled_assets_dir()
    if bundled_assets:
        return _build_from_bundled(bundled_assets, report, output_dir, pretty)

    # Neither source nor bundled assets found
    raise RuntimeError(
        f"Dashboard assets not found. Tried:\n"
        f"  1. Source: {_VIEWER_DIR}\n"
        f"  2. Bundled: {Path(__file__).parent.parent / 'dashboard_assets'}\n"
        f"Make sure either the apps/dashboard directory exists or the package "
        f"was installed with dashboard assets included."
    )


def _build_from_source(
    viewer_dir: Path,
    report: dict[str, Any],
    output_dir: Path,
    base_url: str,
    pretty: bool,
) -> Path:
    """Build report site from source using pnpm/npm.

    Args:
        viewer_dir: Path to apps/dashboard directory.
        report: Full report dict to embed as report.json.
        output_dir: Where to copy the built static site.
        base_url: Base URL for the site.
        pretty: Whether to pretty-print the report JSON.

    Returns:
        Path to the output directory.

    Raises:
        RuntimeError: If the build fails.
    """
    logger.info("Building report site from source: %s", viewer_dir)

    static_dir = viewer_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Write report.json into the dashboard's static directory
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

    # Check if node_modules exists
    if not (viewer_dir / "node_modules").is_dir():
        logger.warning(
            "node_modules not found in %s. Docusaurus build may fail. "
            "Run 'pnpm install' in the workspace root.",
            viewer_dir,
        )

    # Prefer pnpm, fall back to npm
    pnpm_path = shutil.which("pnpm")
    if pnpm_path:
        # Use 'run build' to leverage scripts in package.json
        build_cmd = [pnpm_path, "run", "build"]
    else:
        npm_path = shutil.which("npm")
        if not npm_path:
            raise RuntimeError(
                "Neither pnpm nor npm found in PATH. "
                "Install Node.js and pnpm to build report sites."
            )
        build_cmd = [npm_path, "run", "build"]

    logger.info("Building report site with: %s", " ".join(build_cmd))

    try:
        result = subprocess.run(
            build_cmd,  # nosec B603
            cwd=str(viewer_dir),
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
    build_output = viewer_dir / "build"
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


def _build_from_bundled(
    bundled_assets: Path,
    report: dict[str, Any],
    output_dir: Path,
    pretty: bool,
) -> Path:
    """Build report site from pre-built bundled assets.

    Used as a fallback when source apps/dashboard is not available.
    Simply copies the bundled assets and adds report.json.

    Args:
        bundled_assets: Path to regis/dashboard_assets directory.
        report: Full report dict to embed as report.json.
        output_dir: Where to copy the built static site.
        pretty: Whether to pretty-print the report JSON.

    Returns:
        Path to the output directory.
    """
    logger.info("Using pre-built bundled dashboard assets: %s", bundled_assets)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy bundled assets to output directory
    for item in bundled_assets.iterdir():
        src = bundled_assets / item.name
        dst = output_dir / item.name
        if src.is_dir():
            shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
        else:
            shutil.copy2(str(src), str(dst))

    logger.debug("Copied bundled assets to %s", output_dir)

    # Write report.json to output directory
    report_path = output_dir / "report.json"
    indent = 2 if pretty else None
    report_path.write_text(
        json.dumps(report, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Report site copied to %s (using bundled assets)", output_dir)

    return output_dir
