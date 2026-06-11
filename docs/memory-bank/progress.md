# Progress

## In Progress

**Sprint 1 (19 mai → 2 juin 2026)** — voir `roadmap.md` pour le détail.

- Image-size round 3 — slim/full variants, lazy-loaded scanners (PR pending, see [2026-05-31] in `activeContext.md`)
- Moratoire snapshots doc
- Playbook bundle format
- Finitions site de doc
- Guide GitLab CI

## Completed (Recent)

- **Migration Dependabot → Renovate (2026-06-11)** — app Mend hébergée (brainstorming → spec → plan) :
  - Preset constellation partagé `.github/renovate-constellation.json5` dans le cœur, étendu par `renovate.json5` (cœur) + les satellites. Updates non-major groupées par écosystème + automerge ; majors en draft (skippées par `repo-automerge.yml`) ; sécurité toutes sévérités automergée hors-schedule ; label `dependencies` exclu de `repo-autorebase.yml`.
  - Suppression du workflow critical-only `repo-dependabot-critical-vulns.yml` + du `dependabot.yml` ; PR d'hygiène (surface JS racine morte purgée) ; doc memory-bank/tools-management/guides github-actions recadrés. Spec : `docs/superpowers/specs/2026-06-10-renovate-migration-design.md` ; plan : `docs/superpowers/plans/2026-06-10-renovate-migration.md`. **Reste** : étape manuelle mainteneur (app Mend + désactivation Dependabot security updates) + onboarding satellites.

- **Règles d'identité de plateforme OCI (2026-06-08, [PR #661](https://github.com/trivoallan/regis/pull/661), `whats-new`)** — non cassant, opt-in (brainstorming → writing-plans → subagent-driven, 6 tâches, revue spec+qualité par tâche + revue finale holistique):
  - 3 nouveaux criteria OCI sur _quelles_ plateformes (le `platforms-count` existant ne compte que le nombre) : `platforms-required` (`contains_all` = au moins), `platforms-whitelist` (`subset` = uniquement), `platforms-blacklist` (`!intersects` = aucune). Param uniforme `platforms` (cf. `required-labels`/`labels`). Opérateurs JSON Logic **existants** — aucun nouvel opérateur.
  - Nouvelle projection plate `results.oci.platforms_supported` = liste dédupliquée de chaînes canoniques `os/arch[/variant]` (filtre `unknown`, ordre préservé via `dict.fromkeys`) ; champ **optionnel** ajouté à `oci.schema.json` (`additionalProperties:false`). Matching par égalité stricte (`linux/arm64` ≠ `linux/arm64/v8`).
  - **Opt-in** (décision post-revue) : les 3 criteria sont `enable: false` (sinon bruyants par défaut — whitelist échoue sur une image multi-arch large, required sur toute image mono-arch). `merge_rules()` auto-active un criterion instancié via une liaison `criterion:` (un `enable: false` explicite reste prioritaire) ; un override par slug seul (Case B) **n'active pas** un criterion opt-in. C'est le **premier** criterion `enable:false` du cœur — le mécanisme d'auto-activation est nouveau dans le moteur.
  - Pages de référence régénérées depuis `default_criteria()` ; note opt-in dans `reference/analyzers/oci.md` + le spec. Suite 543 PASS, couverture 92.14 %. Spec : `docs/superpowers/specs/2026-06-08-oci-platforms-whitelist-blacklist-design.md` ; plan : `docs/superpowers/plans/2026-06-08-oci-platforms-whitelist-blacklist.md`. **Reste** : merge de la PR (main protégée).

- **Dégraissage pré-v1 — suppression de 3 features inutiles (2026-06-05)** — 3 PR distinctes (brainstorming → spec → plans → subagent-driven):
  - **PR #648** (`chore(skills)`, non cassant) — skill Claude `/create-playbook` retirée (chevauchait `regis bootstrap playbook`) ; `custom-playbook.md` + `CLAUDE.md` mis à jour ; porte les design docs partagés (spec + 3 plans).
  - **PR #649** (`feat(cli)!`, mineur) — commande `regis github` retirée (redondante depuis l'extraction de `trivoallan/regis-action`) ; `gitlab` conservé.
  - **PR #650** (`feat(cli)!`, mineur) — feature **archive** retirée (`--archive` + `regis/archive` + schéma) suite à l'**abandon de `regis-dashboard`** au profit de regis-backstage (qui ne consomme pas le format archive) ; pages archive/viewer purgées ; `--html`/`report.json` conservés.
  - Suites 569/563/543 PASS, couverture ≥ 91,6 %. Spec : `docs/superpowers/specs/2026-06-05-feature-pruning-design.md`. ⚠ PR1/PR3 (sur `main`) éditent des docs communs → rebase de la 2ᵉ mergée.

