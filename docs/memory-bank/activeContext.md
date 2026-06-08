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

- [2026-06-08] **Règles d'identité de plateforme OCI** ([PR #661](https://github.com/trivoallan/regis/pull/661), `whats-new`, non cassant, opt-in):
  - 3 criteria OCI (`platforms-required`/`-whitelist`/`-blacklist`) sur _quelles_ plateformes une image supporte, adossés à une nouvelle projection plate `results.oci.platforms_supported` (`os/arch[/variant]` canonique, dédupliquée). Réutilise `contains_all`/`subset`/`intersects` — aucun nouvel opérateur. Param uniforme `platforms`.
  - **Premier criterion `enable:false` du cœur** : les 3 sont opt-in (désactivés par défaut, sinon bruyants) ; `merge_rules()` auto-active un criterion lié via `criterion:` (un `enable:false` explicite gagne ; un override par slug seul n'active pas). Détail dans `progress.md`. Pattern réutilisable pour de futures règles « politique » à ne pas activer par défaut.
  - 6 tâches subagent-driven (revue spec+qualité par tâche + holistique). Suite 543 PASS, couverture 92.14 %. Spec/plan sous `docs/superpowers/`.

- [2026-06-05] **Dégraissage pré-v1 : suppression de 3 features inutiles** (3 PR distinctes ; brainstorming → spec → plans → subagent-driven, revue conformité + qualité par PR):
  - **PR #648** (`chore(skills)`, non cassant) : suppression de la skill Claude `/create-playbook` (chevauchait `regis bootstrap playbook`). Doc `custom-playbook.md` recadrée sur le bootstrap CLI ; `/create-playbook` retiré de la liste project-skills de `CLAUDE.md`. Porte aussi les **design docs partagés** (spec + 3 plans). Résout le suivi « la skill émet encore `rule:` ».
  - **PR #649** (`feat(cli)!`, bump mineur) : suppression de la commande `regis github update-pr`, redondante depuis l'extraction de [`trivoallan/regis-action`](https://github.com/trivoallan/regis-action). Retrait `github_cli.py` + `test_github_cli.py` + wiring `cli.py` ; doc `integrations/github.md` / `roadmap.md` / `reference/cli.md` élaguée. `gitlab` **conservé** (extraction future notée).
  - **PR #650** (`feat(cli)!`, bump mineur) : suppression de la feature **archive** (`--archive` + `regis/archive/store.py` + schéma `archives.schema.json` source+publié). Déclencheur : **abandon de `regis-dashboard`** (unique consommateur de l'archive) au profit du plugin regis-backstage, qui lit `report.json` et agrège lui-même (ne consomme pas `manifest.json`/`data.json`). Purge des pages archive + stubs dashboard-viewer (`report-viewer.md`, `tools/viewer.mdx`) ; description `schemaVersion` du report schema dépolluée (« standalone dashboard » → « downstream consumers »). `--html` / `report.json` **conservés** (le reste de la Phase 2 dashboard était déjà fait).
  - Suites : 569 (PR2) / 563 (PR1) / 543 (PR3) PASS, couverture ≥ 91,6 %, builds doc verts. Spec : `docs/superpowers/specs/2026-06-05-feature-pruning-design.md` ; plans : `plans/2026-06-05-pr{1,2,3}-*.md`. **⚠ PR1 & PR3 branchées sur `main` éditent des docs communs** (`github.md`, `roadmap.md`, `cli.md`) → rebase de la 2ᵉ mergée. Conservé : `gitlab`, `.github/skills`, `check`/`version`/`list`/`evaluate`. **Reste (hors cœur)** : archiver le dépôt `regis-dashboard` + son image GHCR.

- [2026-06-05] **Vocabulaire : désurcharge de « rule » → modèle à 4 couches** (branche `tritri/vibrant-lamarr-5d23e9`, PR #646, non cassant):
  - `finding → metric → criterion → rule`. Ce qu'un analyzer livre comme condition réutilisable paramétrée (`cve-count`, ex-« default rule »/template) devient un **criterion** ; « rule » est réservé à la décision liée dans le playbook (criterion + options + sévérité + tier). Déclencheur : la page `concepts/rules` confondait mesure/condition et décision (brainstorm produit). Choix `criterion` et non `check` (qui collisionne avec `regis check`).
  - **Rename à fond, non cassant** : `rule.`→`criterion.` partout, y compris le namespace JSON Logic (`rule.params`→`criterion.params`). Le moteur dual-binde `criterion`/`rule` et le loader dual-lit la clé `criterion:`/`rule:` → les playbooks legacy évaluent à l'identique (avec warn de dépréciation) pendant une fenêtre ; coupure à la prochaine majeure. `BaseAnalyzer.default_rules()` → `default_criteria()` + shim bidirectionnel (scan MRO) pour les plugins tiers.
  - **Codemod** `regis playbook migrate` (idempotent, préserve l'évaluation via le dual-bind) ; playbook par défaut migré avec (dogfood) → plus de warnings. Doc : `concepts/rules` recadrée + concept `criterion` + guide `upgrade/rule-to-criterion.md` + page analyzers (metric/finding/component).
  - 4 tâches via subagent-driven-development (revue spec+qualité par tâche + revue finale holistique qui a rattrapé le playbook par défaut auto-déprécié). Suite 569 PASS, couverture 91.68 %. `feat(playbook)` non cassant → bump mineur. Plan : `plans/2026-06-05-rename-rule-to-criterion-plan.md` ; décision : `decisionLog.md`. Suivi : skill `/create-playbook` émet encore `rule:` (chip).
- [2026-06-04] **Extraction de l'action GitHub → dépôt dédié `trivoallan/regis-action`** (branche `claude/github-action-extraction-6zdu5`, breaking):
  - **Décision** (voir `decisionLog.md`) : le cœur **arrête de livrer l'action**. L'action composite (`action.yml`, racine, ex-Marketplace `trivoallan/regis@vX`) part dans [`trivoallan/regis-action`](https://github.com/trivoallan/regis-action), versionnée indépendamment (`v1.x`, release-please `simple` + `tag-major.yml` pour le tag flottant `v1`). L'input `version:` continue de cibler une image cœur `ghcr.io/trivoallan/regis:<tag>` ; le `uses:` et le `version:` restent indépendants. **Démarrage neuf** (pas de `git filter-repo`, contenu trivial). Calque la décision dashboard du 2026-06-01, en plus simple (pas de code, pas de build).
  - **Nettoyage cœur livré** : suppression de `action.yml` + `.github/workflows/ci-action-dogfood.yml` + l'exception de SHA-pinning auto-référencée dans `ci-lint.yml`. Docs repointées vers `trivoallan/regis-action@v1` avec note de migration (`README.md`, `docs/website/docs/usage/integrations/github.md`) ; `versioned_docs/` (snapshots figés) intacts.
  - **Bug latent corrigé** : l'`action.yml` extrait (copie conforme du cœur) passait encore `regis analyze --site`, option retirée en 0.33 (decouple dashboard) au profit de `--html` → échec contre `regis:latest`. Corrigé en `--html` dans `regis-action` (`4dd2b9b`) avant de couper `v1.0.0`.
  - **Issue** : dépôt `regis-action` créé via l'API ; le périmètre de session (`trivoallan/regis` seul) ayant bloqué le push, le contenu a d'abord transité par `regis-action-staging/`. Le mainteneur a ensuite poussé le bundle (`5ab906d`), coupé `v1.0.0` + `v1` flottant, posé la branch protection (check requis `Lint action`), vérifié le self-test, et retiré le dossier de staging de la branche PR. **Reste manuel** : secret PAT `RELEASE_PLEASE_TOKEN` + publication Marketplace (web). `feat(ci)!` → bump pré-v1. PR #644.
- [2026-06-01] **Playbook format → enveloppe Kubernetes (PR #640, breaking)**:
  - Les playbooks adoptent `apiVersion: regis.trivoallan.dev/v1alpha1` / `kind: Playbook` / `metadata` / `spec`. `schemaVersion` (entier) → `apiVersion` ; `metadata` style Backstage (`name`=id, `title`=affichage, `description`, SemVer du bundle → label `app.kubernetes.io/version`) ; `tiers`/`rules`/`badges`/`integrations`/`links` sous `spec`. Sémantique d'évaluation inchangée.
  - **Rupture nette** (pré-v1) : le loader rejette l'ancien format à plat ; `regis playbook upgrade` restructure les playbooks legacy (drop `pages`/`sections`/`sidebar`, idempotent). Nouveau `regis/schemas/playbook/v1alpha1/playbook.schema.json` ; registre indexé par `apiVersion` ; ancien schéma `v1` supprimé. Le loader valide puis **normalise** l'enveloppe en dict aplati → consommateurs en aval inchangés (approche A).
  - Champ d'audit rapport `schema_version` → `api_version` (`evaluator.py`) ; schémas de sortie `result`/`report` alignés. Le `schemaVersion` entier de l'enveloppe report (`REPORT_SCHEMA_VERSION`) est un concept distinct, intact. Default + 2 cookiecutters + skill `/create-playbook` + docs migrés.
  - Livré via skills empilées (brainstorming → writing-plans → subagent-driven-development, 10 tâches TDD, 1 implémenteur + revue indépendante par tâche). Suite 539 PASS, couverture 91.66 %. `feat(playbook)!` → bump 0.33 → 0.34. Décision : `decisionLog.md` ; spec : `docs/superpowers/specs/2026-06-01-playbook-kubernetes-kinds-design.md`.
- [2026-06-01] **Dashboard full decouple — décision + Phase 0 + Phase 1 livrées**:
  - **Décision** (voir `decisionLog.md`) : le cœur **arrête complètement de livrer la dashboard**. `apps/dashboard` est extrait dans un dépôt dédié `regis-dashboard`. Lien unique : contrat `report.json` + `schemaVersion` entier, vérifié **100 % au runtime côté dashboard** ; le cœur n'a **aucune** logique de compatibilité. **Supersède** l'approche OCI/`ToolFetcher` (PR #628, fermée).
  - **Coupe radicale** : `serve` standalone = **static-preview-only**. Le backend GitLab proxy + webhooks/SSE (`regis/server/`) est abandonné, pas réécrit en Node ; `gitlab.tsx` + ses 3 composants exclusifs sont retirés à l'extraction.
  - **Phase 0 livrée (PR #630)** : champ `schemaVersion` entier requis sur l'enveloppe `report.json` (`regis/schemas/report/report.schema.json`), constante `REPORT_SCHEMA_VERSION` + helper `ensure_schema_version()` dans `regis/utils/report.py`, producteur estampillé + backfill des **trois** chemins de chargement (rerun, evaluate, cache-hit) dans `regis/commands/analyze.py`, fixture contrat `tests/fixtures/report.v1.json`. Suite 626 PASS, couverture 91.18 %. Breaking (`feat(schema)!`) → bump pré-v1 0.32 → 0.33.
  - **Phase 1 livrée** (dépôt [`trivoallan/regis-dashboard`](https://github.com/trivoallan/regis-dashboard), plans #632) :
    - **1a** : extraction `git filter-repo` (historique préservé) → GitHub Pages dédié, `v0.1.0`, release-please + Conventional Commits + branch protection + **PAT** (`RELEASE_PLEASE_TOKEN`) pour que les PR de release déclenchent la CI (le `GITHUB_TOKEN` par défaut ne le peut pas — deadlock classique). Demo `report.json` = la fixture `report.v1.json` du cœur.
    - **1b** (PR #2) : CLI TypeScript (`commander`) — `render`/`serve`/`archive add|configure`/`bootstrap archive` — ports fidèles de `regis/report/docusaurus.py`, `commands/archive.py`, `archive/store.py`, le cookiecutter archive. Image Docker `node:20-alpine` (Docusaurus offline) ; publication GHCR sur tags `v*` ; tests vitest. `vitest@2.x` épinglé (le `vite-node@3.2.5` de la branche 3.x renvoie 404 sur notre registre).
    - **1c** (PR #4) : garde runtime `schemaVersion` dans `ReportProvider` (`checkSchemaCompat`, plage `{min:1,max:1}`) — hors plage → UI d'erreur, absent → bannière best-effort, dans la plage → rendu. Test de contrat offline (demo report committé) + workflow de dérive cross-repo live (fetch de la fixture du cœur, hebdo + sur PR).
    - **Cœur inchangé** au-delà de Phase 0 ; la dashboard détient 100 % de la logique de compatibilité. Prochaine release dashboard `0.2.0` (PR de release ouverte) → première image GHCR. **Phase 2** (retrait du code dashboard du cœur) reste à faire, désormais débloquée.
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

- **Monorepo vs split** (pré-v1) : ✅ **résolu [2026-06-01]** — split décidé via la coupe radicale (le cœur n'embarque plus la dashboard). Détail dans `decisionLog.md` et l'entrée Recent Changes ci-dessus.
