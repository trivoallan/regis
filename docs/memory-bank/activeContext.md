# Active Context

## Current Objective

**Sprint 1 (19 mai → 2 juin)** — Fondations : nettoyer, stabiliser, poser la base playbook.

Items en cours :

| Item                        | Description                                                                                                          | Status      |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Moratoire snapshots doc** | Arrêter la génération de snapshots versionnés. Purger les vieilles versions. Désactiver `release-snapshot.yml`.      | Not Started |
| **Playbook bundle format**  | Playbooks sous forme de répertoire : `playbook.yaml` + `README.md` + `inputs.schema.json`. Nouveau `InputsAnalyzer`. | Not Started |
| **Finitions site de doc**   | Branding, CI hardening, navigation sidebar, SEO baseline.                                                            | Not Started |
| **Guide GitLab CI**         | Process d'intégration regis dans un pipeline GitLab, multi-archives, déploiement rapport.                            | Not Started |

Voir `docs/memory-bank/roadmap.md` pour le détail complet.

## Recent Changes

- [2026-05-31] **Docker image size — round 3** (PR pending):
  - Lazy-loaded scanner binaries via new `regis.tools` package: manifest (`regis/tools/manifest.yaml` pins grype/syft/trufflehog/hadolint/dockle/regctl with sha256 per arch + optional cosign issuer), typed loader, `ToolFetcher` (cache, sha256, flock concurrency, mirror, cosign best-effort, fetch_all), `ensure_tool()` bridge in `regis/utils/process.py`.
  - Six analyzer/wrapper sites (`grype.py`, `syft.py`, `trufflehog.py`, `regctl.py`, `hadolint.py`, `dockle.py`) routed through `ensure_tool` — host PATH still short-circuits; manifest-listed tools fall back to the fetcher when absent.
  - New CLI: `regis bootstrap tools [--check|--tool NAME]`. `regis doctor` gains a "Tools (manifest)" section reporting ✓ cached / ⏩ not cached / ✗ sha mismatch.
  - **Dockerfile**: two-variant build (`--build-arg VARIANT=slim|full`). Runtime base switched from `python:3.14-slim` to `python:3.11-alpine` (gcompat added in full for hadolint's Haskell runtime). Distroless was attempted and abandoned (the `--copies` venv binary fails to find `libpython3.11.so.1.0`; copying the lib in worked but produced a heavier full image than the original — see `docs/superpowers/specs/2026-05-31-image-size-round-3-design.md` for the decision trail).
  - **Measured sizes** (local arm64): slim 156 MB (was 372 MB single-variant — **-58 %**), full 484 MB (was 372 MB — **+30 %**, the regression is tracked as a follow-up).
  - **CI**: `cd-docker.yml` matrix on variant (slim → `:VERSION`/`:latest`, full → `:VERSION-full`/`:latest-full`, badge regeneration slim-only). `ci-image-size.yml` per-variant ceilings (slim 200 MB / full 520 MB). New `ci-tools-manifest.yml` (sha256 drift check, PR + weekly cron). New `ci-tools-fetch-smoke.yml` (cold-fetch + warm-analyze alpine:3.20 end-to-end).
  - **Breaking** (justifies 0.32 → 0.33): `:latest` no longer ships scanners by default (lazy fetch on first use); air-gapped users must use `:latest-full` or set `REGIS_TOOLS_MIRROR`. Python base bumped 3.14 → 3.11 (still within `requires-python>=3.10`). User stays `regis:1001`.
  - New env vars: `REGIS_CACHE_DIR`, `REGIS_TOOLS_MIRROR`, `REGIS_OFFLINE`, `REGIS_REQUIRE_COSIGN`. Docs: new `docs/website/docs/usage/tools-management.md` (user + maintainer guidance), `configuration.md` env table append, `cli.md` `bootstrap tools` + `doctor` Tools section, README image-variants table.
  - **Test surface**: +35 new tests (4 manifest schema, 4 manifest loader, 12 fetcher, 1 cosign, 3 ensure_tool, 2 bootstrap CLI, 1 doctor extension, plus minor existing-test adjustments). Full suite 597 PASS, coverage 90.95 %.
- [2026-05-31] **Playbook versioning** (PR not yet open): two new required fields (`schemaVersion: 1` integer + `version: 1.0.0` SemVer) on every playbook, schema registry under `regis/schemas/playbook/v1/`, loader hard-fails on missing/unknown, `regis playbook upgrade` migrates legacy bundles in place, report propagates `playbook_version` + `schema_version` for audit. Breaking change.
- [2026-05-30] **v0.32.0 cut + image-size badge fix + SBOM release fix**:
  - Released **v0.32.0** (Release Please PR #576 squash-merged) — ships round-2 trims + the skopeo→regctl rename. `ghcr.io/trivoallan/regis:0.32.0` + `:latest` published.
  - **Docker image-size badge** (PR #613, merged): the third-party `ghcr-badge.egpl.dev` service was **suspended** (HTTP 503), breaking the README badge. Replaced with a committed `image-size-badge.svg` regenerated on every `cd-docker.yml` publish via shields.io and surfaced back through an auto-PR on `docs/image-size-badge` (same pattern as `coverage-badge.svg`, app-token-driven so it ignores the job's `contents` perm). Badge now shows the **extracted on-disk size (~337 MB amd64)** — the real post-pull footprint — not the compressed transfer size (~108 MB) the old badge advertised.
  - **Size-measurement gotcha**: `docker image ls` under the local containerd snapshotter reports **484 MB** for this image — a display quirk, NOT a regression. Authoritative breakdown (gunzip per layer): trivy 160 MB, debian-slim base 81 MB, python build 38 MB, venv 29 MB, dockle 25 MB, regctl 12 MB. CI gate (`ci-image-size.yml`, overlay2) measures ~337 MB against a 360 MB ceiling; added `show_current_size: true` so the value shows in PR logs.
  - **SBOM-to-release fix** (PR #618, pending auto-merge): `cd-docker` ran with `contents: read`, so `anchore/sbom-action` failed at "Attaching SBOMs to release" (`Resource not accessible by integration`). Image still published (build step runs first), but **every tagged release since v0.30.0 silently shipped without CycloneDX/SPDX SBOM assets**. Fixed by elevating the job to `contents: write`.
- [2026-05-29] **Docker image size — round 2**:
  - Dropped `git` + `jq` from the runtime apt layer (git is host-only via the bootstrap `--repo` flow; jq has no runtime caller).
  - Moved `fastapi` + `uvicorn[standard]` to a `[server]` optional extra; in-container `dashboard serve` now errors with a `pip install regis[server]` hint (breaking, consistent with the round-1 bootstrap decision). `dev` extra still pulls them so tests are unchanged.
  - `pip install --no-compile` + venv `__pycache__`/`*.pyc` prune.
  - Tightened CI ceiling 250 → 220 MB (conservative; amd64 not measured locally). Measured arm64 tar: 186 → 138 MB (round 2); 244 → 138 MB cumulative (~43 %).
- [2026-05-29] **Docker image refactor (breaking, v0.32.0)**:
  - Rewrote `Dockerfile` as 4-stage build (`frontend-builder`, `python-builder`, `tools-fetcher`, `final`).
  - Removed Node.js, pnpm, curl, gnupg, build-essential from runtime image.
  - `regis bootstrap archive --dev/--repo` now host-only with structured error message via `_NODE_INSTALL_HINT` / `_PNPM_INSTALL_HINT`.
  - Extended `require_tool()` with optional `install_hint` argument.
  - Strict `.dockerignore` (excludes `docs/`, `tests/`, `*.md` except `README.md`).
  - `release-please-config.json`: `bump-minor-pre-major: true` so 0.31.0 → 0.32.0 instead of 1.0.0.
  - New CI gate `ci-image-size.yml` enforces 250 MB ceiling via `wemake-services/docker-image-size-limit`.
  - Measured reduction: tar size 244 MB → 186 MB (~24 %); below the 50 % target — skopeo apt layer dominates the remainder.
- [2026-05-26] **CLI quality-of-life batch** (PRs #595–#603, all merged): nine one-issue-per-PR features landed on `main` from issues #581–#589.
  - `regis doctor` (#590, prior) checks external binary availability.
  - `regis playbook validate` (#600) validates a playbook bundle/file offline against the JSON Schema.
  - `regis analyze --skip NAME` (#598) excludes named analyzers from a run.
  - `REGIS_PLAYBOOK` / `REGIS_PLATFORM` / `REGIS_OUTPUT` / `REGIS_OUTPUT_DIR` / `REGIS_MAX_WORKERS` env vars (#599) shorten CI invocations.
  - Top-level `-q` / `--quiet` (#601) clamps logs to ERROR and silences progress/info, keeping analyzer failures visible.
  - Per-analyzer progress line with `(s)` timing (#602) + analyzer-failure lines in red. Timing measured inside the worker so queue-wait isn't counted.
  - One-line `Playbook · <name>  N rules · P passed · F failed (<level>)` summary printed when `--playbook` is explicitly provided (#603).
  - `regis rules list --filter-level/--filter-provider` (#597), `regis rules show --format yaml` (#595), DEBUG `analyzer X finished in Ns` log (#596).
  - Documentation refreshed in `docs/website/docs/reference/cli.md` and `usage/configuration.md`.
- [2026-05-23] **CLAUDE.md restructure** (PR #592, merged): file dropped from ~180 → ~90 lines.
  - Split into agent essentials (top) and project policy (bottom). Memory Bank section condensed to a 3-line pointer (no longer duplicates `RULES.md`).
  - New **Craftsmanship** principle: _spec-based programming with stacked skills_.
  - **Git workflow**: made the rebase requirement explicit — always rebase feature branches on the latest `main` (never merge `main` back in).
  - Reference material relocated to `systemPatterns.md`: full CI/CD Gotchas section and full Commit Scopes list.
- [2026-04-22] **Claude Workflows CI/CD Fixes**: SHA-pinned actions, ajout permissions workflow-level, correction linting YAML.
- [2026-04-22] **M002/S02 — Snapshot publication date**: flag `--markdown` à `regis analyze`, backfill dates v0.27.0/v0.26.2.
- [2026-04-21] **GitHub Actions Auth Unification**: workflows migrent vers `actions/create-github-app-token@v1`.
- [2026-03-21] **Tremor UI overhaul** (dashboard) : navbar identity badges, StatCard KPI, 12 pages analyzers, tables paginées CVE.

## Decisions in Progress

- ~~**Monorepo vs split** (pré-v1)~~ : **tranché [2026-05-31]** → split du dashboard dans un dépôt dédié, artefact OCI épinglé consommé via `ToolFetcher` au build-time. Voir `decisionLog.md` [2026-05-31] + plan `plans/2026-05-31-dashboard-repo-split-plan.md`. Cible : avant v1.0.0-alpha.
