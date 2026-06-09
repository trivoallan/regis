# Tool-Fetch Progress Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface one-shot, stderr progress lines whenever Regis downloads a scanner binary on a cache miss, from any entry point.

**Architecture:** The `ToolFetcher` library layer emits typed `ToolEvent`s through an optional injected `on_event` callback (default `None` = silent, unchanged behavior). A single CLI-side `click_reporter` renders each event as a one-shot line on stderr, gated by the effective `regis` log level (silent under `--quiet`). The reporter is wired at the two download sites: `ensure_tool()` (lazy `analyze`) and `bootstrap tools` (eager).

**Tech Stack:** Python 3.10+, `click`, `pytest`, stdlib `logging`/`threading`. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-09-tool-fetch-progress-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| `regis/tools/fetcher.py` (modify) | `ToolEvent` dataclass, `on_event` param, byte/time measurement, start/done/error emission. |
| `regis/utils/tool_progress.py` (create) | `click_reporter` — render events to stderr, log-level gating, write lock. |
| `regis/utils/process.py` (modify) | Wire `click_reporter` into the default fetcher used by `ensure_tool()`. |
| `regis/commands/bootstrap.py` (modify) | Wire `click_reporter` into the eager `fetch_all` path. |
| `tests/tools/test_fetcher.py` (modify) | Event-emission tests. |
| `tests/utils/test_tool_progress.py` (create) | Renderer + gating + lock tests. |
| `tests/commands/test_bootstrap.py` (modify, or create if absent) | Integration: `bootstrap tools` wires the reporter. |
| `docs/website/docs/usage/tools-management.md` (modify) | One-line user note. |

---

## Task 1: `ToolEvent` dataclass + `on_event` plumbing (no emission yet)

**Files:**
- Modify: `regis/tools/fetcher.py`
- Test: `tests/tools/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/tools/test_fetcher.py`:

```python
def test_on_event_defaults_to_none_and_is_optional(fake_tool) -> None:
    payload, sha, cache = fake_tool
    binpath = cache / "grype" / "0.0.1" / "linux-amd64" / "grype"
    _write_binary(binpath, payload)
    # No on_event passed: constructing and using the fetcher must work unchanged.
    fetcher = ToolFetcher(cache_dir=cache, arch="amd64", offline=True)
    assert fetcher._on_event is None
    assert fetcher.ensure("grype") == binpath  # cache hit, emits nothing


def test_tool_event_is_frozen() -> None:
    from regis.tools.fetcher import ToolEvent

    ev = ToolEvent(kind="fetch_start", tool="grype", version="0.0.1", arch="amd64")
    with pytest.raises(Exception):
        ev.tool = "syft"  # type: ignore[misc]  # frozen dataclass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/tools/test_fetcher.py::test_tool_event_is_frozen tests/tools/test_fetcher.py::test_on_event_defaults_to_none_and_is_optional -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'ToolEvent'` / `AttributeError: ... '_on_event'`.

- [ ] **Step 3: Write minimal implementation**

In `regis/tools/fetcher.py`, add `import time` to the stdlib imports and `from collections.abc import Callable` near the top. Add the dataclass after `ToolStatus`:

```python
@dataclass(frozen=True)
class ToolEvent:
    """A lifecycle event emitted while fetching a tool binary."""

    kind: str  # "fetch_start" | "fetch_done" | "fetch_error"
    tool: str
    version: str
    arch: str
    url: str | None = None
    bytes: int | None = None
    elapsed_s: float | None = None
    error: str | None = None
```

Extend `ToolFetcher.__init__` signature and body. Add the parameter (keyword, last) and store it:

```python
    def __init__(
        self,
        cache_dir: Path | None = None,
        mirror: str | None = None,
        arch: str | None = None,
        verify_cosign: bool = False,
        require_cosign: bool = False,
        offline: bool = False,
        on_event: Callable[[ToolEvent], None] | None = None,
    ) -> None:
        self.cache_dir = (cache_dir or _default_cache_dir()).resolve()
        self.mirror = mirror or os.environ.get("REGIS_TOOLS_MIRROR")
        self.arch = arch or _detect_arch()
        self.verify_cosign = verify_cosign
        self.require_cosign = require_cosign
        self.offline = offline or os.environ.get("REGIS_OFFLINE") == "1"
        self._on_event = on_event
        self._tools = _manifest.load_manifest()
```

