# Dashboard Full Decouple — Design

> **Date**: 2026-05-31
> **Status**: Design approved, pending implementation plan
> **Supersedes**: the OCI/`ToolFetcher` build-time-pin design captured in
> `docs/memory-bank/plans/2026-05-31-dashboard-repo-split-plan.md` (PR #628).

## Why this supersedes PR #628

PR #628 split `apps/dashboard` into a dedicated repo but kept the core **consuming**
the dashboard: a versioned OCI artifact fetched at build-time via the existing
`ToolFetcher`, bundled into every wheel and image, with a build-time `schemaVersion`
compatibility pin.

Stress-testing that design surfaced that the `ToolFetcher` reuse was thin — the
dashboard is a static, arch-independent, eagerly-bundled asset, while `ToolFetcher`
exists for lazy, per-arch, runtime-fetched binaries. Four of its five reasons to
exist (lazy slim, mirror, offline, doctor integration) were explicitly opted out.
What remained was "uses `regctl`", i.e. "uses ghcr".

This design takes the more decisive move: **the core stops shipping the dashboard
entirely.** This removes more complexity than the split adds — no `assets:` section,
no `ToolFetcher` extension, no `REGIS_DASHBOARD_DIR`, no build-time pin to enforce.

## Decision

`apps/dashboard` becomes a fully independent project in a new `regis-dashboard`
repository. The two projects are linked by a **single versioned contract**:
`report.json` + a new integer `schemaVersion` field. The core knows nothing about
the dashboard.

### Drivers (validated)

1. **Decoupled release cadences** — release the dashboard independently of the CLI.
2. **Lighten the core** — remove Node/pnpm/Docusaurus from the **Python package
   build path** (wheel + Docker image).

The radical cut also yields a third benefit not available to the PR #628 design:
the core's build path gains **zero new external dependencies** (no ghcr fetch in
the wheel/image build), because there is nothing to fetch.

Explicitly out of scope as drivers: standalone product reuse, separate front/back
governance.

## Architecture

```text
┌──────────────────────────────────────────┐         ┌──────────────────────────────────────────┐
│ regis (core, this repo)                  │         │ regis-dashboard (new repo)               │
│                                          │         │                                          │
│  • analyzers                             │         │  • Docusaurus + Tremor SPA               │
│  • playbook / rules / registry           │         │  • Multi-archive config UI               │
│  • CLI: analyze, evaluate, check,        │         │  • CLI: render, serve, bootstrap         │
│    doctor, playbook, rules,              │  ────►  │    archive, archive add/configure        │
│    bootstrap {playbook, gitlab-ci,       │ report  │  • Autonomous release cycle              │
│    tools}                                │  .json  │  • Own distribution (Docker primary)     │
│  • `--html` format (Jinja2 self-cont.)   │         │  • Dedicated GitHub Pages                │
│  • `--json` format (the contract)        │         │                                          │
│                                          │         │  Declares the schemaVersion range        │
│  Embeds NO dashboard asset.              │         │  each release supports.                  │
│  No Node on the wheel/image build path.  │         │                                          │
└──────────────────────────────────────────┘         └──────────────────────────────────────────┘
        │                                                    ▲
        │ report.json (schemaVersion: N)                    │
        └────────────────────────────────────────────────────┘
                       versioned runtime contract
```

### Removed from the core

- `regis/commands/dashboard.py` (group `export`, `serve`)
- `regis/commands/archive.py` (group `add`, `configure`)
- `regis bootstrap archive` subcommand + `regis/cookiecutters/archive/`
- `--site` flag on `analyze` / `evaluate`; the `html-site` format branch in
  `regis/utils/report.py`
- `regis/report/docusaurus.py`
- `regis/server/` + the `[server]` optional extra (FastAPI, uvicorn)
- `regis/dashboard_assets/` + its `pyproject.toml` package-data
- `apps/dashboard/` + its entry in `pnpm-workspace.yaml`
- `cd-dashboard.yml` workflow

### Retained in the core (visualization)

- `regis analyze --html` — Jinja2 single-file, self-contained (created 2026-04-25,
  already decoupled from `dashboard_assets`).
- `regis analyze --json` — the machine contract.

### Decision: archive bootstrap moves entirely to regis-dashboard (option α)

`regis bootstrap archive`, `regis archive add`, and `regis archive configure` all
serve the dashboard exclusively. They move **in full** to `regis-dashboard`
(`regis-dashboard bootstrap archive`, etc.). The core keeps no archive cookiecutter.

Trade-off accepted: the core loses a customer-facing entry point and some
discoverability, in exchange for a clean "core = analyzer + self-contained format"
boundary. Mitigated by the post-analyze message (see Distribution & DX).

## The contract: `report.json` + `schemaVersion`

This is the only thing linking the two repos, so it is specified precisely.

### Field shape

