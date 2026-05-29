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

- **Monorepo vs split** (pré-v1) : exploration structurée, pas encore de décision. Inconnues : patterns contributeurs futurs, cadence post-v1, gouvernance à l'échelle.
