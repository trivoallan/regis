"""doctor command — check external tool availability and versions."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404

import click

from regis.tools.fetcher import ToolFetcher

# Tools required by regis analyzers, in display order.
_REQUIRED_TOOLS: list[tuple[str, str]] = [
    ("grype", "version"),
    ("syft", "version"),
    ("trufflehog", "--version"),
    ("regctl", "version"),
    ("hadolint", "--version"),
    ("dockle", "--version"),
]


def _print_tools_section() -> bool:
    """Print a manifest-backed Tools section. Returns False on sha256 mismatch."""
    click.echo("Tools (manifest):")
    fetcher = ToolFetcher()
    all_ok = True
    for status in fetcher.status():
        if status.cached and status.sha256_ok:
            mark = "✓"
            detail = f"cached @ {status.path}"
        elif status.cached and status.sha256_ok is False:
            mark = "✗"
            detail = f"cache present but sha256 MISMATCH @ {status.path}"
            all_ok = False
        else:
            mark = "⏩"
            detail = "not cached (will fetch on first use)"
        click.echo(f"  {mark} {status.name:<12} {status.version:<10} {detail}")
    return all_ok


def _get_version(path: str, version_flag: str) -> str | None:
    """Return the first line of `path <version_flag>` output, or None on failure."""
    try:
        result = subprocess.run(  # nosec B603
            [path, version_flag],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        output = (result.stdout or result.stderr).strip()
        return output.splitlines()[0] if output else None
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None


@click.command(name="doctor")
def doctor() -> None:
    """Check that all required external tools are installed and show their versions."""
    all_ok = True

    for tool, version_flag in _REQUIRED_TOOLS:
        path = shutil.which(tool)
        if path:
            version_line = _get_version(path, version_flag) or "(version unknown)"
            click.echo(f"  ✓ {tool:<12} {version_line}")
        else:
            click.echo(f"  ✗ {tool:<12} not found in PATH", err=False)
            all_ok = False

    tools_ok = _print_tools_section()

    if not all_ok or not tools_ok:
        raise SystemExit(1)