Add a private emit helper as a method on `ToolFetcher` (place it right after `__init__`):

```python
    def _emit(self, event: ToolEvent) -> None:
        if self._on_event is not None:
            self._on_event(event)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/tools/test_fetcher.py::test_tool_event_is_frozen tests/tools/test_fetcher.py::test_on_event_defaults_to_none_and_is_optional -v --no-cov`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add regis/tools/fetcher.py tests/tools/test_fetcher.py
git commit -m "feat(cli): add ToolEvent + on_event hook to ToolFetcher"
```

---

## Task 2: Emit `fetch_start` / `fetch_done` / `fetch_error` from the download path

**Files:**
- Modify: `regis/tools/fetcher.py` (`_download_and_install`)
- Test: `tests/tools/test_fetcher.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/tools/test_fetcher.py` (reuses the `_serve` helper already in the file):

```python
def test_ensure_emits_start_then_done_on_cache_miss(monkeypatch, tmp_path):
    payload = b"binary-bytes-1234"
    sha = hashlib.sha256(payload).hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)

    events = []
    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none",
                sha256={"amd64": sha, "arm64": sha},
            )
        }
        _patch_manifest(monkeypatch, tools)
        cache = tmp_path / "cache"
        fetcher = ToolFetcher(
            cache_dir=cache, arch="amd64", on_event=events.append
        )
        fetcher.ensure("grype")

    kinds = [e.kind for e in events]
    assert kinds == ["fetch_start", "fetch_done"]
    start, done = events
    assert start.tool == "grype" and start.version == "0.0.1"
    assert start.arch == "amd64" and start.url.endswith("/tool.bin")
    assert done.bytes == len(payload)
    assert done.elapsed_s is not None and done.elapsed_s >= 0.0


def test_cache_hit_emits_no_events(fake_tool) -> None:
    payload, sha, cache = fake_tool
    binpath = cache / "grype" / "0.0.1" / "linux-amd64" / "grype"
    _write_binary(binpath, payload)
    events = []
    fetcher = ToolFetcher(
        cache_dir=cache, arch="amd64", offline=True, on_event=events.append
    )
    fetcher.ensure("grype")
    assert events == []


