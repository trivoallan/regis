# Design — Visual feedback for lazy tool fetches

**Date:** 2026-06-09
**Status:** Approved (design), pending implementation plan
**Scope (commit):** `cli`

## Problem

On a cold cache, `regis analyze` downloads missing scanner binaries (grype, syft,
trufflehog, hadolint, dockle, regctl — 10–160 MB each) lazily on first use, deep
inside worker threads. The download is silent: the only trace is a
`logger.info("Fetching …")` that is masked at the default log level. The user sees
`Running 6 analyzer(s) with 4 worker(s)...` followed by **nothing** for up to a
minute while binaries download — the CLI looks frozen.

`regis bootstrap tools` (the eager, all-at-once fetch) is silent for the same reason.

## Goal

Give **centralized, always-on (except `--quiet`) visual feedback** whenever a tool
is actually downloaded, from **any** entry point, without coupling the
`ToolFetcher` library layer to `click`, without adding a UI dependency (Rich/tqdm),
and without animated/live rendering (which is hard to coordinate across the
concurrent worker threads).

## Decisions (settled during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Where feedback applies | **Centralized in the fetcher layer** — every caller benefits (lazy `analyze`, eager `bootstrap tools`, any future caller). |
| 2 | Richness | **One-shot lines** (start + done/error), plain `click`, zero dependency. No live `%`/bar, no spinner. |
| 3 | Emit mechanism | **Observer callback** — fetcher exposes an optional `on_event`; the CLI wires a default `click`-based reporter. Library stays pure & testable. |
| 4 | Visibility | **Always on stderr, suppressed under `--quiet`**; emitted **only on a real cache miss** (never on cache hit or PATH short-circuit). |
| — | `--quiet` gating | **Proxy on the effective log level** (`--quiet` already clamps the root logger to `ERROR`). The reporter prints only when `getEffectiveLevel() <= INFO`. |

## Architecture

### Event model (library, pure)

`regis/tools/fetcher.py` gains:

- An optional constructor param `on_event: Callable[[ToolEvent], None] | None = None`
  (default `None` = silent, preserving current library behavior exactly).
- A frozen dataclass `ToolEvent` (typed, not a dict) carrying `kind` plus the
  relevant fields.
- Three emissions inside `_download_and_install`:
  - `fetch_start` — `tool`, `version`, `arch`, `url` (emitted **before** the download begins — this is what kills the "frozen" effect).
  - `fetch_done` — `tool`, `bytes` (measured during `copyfileobj`), `elapsed_s`.
  - `fetch_error` — `tool`, `error` (emitted **before** `ToolFetchError` propagates; the line is purely informative and does **not** swallow the exception).

The cache hit and PATH short-circuit paths emit nothing.

### Renderer (CLI-side, single shared function)

New `regis/utils/tool_progress.py` exposing `click_reporter`:

- Renders each event as a one-shot line on stderr (no `\r`, no rewrites — safe in CI logs):
  ```
    ⬇ Fetching grype 0.74.7 (linux-arm64)…
    ✓ Fetched grype (12.4 MB in 1.3s)
    ✗ Failed to fetch grype — sha256 mismatch
  ```
  Style matches the existing `analyze` progress lines: 2-space indent, ✓/✗ glyphs;
  `✗` in red via `click.style(fg="red")`; `⬇`/`✓` uncolored. Bytes measured from
  actual bytes written, formatted MB/KB (no dependence on `Content-Length`).
- **Gating:** prints only when `logging.getLogger("regis").getEffectiveLevel() <= logging.INFO`
  (silent under `--quiet`, which sets `ERROR`). The reporter reads the log level
  but never *emits* via logging.
- **Thread-safety:** serializes writes behind a module-level `threading.Lock`.
  Each `click.echo` is a single write, so lines never interleave intra-line even
  with 4 concurrent workers.

### Wiring (centralization)

The single `click_reporter` is wired at the two sites that download:

- `regis/utils/process.py` — `_default_fetcher()` constructs `ToolFetcher(on_event=click_reporter)` (lazy `analyze` path).
- `regis/commands/bootstrap.py` — `ToolFetcher(on_event=click_reporter)` on the `fetch_all` path.

`regis/commands/doctor.py` (read-only `status()`, no download) is **unchanged**.

### Example: cold-cache `analyze`

```
  Running 6 analyzer(s) with 4 worker(s)...
  ⬇ Fetching grype 0.74.7 (linux-arm64)…
  ⬇ Fetching syft 1.18.1 (linux-arm64)…
  ✓ Fetched grype (12.4 MB in 1.3s)
  ✓ grype        (1.4s)
  ✓ Fetched syft (45.1 MB in 2.0s)
  ✓ syft         (2.1s)
```

Start/done pairs from different threads interleave, but each line is atomic and
readable — and it finally explains *why* an analyzer took time.

## Testing

Coverage is enforced at two levels (global ≥ 90 % + per-file ≥ 90 %); every touched
file must stay covered.

**Library (`tests/tools/test_fetcher.py`)** — assert on events, decoupled from rendering:
- Cache miss emits `fetch_start` then `fetch_done` in order, with plausible `bytes`/`elapsed_s`.
- Cache hit and PATH short-circuit → **no** events.
- sha256 failure → `fetch_error` emitted **before** `ToolFetchError` is raised.
- `on_event=None` (default) → no calls, no coupling (current behavior preserved).
- Reuses the existing mocked-download fixtures (the 12 current fetcher tests).

**Renderer (`tests/utils/test_tool_progress.py`, new):**
- Each event kind → expected line (format, glyph, MB/KB, red on error) via stderr capture.
- Gating: level `INFO` → prints; level `ERROR` (quiet) → total silence.
- Serialization: two concurrent threads produce no truncated line (lock).

**Integration (light):**
- `bootstrap tools` and the `ensure_tool` path wire the reporter (a mocked fetch
  produces the lines). Patch at the source per project convention
  (`regis.utils.process._default_fetcher`, `regis.commands.bootstrap.ToolFetcher`).

## File scope

**Modified:**
- `regis/tools/fetcher.py` — `on_event` param, `ToolEvent` dataclass, byte measurement, start/done/error emission.
- `regis/utils/process.py` — `_default_fetcher()` wires the reporter.
- `regis/commands/bootstrap.py` — `ToolFetcher(on_event=…)` on `fetch_all`.

**New:**
- `regis/utils/tool_progress.py` — `click_reporter` (rendering + log-level gating + lock).
- `tests/utils/test_tool_progress.py` — renderer tests.

**Extended tests:** `tests/tools/test_fetcher.py` (events).

**Docs:** short note in `docs/website/docs/usage/tools-management.md` ("first-use
fetch now reports progress on stderr"); mention in `cli.md` if warranted.

## Out of scope (YAGNI)

No live `%`/progress bar, no Rich, no spinner, `doctor` unchanged, no feedback on
cache hit.