`schemaVersion` is an **integer** at the root of `report.json` (mirrors the
playbook `schemaVersion: 1` pattern). It is **distinct** from the existing `version`
field (the snapshot date). Added to `regis/schemas/report/report.schema.json` as
`required`.

```jsonc
{
  "schemaVersion": 1,          // NEW: integer, required. The contract.
  "version": "2026-05-31",     // EXISTING: snapshot date. Unchanged.
  "playbook_name": "...",
  "analyzers": { ... }
}
```

### Bump policy

- `schemaVersion` increments **only** on a breaking structural change (field
  removed/renamed, semantics changed). Adding an optional field is **not** a bump.
- Every bump → core changelog entry + migration note.

### Compatibility ownership & enforcement

- **The dashboard declares** the `schemaVersion` range each release can render as
  an inclusive `[min, max]` integer pair (e.g. `supports: { min: 1, max: 2 }`
  renders schemaVersion 1 and 2). The core declares nothing about the dashboard.
- **Enforcement is 100% runtime, dashboard-side**, when the dashboard loads a
  `report.json`. There is no build-time pin and no compat logic in the core.
- The core has **zero compatibility logic**. It simply emits the current
  `schemaVersion` it knows. All verification lives in the dashboard.

Rationale for runtime-only: with the radical cut the core never pins a dashboard
build, so there is no "build moment" to check. The only place a `report.json` meets
a given dashboard is when a user points a dashboard at a report — that is where the
check belongs. Bonus: it also covers the old-dashboard / new-report case that a
build-time pin never saw.

### Error behavior (dashboard-side)

- **schemaVersion out of range** → explicit message, never a silently broken render:
  `This report uses schemaVersion 3; this dashboard supports 1–2. Upgrade with: <instruction>`
- **`schemaVersion` absent** (pre-split report) → treat as `schemaVersion: 0` and
  show "report predates schema versioning, best-effort support" rather than crash.

### Cross-repo contract test

The only file-level dependency between the repos:

- The core versions fixtures: `tests/fixtures/report.v1.json` (one per
  `schemaVersion`).
- `regis-dashboard` CI fetches these fixtures (raw GitHub URL pinned to a tag) and
  asserts the render works.
- This is a **versioned-file** dependency, not a pipeline dependency — no cadence
  coupling.

## History migration & new repo

### Extraction

`git filter-repo --path apps/dashboard/ --path-rename apps/dashboard/:` on a fresh
clone of the core → new `regis-dashboard` repo with the `apps/dashboard` history
preserved, re-rooted.

`filter-repo` moves **only** `apps/dashboard/`. The Python that _served_ the
dashboard (`regis/server/`, `regis/report/docusaurus.py`,
`regis/commands/dashboard.py`, `regis/commands/archive.py`, the `archive`
cookiecutter) is **deleted from the core and rewritten from scratch** in the new
repo (JS-first: Docusaurus already has `build` + `serve`). We discard ~15 KB of
tested Python to avoid a polyglot repo; its history stays visible in the core's
pre-deletion log.

### Accepted extraction costs

- `git blame` from the core no longer follows into dashboard history.
- PR cross-references (`#NNN`) in migrated commits point at core issues/PRs — dead
  links in the new repo. Acceptable for archived history.
- Cross-cutting commits (one commit touching both core + dashboard, e.g. the
  2026-03-21 Tremor overhaul) appear duplicated in both histories. Inevitable,
  benign.

### New repo bootstrap

- `release-please` + Conventional Commits (same discipline as the core).
- CI: `pnpm build` → primary Docker image (`ghcr.io/trivoallan/regis-dashboard`) +
  dedicated GitHub Pages + optional npm/pip asset publication.
- Settings App for GitHub config (same pattern as the core).
- **No Memory Bank** — a `README.md` + `CONTRIBUTING.md` suffice for a
  single-responsibility front-end project.

### Ordering guard

Extraction (Phase 1) happens **before** core deletion (Phase 2). The core deletes
nothing until the new repo has a working `render`, a published image, and a green
contract test. This avoids any window where users cannot visualize a report.

## Distribution, DX & error handling

### Distribution of regis-dashboard (Docker-primary)

- `docker run --rm -v $PWD:/data ghcr.io/trivoallan/regis-dashboard render /data/report.json`
  → writes a static site.
- `docker run ... serve /data/report.json` → live preview.
- npm (`npx @regis/dashboard render …`) and/or pip are optional overlays, not the
  canonical path.

### User journeys (before → after)

| Need                    | Before (monorepo)         | After (split)                                                    |
| ----------------------- | ------------------------- | ---------------------------------------------------------------- |
| One-shot email share    | `regis analyze --html`    | **unchanged**                                                    |
| Machine data            | `regis analyze --json`    | **unchanged**                                                    |
| Interactive exploration | `regis analyze --site`    | `regis analyze --json` then `regis-dashboard render report.json` |
| Live preview            | `regis dashboard serve`   | `regis-dashboard serve report.json`                              |
| CI archive deliverable  | `regis bootstrap archive` | `regis-dashboard bootstrap archive`                              |