def test_sha_mismatch_emits_fetch_error_before_raising(monkeypatch, tmp_path):
    payload = b"binary-bytes"
    wrong_sha = hashlib.sha256(b"different").hexdigest()
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "tool.bin").write_bytes(payload)

    events = []
    with _serve(pub) as base_url:
        from regis.tools.manifest import Tool

        tools = {
            "grype": Tool(
                name="grype",
                version="0.0.1",
                url_template=f"{base_url}/tool.bin",
                archive="none",
                sha256={"amd64": wrong_sha, "arm64": wrong_sha},
            )
        }
        _patch_manifest(monkeypatch, tools)
        cache = tmp_path / "cache"
        fetcher = ToolFetcher(
            cache_dir=cache, arch="amd64", on_event=events.append
        )
        with pytest.raises(ToolFetchError, match="sha256 mismatch"):
            fetcher.ensure("grype")

    kinds = [e.kind for e in events]
    assert kinds == ["fetch_start", "fetch_error"]
    assert "sha256 mismatch" in events[-1].error
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/tools/test_fetcher.py -k "emits or cache_hit_emits or mismatch_emits" -v --no-cov`
Expected: FAIL — events list stays empty (`AssertionError`), since no emission exists yet.

- [ ] **Step 3: Write minimal implementation**

Replace the body of `_download_and_install` in `regis/tools/fetcher.py` with the version below (adds `fetch_start` before the download, captures `downloaded` bytes and elapsed time, wraps the verify/install in a `try/except ToolFetchError` that emits `fetch_error` then re-raises, and emits `fetch_done` only on success). The existing cleanup `finally` is preserved:

```python
    def _download_and_install(
        self, tool: Tool, target: Path, expected_sha: str
    ) -> None:
        """Download ``tool`` to ``target`` after sha256 verification."""
        url = self._resolve_url(tool)
        self._emit(
            ToolEvent(
                kind="fetch_start",
                tool=tool.name,
                version=tool.version,
                arch=self.arch,
                url=url,
            )
        )
        logger.info("Fetching %s %s from %s", tool.name, tool.version, url)
        started = time.monotonic()
        downloaded = 0
        with tempfile.NamedTemporaryFile(
            dir=target.parent,
            prefix=f"{tool.name}.",
            suffix=".partial",
            delete=False,
        ) as tmpf:
            partial = Path(tmpf.name)
        try:
            try:
                with urllib.request.urlopen(  # nosec B310 — http(s) only, verified by sha256
                    url, timeout=DOWNLOAD_TIMEOUT_S
                ) as resp:
                    with partial.open("wb") as out:
                        shutil.copyfileobj(resp, out)
                downloaded = partial.stat().st_size

                extracted = self._maybe_extract(tool, partial)
                actual = _sha256_file(extracted)
                if actual != expected_sha:
                    raise ToolFetchError(
                        f"{tool.name} sha256 mismatch: expected {expected_sha}, got {actual}"
                    )
                if tool.cosign is not None:
                    try:
                        verify_blob(extracted, url, tool.cosign)
                        logger.info("cosign: verified %s", tool.name)
                    except CosignUnavailable as exc:
                        if (
                            self.require_cosign
                            or os.environ.get("REGIS_REQUIRE_COSIGN") == "1"
                        ):
                            raise ToolFetchError(
                                f"{tool.name}: cosign required but unavailable ({exc})"
                            ) from exc
                        logger.info(
                            "cosign verification skipped for %s (binary not on PATH)",
                            tool.name,
                        )
                    except CosignVerificationFailed as exc:
                        raise ToolFetchError(
                            f"{tool.name}: cosign verification failed: {exc}"
                        ) from exc
                extracted.replace(target)
                os.chmod(target, 0o755)  # nosec B103 — tool binaries must be executable
            except ToolFetchError as exc:
                self._emit(
                    ToolEvent(
                        kind="fetch_error",
                        tool=tool.name,
                        version=tool.version,
                        arch=self.arch,
                        error=str(exc),
                    )
                )
                raise
        finally:
            if partial.exists():
                partial.unlink()
            # extracted may equal partial; cleanup any sibling
            for stray in target.parent.glob(f"{tool.name}.*.partial*"):
                stray.unlink(missing_ok=True)
            for stray in target.parent.glob(f"{tool.name}.*.partial.extracted"):
                stray.unlink(missing_ok=True)
        self._emit(
            ToolEvent(
                kind="fetch_done",
                tool=tool.name,
                version=tool.version,
                arch=self.arch,
                bytes=downloaded,
                elapsed_s=time.monotonic() - started,
            )
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/tools/test_fetcher.py -v --no-cov`
Expected: PASS (all existing fetcher tests + the 3 new ones).

- [ ] **Step 5: Commit**

```bash
git add regis/tools/fetcher.py tests/tools/test_fetcher.py
git commit -m "feat(cli): emit fetch lifecycle events from ToolFetcher download path"
```

---

## Task 3: `click_reporter` renderer (rendering + gating + lock)

**Files:**
- Create: `regis/utils/tool_progress.py`
- Test: `tests/utils/test_tool_progress.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/utils/test_tool_progress.py`:

```python
from __future__ import annotations

import logging
import threading

import pytest

from regis.tools.fetcher import ToolEvent
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
            kind="fetch_start", tool="grype", version="0.74.7", arch="arm64",
            url="https://x/grype",
        )
    )
    assert lines == ["  ⬇ Fetching grype 0.74.7 (linux-arm64)…"]


def test_done_event_renders_size_and_duration(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_done", tool="grype", version="0.74.7", arch="arm64",
            bytes=13_002_342, elapsed_s=1.34,
        )
    )
    assert lines == ["  ✓ Fetched grype (12.4 MB in 1.3s)"]


def test_done_event_formats_small_payload_in_kb(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_done", tool="syft", version="1.0.0", arch="amd64",
            bytes=2048, elapsed_s=0.2,
        )
    )
    assert lines == ["  ✓ Fetched syft (2.0 KB in 0.2s)"]


