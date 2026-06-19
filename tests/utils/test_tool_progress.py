from __future__ import annotations

import logging
import threading

import pytest

from regis.adapters.driven.tools.fetcher import ToolEvent
from regis.utils.tool_progress import click_reporter


@pytest.fixture(autouse=True)
def _info_level(monkeypatch):
    """Default to a printing level (WARNING) unless a test overrides it."""
    logging.getLogger("regis").setLevel(logging.WARNING)
    yield
    logging.getLogger("regis").setLevel(logging.NOTSET)


def _capture(monkeypatch) -> list[str]:
    lines: list[str] = []

    def fake_echo(message="", err=False):  # noqa: ANN001
        lines.append(message)

    monkeypatch.setattr("regis.utils.tool_progress.click.echo", fake_echo)
    return lines


def test_start_event_renders_download_line(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_start",
            tool="grype",
            version="0.74.7",
            arch="arm64",
            url="https://x/grype",
        )
    )
    assert lines == ["  ⬇ Fetching grype 0.74.7 (linux-arm64)…"]


def test_done_event_renders_size_and_duration(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_done",
            tool="grype",
            version="0.74.7",
            arch="arm64",
            bytes=13_002_342,
            elapsed_s=1.34,
        )
    )
    assert lines == ["  ✓ Fetched grype (12.4 MB in 1.3s)"]


def test_done_event_formats_small_payload_in_kb(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_done",
            tool="syft",
            version="1.0.0",
            arch="amd64",
            bytes=2048,
            elapsed_s=0.2,
        )
    )
    assert lines == ["  ✓ Fetched syft (2.0 KB in 0.2s)"]


def test_error_event_renders_red_failure_line(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_error",
            tool="grype",
            version="0.74.7",
            arch="arm64",
            error="sha256 mismatch",
        )
    )
    assert len(lines) == 1
    assert "✗ Failed to fetch grype — sha256 mismatch" in lines[0]


def test_quiet_level_silences_all_events(monkeypatch):
    logging.getLogger("regis").setLevel(logging.ERROR)
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(kind="fetch_start", tool="grype", version="0.74.7", arch="arm64")
    )
    assert lines == []


def test_default_fetcher_is_wired_with_click_reporter(monkeypatch):
    import regis.utils.process as process
    import regis.utils.tool_progress as tp

    process._default_fetcher.cache_clear()  # drop any lru_cached instance

    captured = {}

    class FakeFetcher:
        def __init__(self, *a, on_event=None, **kw):  # noqa: ANN001
            captured["on_event"] = on_event

    monkeypatch.setattr("regis.adapters.driven.tools.fetcher.ToolFetcher", FakeFetcher)
    process._default_fetcher()
    assert captured["on_event"] is tp.click_reporter
    process._default_fetcher.cache_clear()


def test_concurrent_calls_do_not_truncate_lines(monkeypatch):
    lines = _capture(monkeypatch)

    def emit(i: int) -> None:
        click_reporter(
            ToolEvent(kind="fetch_start", tool=f"t{i}", version="1", arch="amd64")
        )

    threads = [threading.Thread(target=emit, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(lines) == 20
    assert all(line.startswith("  ⬇ Fetching t") for line in lines)