- **Vocabulaire « rule » → modèle 4 couches (2026-06-05, PR #646)** — non cassant:
  - `finding → metric → criterion → rule` : les analyzers livrent des **criteria** (conditions réutilisables paramétrées, ex-« default rules ») ; « rule » = la décision liée dans le playbook. Clé playbook `criterion:` (legacy `rule:` déprécié mais fonctionnel), namespace `criterion.params.*`. Choix `criterion` (pas `check`, collision `regis check`).
  - Moteur dual-bind + loader dual-read + warn de dépréciation ; `default_rules()`→`default_criteria()` (shim tiers) ; codemod `regis playbook migrate` (idempotent, préserve l'évaluation) ; playbook par défaut migré (dogfood). Doc recadrée + guide `upgrade/rule-to-criterion.md` + page analyzers (metric/finding/component).
  - Suite 569 PASS, couverture 91.68 %. `feat(playbook)` non cassant → mineur. Décision : `decisionLog.md` ; plan : `plans/2026-06-05-rename-rule-to-criterion-plan.md`. Suivi : skill `/create-playbook` émet encore `rule:`.

- **GitHub Action extraction → dépôt dédié (2026-06-04)** — breaking, pré-v1:
  - L'action composite quitte le cœur pour [`trivoallan/regis-action`](https://github.com/trivoallan/regis-action), versionnée indépendamment (`v1.x`, release-please `simple` + `tag-major.yml`). Suppression côté cœur de `action.yml`, `ci-action-dogfood.yml`, et de l'exception de SHA-pinning dans `ci-lint.yml`.
  - Docs repointées vers `trivoallan/regis-action@v1` + note de migration (`README.md`, guide `integrations/github.md`) ; snapshots `versioned_docs/` laissés intacts.
  - Bug latent corrigé pendant l'extraction : l'`action.yml` passait `analyze --site` (retiré en 0.33) → `--html` dans `regis-action` (`4dd2b9b`).
  - Dépôt [`trivoallan/regis-action`](https://github.com/trivoallan/regis-action) live : bundle poussé (`5ab906d`), `v1.0.0` + `v1` flottant coupés, branch protection (`Lint action`), self-test vert, staging retiré de la branche PR. Reste manuel : secret PAT `RELEASE_PLEASE_TOKEN` + publication Marketplace. `feat(ci)!`, PR #644. Décision : `decisionLog.md` ; plan : `docs/memory-bank/plans/github-action-extraction-plan.md`.

- **Playbook format → enveloppe Kubernetes (2026-06-01, PR #640)** — breaking, pré-v1:
  - `apiVersion: regis.trivoallan.dev/v1alpha1` / `kind: Playbook` / `metadata` (style Backstage) / `spec` ; remplace l'entier `schemaVersion`. Le loader valide contre le nouveau schéma `v1alpha1` puis normalise vers la forme aplatie interne (consommateurs inchangés, approche A) ; ancien schéma `v1` supprimé.
  - `regis playbook upgrade` migre les playbooks legacy à plat (drop `pages`/`sections`/`sidebar`, idempotent) ; `validate` affiche apiVersion/kind. Default + 2 cookiecutters + skill `/create-playbook` + docs migrés. Audit rapport `schema_version` → `api_version` (le `schemaVersion` de l'enveloppe report reste intact).
  - 10 tâches TDD via subagent-driven-development ; suite 539 PASS, couverture 91.66 % ; `feat(playbook)!` → 0.33 → 0.34.

- **Dashboard decouple — Phase 1 (2026-06-01)** — standalone repo [`trivoallan/regis-dashboard`](https://github.com/trivoallan/regis-dashboard):
  - 1a: `git filter-repo` extraction (history preserved) → own GitHub Pages, `v0.1.0`, release-please + PAT-triggered CI + branch protection.
  - 1b (PR #2): TS CLI (`render`/`serve`/`archive add|configure`/`bootstrap archive`) + `node:20-alpine` Docker image (GHCR on `v*` tags) + vitest.
  - 1c (PR #4): runtime `schemaVersion` compat gate in `ReportProvider` + offline & live cross-repo contract tests.
  - Core touched only by Phase 0 (#630). Dashboard owns all compat logic; GitLab live-backend dropped (static-preview-only). `0.2.0` release PR open. Phase 2 (core cleanup) still pending.

- **Dashboard decouple — Phase 0 : contrat `schemaVersion` (2026-06-01, PR #630)**:
  - Champ entier `schemaVersion` requis sur l'enveloppe `report.json` ; constante `REPORT_SCHEMA_VERSION` + helper `ensure_schema_version()` ; producteur estampillé + backfill des trois chemins de chargement (rerun/evaluate/cache-hit).
  - Fixture de contrat cross-repo `tests/fixtures/report.v1.json`. Suite 626 PASS, couverture 91.18 %. Breaking → 0.32 → 0.33.
  - Décision globale (coupe radicale, static-preview-only) consignée dans `decisionLog.md` ; supersède PR #628 (fermée).

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

- **M002/S05 — Dependency upgrade (2026-04-22)**:
  - `pipenv update` : Pipfile.lock rafraîchi (marshmallow reste 3.26.2, pas de pin v4 nécessaire).
  - `pnpm update` au workspace root : pnpm-lock.yaml root unique rafraîchi (15 paquets ajoutés, 2 retirés).
  - `pinact 3.9.0 --exclude 'trivoallan/regis'` : 11 workflows mis à jour (SHA-pins), 3 major bumps acceptés (attest-build-provenance v2→v4, fetch-metadata v2→v3, paths-filter v3→v4).
  - 460 tests passent, 90.74% coverage.

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