def test_error_event_renders_red_failure_line(monkeypatch):
    lines = _capture(monkeypatch)
    click_reporter(
        ToolEvent(
            kind="fetch_error", tool="grype", version="0.74.7", arch="arm64",
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


def test_concurrent_calls_do_not_truncate_lines(monkeypatch):
    lines = _capture(monkeypatch)

    def emit(i: int) -> None:
        click_reporter(
            ToolEvent(
                kind="fetch_start", tool=f"t{i}", version="1", arch="amd64"
            )
        )

    threads = [threading.Thread(target=emit, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(lines) == 20
    assert all(line.startswith("  ⬇ Fetching t") for line in lines)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/utils/test_tool_progress.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'regis.utils.tool_progress'`.

- [ ] **Step 3: Write minimal implementation**

Create `regis/utils/tool_progress.py`:

```python
"""CLI-side renderer for tool-fetch lifecycle events (stderr, one-shot lines)."""

from __future__ import annotations

import logging
import threading

import click

from regis.tools.fetcher import ToolEvent

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/utils/test_tool_progress.py -v --no-cov`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add regis/utils/tool_progress.py tests/utils/test_tool_progress.py
git commit -m "feat(cli): add click_reporter for tool-fetch progress lines"
```

---

## Task 4: Wire the reporter into the lazy `ensure_tool` path

**Files:**
- Modify: `regis/utils/process.py` (`_default_fetcher`)
- Test: `tests/utils/test_tool_progress.py` (or existing `tests/utils/test_process.py` if present — keep with the wiring)

- [ ] **Step 1: Write the failing test**

Add to `tests/utils/test_tool_progress.py`:

```python
def test_default_fetcher_is_wired_with_click_reporter(monkeypatch):
    import regis.utils.process as process
    import regis.utils.tool_progress as tp

    process._default_fetcher.cache_clear()  # drop any lru_cached instance

    captured = {}

    class FakeFetcher:
        def __init__(self, *a, on_event=None, **kw):  # noqa: ANN001
            captured["on_event"] = on_event

    monkeypatch.setattr("regis.tools.fetcher.ToolFetcher", FakeFetcher)
    process._default_fetcher()
    assert captured["on_event"] is tp.click_reporter
    process._default_fetcher.cache_clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/utils/test_tool_progress.py::test_default_fetcher_is_wired_with_click_reporter -v --no-cov`
Expected: FAIL — `captured["on_event"]` is `None` (reporter not wired yet).

- [ ] **Step 3: Write minimal implementation**

In `regis/utils/process.py`, update `_default_fetcher` to inject the reporter:

```python
@lru_cache(maxsize=1)
def _default_fetcher():
    from regis.tools.fetcher import ToolFetcher
    from regis.utils.tool_progress import click_reporter

    return ToolFetcher(on_event=click_reporter)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/utils/test_tool_progress.py::test_default_fetcher_is_wired_with_click_reporter -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/utils/process.py tests/utils/test_tool_progress.py
git commit -m "feat(cli): wire tool-fetch progress into lazy ensure_tool path"
```

---

## Task 5: Wire the reporter into the eager `bootstrap tools` path

**Files:**
- Modify: `regis/commands/bootstrap.py` (`bootstrap_tools`)
- Test: `tests/commands/test_bootstrap.py` (add to it; create if it does not exist)

- [ ] **Step 1: Write the failing test**

Add to `tests/commands/test_bootstrap.py` (create the file with the imports below if absent):

```python
from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from regis.cli import main


def test_bootstrap_tools_wires_click_reporter():
    import regis.utils.tool_progress as tp

    captured = {}

    class FakeFetcher:
        def __init__(self, *a, on_event=None, **kw):  # noqa: ANN001
            captured["on_event"] = on_event

        def fetch_all(self, names=None):  # noqa: ANN001
            return {}

    with patch("regis.commands.bootstrap.ToolFetcher", FakeFetcher):
        result = CliRunner().invoke(main, ["bootstrap", "tools"])

    assert result.exit_code == 0, result.output
    assert captured["on_event"] is tp.click_reporter
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/commands/test_bootstrap.py::test_bootstrap_tools_wires_click_reporter -v --no-cov`
Expected: FAIL — `on_event` is `None` (the command constructs `ToolFetcher()` with no callback).

- [ ] **Step 3: Write minimal implementation**

In `regis/commands/bootstrap.py`, import the reporter at the top of the module (with the other imports):

```python
from regis.utils.tool_progress import click_reporter
```

Then, in `bootstrap_tools`, construct the fetcher with the callback. The `--check` path does not download, so leaving the callback wired is harmless, but construct it once with the reporter:

```python
    fetcher = ToolFetcher(on_event=click_reporter)
```

(Replace the existing `fetcher = ToolFetcher()` line. Everything else in the command is unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/commands/test_bootstrap.py::test_bootstrap_tools_wires_click_reporter -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/commands/bootstrap.py tests/commands/test_bootstrap.py
git commit -m "feat(cli): wire tool-fetch progress into bootstrap tools"
```

---

## Task 6: User documentation note

**Files:**
- Modify: `docs/website/docs/usage/tools-management.md`

- [ ] **Step 1: Add the note**

Find the section describing first-use/lazy fetching in `docs/website/docs/usage/tools-management.md` (search for "lazy" / "first use" / "fetch"). Add a short paragraph:

```markdown
When a tool is downloaded on first use, Regis now prints a one-line progress
notice to stderr — `⬇ Fetching grype 0.74.7 (linux-arm64)…` followed by
`✓ Fetched grype (12.4 MB in 1.3s)`. These notices appear during `regis analyze`
(lazy fetch) and `regis bootstrap tools` (eager fetch), and are suppressed by the
global `--quiet` flag.
```

- [ ] **Step 2: Build the docs to verify no breakage (optional but recommended)**

Run: `pnpm --filter @regis/dashboard build` (only if touching other doc wiring; a prose-only addition needs no build, but confirm the file still renders if a local Docusaurus dev server is running).
Expected: no Markdown errors.

- [ ] **Step 3: Commit**

```bash
git add docs/website/docs/usage/tools-management.md
git commit -m "docs(cli): note tool-fetch progress lines in tools-management guide"
```

---

## Task 7: Full-suite verification

- [ ] **Step 1: Run the whole suite with coverage gates**

Run: `pipenv run pytest`
Expected: PASS; global coverage ≥ 90 % and every touched file ≥ 90 %. New files `regis/utils/tool_progress.py` and the fetcher changes are exercised by Tasks 2–5.

- [ ] **Step 2: Lint & format**

Run: `pipenv run ruff check . && pipenv run ruff format --check .`
Expected: clean. If `ruff format --check` reports diffs, run `pipenv run ruff format .` and amend the relevant commit.

- [ ] **Step 3: Manual smoke (optional, real network)**

Run, with an empty cache dir, against any small public image:

```bash
REGIS_CACHE_DIR=$(mktemp -d) pipenv run regis analyze alpine:3.20 2>&1 | grep -E "Fetching|Fetched"
```

Expected: `⬇ Fetching …` / `✓ Fetched …` lines appear interleaved with analyzer progress. Re-running against the same `REGIS_CACHE_DIR` prints **no** fetch lines (cache hit).

---

## Self-Review Notes (author)

- **Spec coverage:** Decisions 1–4 + gating → Tasks 1–5; event model → Tasks 1–2; renderer/gating/lock → Task 3; centralized wiring at both download sites → Tasks 4–5; `doctor` untouched (no task); docs → Task 6; two-level coverage → Task 7.
- **Gating value:** default level is `WARNING`; reporter prints when `getEffectiveLevel() < ERROR`, silent only under `--quiet` (`ERROR`). Verified against `regis/cli.py:59-64`.
- **Type consistency:** `ToolEvent(kind, tool, version, arch, url, bytes, elapsed_s, error)` used identically in fetcher emission (Task 2) and renderer (Task 3); `on_event` keyword name identical across fetcher, `_default_fetcher`, and `bootstrap_tools`; `click_reporter` referenced by identity in Tasks 4–5 tests.
- **Byte semantics:** `bytes` = size of the downloaded payload on disk (`partial.stat().st_size`), measured before extraction — for archived tools this is the archive size, which is the meaningful "downloaded" figure.
