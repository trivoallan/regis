"""Subprocess helpers for CLI commands."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from functools import lru_cache
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


def require_tool(name: str, install_hint: str | None = None) -> str:
    """Ensure a CLI tool is available in PATH or raise ClickException.

    Args:
        name: Tool binary name to look up in PATH.
        install_hint: Optional multi-line guidance appended to the error
            message when the tool is missing.
    """
    path = shutil.which(name)
    if not path:
        message = f"'{name}' not found in PATH. Please install it."
        if install_hint:
            message = f"{message}\n\n{install_hint}"
        raise click.ClickException(message)
    return path


@lru_cache(maxsize=1)
def _default_fetcher():
    from regis.tools.fetcher import ToolFetcher

    return ToolFetcher()


@lru_cache(maxsize=1)
def _manifest_names() -> frozenset[str]:
    from regis.tools.manifest import load_manifest

    return frozenset(load_manifest().keys())


def _in_manifest(name: str) -> bool:
    return name in _manifest_names()


def ensure_tool(name: str, install_hint: str | None = None) -> str:
    """Return absolute path to *name*, downloading via the manifest if needed.

    Resolution:
      1. ``shutil.which(name)`` (host PATH, full image, dev install).
      2. If *name* is in the tools manifest, delegate to
         :class:`regis.tools.fetcher.ToolFetcher`.
      3. Otherwise raise :class:`click.ClickException` (same shape as
         :func:`require_tool`).
    """
    found = shutil.which(name)
    if found:
        return found
    if _in_manifest(name):
        from regis.tools.fetcher import ToolFetchError

        try:
            return str(_default_fetcher().ensure(name))
        except ToolFetchError as exc:
            raise click.ClickException(str(exc)) from exc
    message = f"'{name}' not found in PATH. Please install it."
    if install_hint:
        message = f"{message}\n\n{install_hint}"
    raise click.ClickException(message)
