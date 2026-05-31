# Progress

## In Progress

**Sprint 1 (19 mai → 2 juin 2026)** — voir `roadmap.md` pour le détail.

- Image-size round 3 — slim/full variants, lazy-loaded scanners (PR pending, see [2026-05-31] in `activeContext.md`)
- Moratoire snapshots doc
- Playbook bundle format
- Finitions site de doc
- Guide GitLab CI

## Completed (Recent)

- **Docker image size reduction — round 2 (2026-05-29)**:
  - Removed git/jq from runtime; FastAPI/Uvicorn → optional `[server]` extra; `--no-compile` venv + cache prune.
  - Measured arm64 tar 186 MB → 138 MB (round 2); 244 MB → 138 MB cumulative (~43 %). CI ceiling tightened 250 → 220 MB.
  - Deferred (own brainstorm): crane-for-skopeo (biggest remaining win), alpine/wolfi base, UPX on Go binaries.

- **Docker image size reduction (2026-05-29, v0.32.0)**:
  - 4-stage Dockerfile; runtime image strips Node.js, pnpm, curl, gnupg, build-essential.
  - Breaking change: `bootstrap archive --dev/--repo` is host-only (structured error message guides install).
  - Measured tar size 244 MB → 186 MB (~24%); below the 50% target — skopeo apt layer dominates the remainder.
  - Hardcoded 250 MB ceiling enforced in CI via `wemake-services/docker-image-size-limit`.
  - `release-please-config.json`: `bump-minor-pre-major: true` so the break bumps to 0.32.0, not 1.0.0.

- **CLI quality-of-life batch (2026-05-26, PRs #595–#603)** — one PR per issue #581–#589:
  - `regis playbook validate <path>` (#600) — offline schema validation of a playbook bundle/file.
  - `regis analyze --skip NAME` (#598) — exclude named analyzers (repeatable).
  - Env vars `REGIS_PLAYBOOK`, `REGIS_PLATFORM`, `REGIS_OUTPUT`, `REGIS_OUTPUT_DIR`, `REGIS_MAX_WORKERS` (#599).
  - Top-level `-q` / `--quiet` (#601) — gates progress/info; failures and errors still print. Wired through `ctx.obj["quiet"]` so `regis.utils.report` helpers consult it via `click.get_current_context`.
  - Per-analyzer progress + timing line with red-styled failures (#602). Timing captured inside the worker thread (excludes ThreadPool queue wait).
  - One-line `Playbook · <name>  N rules · P passed · F failed (<level>)` summary printed when `--playbook` is explicitly provided (#603). Reads `playbook_name` (schema field), tolerates `level: null`, treats `status: "incomplete"` as a separate `⚠` bucket.
  - `regis rules list --filter-level/--filter-provider` (#597), `regis rules show --format yaml` (#595).
  - DEBUG-level per-analyzer timing log `analyzer X finished in N.NNs` (#596).
  - CLI reference doc (`docs/website/docs/reference/cli.md`) and env vars table in `usage/configuration.md` brought in sync.

- **CLAUDE.md restructure (2026-05-23, PR #592)**:
  - File reduced from ~180 → ~90 lines; split into agent essentials + project policy.
  - Added _spec-based programming with stacked skills_ craftsmanship principle (Superpowers methodology + project skills + declarative-spec architecture).
  - Made the rebase-only feature-branch workflow explicit.
  - Added pnpm commands for `apps/dashboard`; dropped stale devcontainer reference; fixed broken whats-new.md link.
  - Reference material (CI/CD gotchas, full commit scopes list) moved to `docs/memory-bank/systemPatterns.md`.

- **Single-file HTML report (2026-04-25)**:
  - Flag `--html` sur `regis analyze` et `regis evaluate` générant un `report.html` self-contained (HTML+CSS, sans JS ni dépendances externes).
  - Option `--sections` : `all` (défaut), `summary`, ou liste d'analyzer slugs.
  - Format interne `"html"` renommé `"html-site"` (flag user-facing `--site` inchangé).
  - Nouveaux fichiers : `regis/report/html.py`, `regis/templates/html/report.html.j2`.
  - 23 nouveaux tests (16 unit + 7 integration), 91% coverage totale.

- **M002/S02 — Snapshot publication date (2026-04-22)**:
  - Backfill dates v0.27.0 (→ 2026-04-09) et v0.26.2 (→ 2026-04-03).
  - Flag `--markdown` sur `regis analyze` (pas de shorthand `-m` — conflit avec `--meta`).
  - Helper `_render_markdown()` et branche `elif fmt == 'md':` dans `regis/utils/report.py`.
  - 8 tests unitaires + script `scripts/verify_s02.py` (7/7 checks). 460 tests passent.

- **Claude Workflows CI/CD Fixes (2026-04-22)**:
  - SHA-pinning des GitHub Actions, permissions workflow-level, corrections YAML linting.
  - Trunk checks passants, PR merged to main.

- **GitHub Actions Auth Unification (2026-04-21)**:
  - 6 workflows migrés vers `actions/create-github-app-token@v1`.
  - `peaceiris/actions-gh-pages` : `personal_token:` à la place de `github_token:`.

## Completed (Historical)

- Memory Bank consolidé sous `docs/memory-bank/`.
- Core CLI, analyzers clés (Skopeo, Trivy, Hadolint, etc.), évaluation playbook JSON Logic.
- Docusaurus : migration depuis Antora, versioning dynamique, documentation à code.
- Schémas JSON relocalisés dans `regis/schemas/` pour le packaging.
- Refactoring commande `generate` → groupe `bootstrap` (`bootstrap playbook`, `bootstrap archive`, `bootstrap archive-repo`).
- Affichage des post-install notes après bootstrap.
- Viewer de rapport moderne Docusaurus/React (`apps/dashboard`) — remplacement Jinja2.
- Support artifacts GitLab avec flag `--base-url` et calcul dynamique du `baseUrl`.
- Trunk : migration depuis Super-Linter, linting unifié local + CI.
- `show_if` / `check_if` sur les items de checklist playbook.
- Refactoring pipeline GitLab CI (4 jobs indépendants : analyze, push_results, set_labels, set_checklist).

## Future Roadmap

Voir `docs/memory-bank/roadmap.md` pour le détail des sprints.
