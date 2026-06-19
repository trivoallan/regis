"""CLI-side renderer for tool-fetch lifecycle events (stderr, one-shot lines)."""

from __future__ import annotations

import logging
import threading

import click

from regis.adapters.driven.tools.fetcher import ToolEvent

logger = logging.getLogger("regis")
_write_lock = threading.Lock()


def _format_bytes(n: int) -> str:
    mb = n / (1024 * 1024)
    if mb >= 1.0:
        return f"{mb:.1f} MB"
    return f"{n / 1024:.1f} KB"


def click_reporter(event: ToolEvent) -> None:
    """Render a tool-fetch event as a one-shot line on stderr.

    Silent when the effective ``regis`` log level is ``ERROR`` or above
    (i.e. under ``--quiet``). Writes are serialized so concurrent worker
    threads never interleave a single line.
    """
    if logger.getEffectiveLevel() >= logging.ERROR:
        return
    if event.kind == "fetch_start":
        line = f"  ⬇ Fetching {event.tool} {event.version} (linux-{event.arch})…"
    elif event.kind == "fetch_done":
        size = _format_bytes(event.bytes or 0)
        line = f"  ✓ Fetched {event.tool} ({size} in {event.elapsed_s:.1f}s)"
    elif event.kind == "fetch_error":
        line = click.style(
            f"  ✗ Failed to fetch {event.tool} — {event.error}", fg="red"
        )
    else:
        return
    with _write_lock:
        click.echo(line, err=True)
