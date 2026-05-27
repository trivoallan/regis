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
  - New **Craftsmanship** principle: _spec-based programming with stacked skills_ — methodology (composing Superpowers skills with project skills like `/create-playbook`, `/verify`, `/code-review`) and architecture (declarative JSON Schemas / playbook YAML / JSON Logic over imperative code).
  - **Git workflow**: made the rebase requirement explicit — always rebase feature branches on the latest `main` (never merge `main` back in).
  - Reference material relocated to `systemPatterns.md`: full CI/CD Gotchas section and full Commit Scopes list.
- [2026-04-22] **Claude Workflows CI/CD Fixes**: SHA-pinned actions dans `claude-code-review.yml` et `claude.yml`, ajout des permissions workflow-level (CKV2_GHA_1), correction linting YAML. PR merged to main.
- [2026-04-22] **M002/S02 — Snapshot publication date**: Ajout du flag `--markdown` à `regis analyze`, backfill dates v0.27.0/v0.26.2. 460 tests passent.
- [2026-04-21] **GitHub Actions Auth Unification**: Les 6 workflows migrent vers `actions/create-github-app-token@v1` avec `REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY`. `peaceiris/actions-gh-pages` utilise `personal_token:`.
- [2026-03-21] **Tremor UI overhaul** (dashboard) : navbar identity badges, StatCard KPI, 12 pages analyzers, tables paginées CVE. Merged.

## Decisions in Progress

- **Monorepo vs split** (pré-v1) : exploration structurée, pas encore de décision. Inconnues : patterns contributeurs futurs, cadence post-v1, gouvernance à l'échelle.
