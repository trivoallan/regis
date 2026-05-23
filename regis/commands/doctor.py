"""doctor command — check external tool availability and versions."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404

import click

# Tools required by regis analyzers, in display order.
_REQUIRED_TOOLS: list[tuple[str, str]] = [
    ("trivy", "--version"),
    ("skopeo", "--version"),
    ("hadolint", "--version"),
    ("dockle", "--version"),
]


def _get_version(tool: str, version_flag: str) -> str | None:
    """Return the first line of `tool <version_flag>` output, or None on failure."""
    try:
        result = subprocess.run(  # nosec B603
            [tool, version_flag],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        output = (result.stdout or result.stderr).strip()
        return output.splitlines()[0] if output else None
    except Exception:
        return None


@click.command(name="doctor")
def doctor() -> None:
    """Check that all required external tools are installed and show their versions."""
    all_ok = True

    for tool, version_flag in _REQUIRED_TOOLS:
        path = shutil.which(tool)
        if path:
            version_line = _get_version(tool, version_flag) or "(version unknown)"
            click.echo(f"  ✓ {tool:<12} {version_line}")
        else:
            click.echo(f"  ✗ {tool:<12} not found in PATH", err=False)
            all_ok = False

    if not all_ok:
        raise SystemExit(1)