### Discoverability mitigation

The core no longer mentions the dashboard in `--help`. Countered by a post-`analyze`
message (when `--json` is produced without `--html`):

```text
Report written to ./out/report.json
  • Share a single file:    regis analyze --html
  • Explore interactively:   https://github.com/trivoallan/regis-dashboard
```

Plus: core README + doc-site landing point to `regis-dashboard`. `--html` remains
the "works with nothing installed" path.

### New failure points

1. **schemaVersion out of range** → explicit dashboard-side message (see Contract).
2. **Malformed / missing `schemaVersion`** → treated as `schemaVersion: 0`,
   best-effort message.
3. **User runs `regis dashboard …` / `regis analyze --site` post-removal** → not a
   bare "unknown command". Leave a **temporary redirect stub** that errors with:
   ```text
   'regis dashboard' moved to a separate tool in v0.33.
   → https://github.com/trivoallan/regis-dashboard
   ```
   Stub removed after one release cycle (e.g. v0.34). This is the artifact with a
   future obligation — its removal can be scheduled.

### Core versioning

Breaking change (`--site`, `dashboard`, `archive`, `bootstrap archive` all leave).
Bump 0.32 → **0.33** (pre-v1 semver, consistent with recent breaks). Strong
changelog + migration section.

### GitLab CI guide (Sprint 1, in progress)

Must be written **for the post-split world directly** — documenting
`regis analyze --json` + a separate dashboard job (`regis-dashboard render`), not
the old `bootstrap archive`. Otherwise it documents an interface that breaks within
the sprint.

### Test surface

The ~30% of integration tests covering site/dashboard/server **leave** the core.
New core tests: the post-analyze message, the redirect stubs, `schemaVersion`
emission. Core coverage must stay ≥ 90% after removal (watch the ratio — removing
tested code can move it either way).

## Phasing (before v1.0.0-alpha)

### Phase 0 — Core prerequisite (pre-split, non-breaking for users)

- [ ] Add `schemaVersion: 1` to `regis/schemas/report/report.schema.json`
      (+ producers in `regis/report/*`, + tests). Distinct from `version`.
- [ ] Version contract fixtures `tests/fixtures/report.v1.json`.

### Phase 1 — New regis-dashboard repo

- [ ] `git filter-repo` of `apps/dashboard` → new repo, history preserved.
- [ ] Rewrite `render` / `serve` / `bootstrap archive` / `archive add|configure`
      JS-first in the new repo.
- [ ] New-repo CI: `pnpm build` → push Docker image + deploy dedicated GitHub Pages.
- [ ] release-please + Conventional Commits in the new repo.
- [ ] Dashboard declares the supported `report.schemaVersion` range per release.
- [ ] Cross-repo contract test green (new-repo CI fetches core fixtures).

### Phase 2 — Core removal (only after Phase 1 is fully green)

- [ ] Delete `regis/commands/dashboard.py`, `regis/commands/archive.py`,
      `regis/report/docusaurus.py`, `regis/server/`, `regis/dashboard_assets/`,
      `regis/cookiecutters/archive/`.
- [ ] Remove `--site` flag + `html-site` branch from `regis/utils/report.py` and
      `regis/commands/analyze.py`.
- [ ] Remove `[server]` extra + `dashboard_assets` package-data from
      `pyproject.toml`.
- [ ] Remove `apps/dashboard` from `pnpm-workspace.yaml`; delete `cd-dashboard.yml`.
- [ ] Add temporary redirect stubs for `regis dashboard` and `regis analyze --site`.
- [ ] Add post-analyze discoverability message.
- [ ] Bump 0.32 → 0.33 with changelog + migration notes.

### Phase 3 — Docs & cleanup

- [ ] GitLab CI guide written for the post-split world.
- [ ] Core README + doc-site landing point to `regis-dashboard`.
- [ ] Update `activeContext.md` + `progress.md`; close "Monorepo vs split".
- [ ] Schedule redirect-stub removal for the next release cycle (e.g. v0.34).

## Risks / watch-points

- **`docs/website` stays** in the core's pnpm workspace (also Docusaurus) → Node is
  **not** eradicated from the repo, only from the wheel/image build path. Packaging
  goal met; stated explicitly.
- **Contract drift**: without `schemaVersion` discipline, decoupled cadences = silent
  breakage. Phase 0 is blocking. The runtime check + cross-repo contract test are
  the safety net.
- **Coverage dip**: removing tested code in Phase 2 can move the 90% ratio either
  way — verify before merging.
- **DX downgrade**: interactive exploration goes from one command to two tools. This
  is the one genuine deficit; `--html` covers the simple case, the post-analyze
  message covers discovery.
- **decisionLog.md**: PR #628's body claimed a `decisionLog.md` entry that the diff
  never added. This design must actually add the entry.
