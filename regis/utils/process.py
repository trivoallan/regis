"""Subprocess helpers for CLI commands."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path

import click


def run_cmd(
    args: list[str],
    cwd: str | Path | None = None,
    check: bool = True,
    step_label: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command and raise ClickException on failure."""
    label = step_label or args[0]
    try:
        result = subprocess.run(  # nosec B603
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as err:
        raise click.ClickException(
            f"'{args[0]}' not found in PATH. Is it installed?"
        ) from err
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise click.ClickException(
            f"Step '{label}' failed (exit {result.returncode}):\n{detail}"
        )
    return result


def require_tool(name: str) -> str:
    """Ensure a CLI tool is available in PATH or raise ClickException."""
    path = shutil.which(name)
    if not path:
        raise click.ClickException(f"'{name}' not found in PATH. Please install it.")
    return path
