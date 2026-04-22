# Active Context

## Current Objective

**Primary**: Memory Bank source of truth consolidated under `docs/memory-bank/`.

**Secondary (reflection in progress)**: Pre-v1 architecture decision — exploring whether to keep monorepo structure vs. split before v1. This is NOT a decision yet, just structured thinking space. Key unknowns: future contributor patterns, post-v1 release cadence, governance at scale. To explore: test contributor workflows, project post-v1 evolution, consult multi-team contributors, document constraints (Harbor integration, JSON schemas, regis-specific rules).

## Recent Changes

- [2026-04-21] Memory Bank update requested; no new application code changes were detected during the scan.
- [2026-04-21] Supplemental planning files (`decisionLog.md`, `roadmap.md`) reviewed and kept alongside the core memory bank.
- Refactored `.gitlab-ci.yml` (consumer cookiecutter): split monolithic `analyze_image` into four independent jobs:
  - `analyze_image` — runs `regis analyze`, produces `reports/` artifacts.
  - `push_results` — commits report to branch, prepends report URL to MR description, posts MR comment.
  - `set_labels` — applies scoped GitLab labels from `playbook.labels` via API.
  - `set_checklist` — appends Markdown review checklist from `playbook.mr_description_checklist` to MR description.
- Fixed `SIGPIPE` (exit code 141) errors by eliminating pipe chains.
- Fixed report URL 404: `analyze_image` now writes its `CI_JOB_ID` to `reports/.analyze_job_id`; `push_results` reads it to build the correct artifact URL.
- Added `show_if` / `check_if` fields to checklist items:
  - `show_if` — JSON Logic expression controlling item visibility.
  - `check_if` — JSON Logic expression controlling pre-checked state (`[x]` vs `[ ]`).
- `mr_description_checklist` output changed from `list[str]` to `list[{label, checked}]`.
- Updated `playbook.schema.json`, `engine.py`, `default.yaml`, and `test_playbook_engine.py` (27 tests pass).
- Updated `docs/modules/ROOT/pages/playbooks.adoc` — checklist section documents `show_if`/`check_if`.
- Updated `docs/modules/ROOT/pages/integrations/gitlab.adoc` — pipeline diagram and job descriptions reflect refactored pipeline.
- Improved documentation for CI/CD integration (moved Cookiecutter, added tips, added C4 diagrams).
- Unified linting experience by migrating to Trunk.
- Migrated documentation to Docusaurus, established dynamic versioning strategy with tag names, and cleaned up redundant folders.
- Added support for Markdown output in `regis rules list` and generated rules reference documentation.
- Refactored `generate` command into a `bootstrap` command group:
  - `bootstrap playbook` — creates a new custom playbook from the `cookiecutters/playbook` template.
  - `bootstrap archive` — bootstraps a standalone Docusaurus + Tremor archive viewer site.
  - Removed the monolithic `generate` command and the deprecated `repository` cookiecutter.
  - Updated `tests/test_bootstrap.py`.
  - Updated `docs/website/docs/reference/cli.md`.
- Added `docs/modules/ROOT/pages/commands.adoc` listing all available CLI commands.
- Updated `docs/modules/ROOT/nav.adoc` to include the new commands page.
- Consolidated bootstrapping documentation:
  - Removed obsolete `docs/modules/ROOT/pages/integrations/cookiecutter.adoc`.
  - Added `#bootstrap` anchor to `commands.adoc`.
- Updated links in `index.adoc`, `get-started.adoc`, `github.adoc`, and `gitlab.adoc` to point to the new anchor.
- Removed `cookiecutter.adoc` from `nav.adoc`.
- Migrated CI linting from Super-Linter to Trunk:
  - Enabled `mypy` and `hadolint` in Trunk.
  - Added necessary type stubs for `PyYAML`, `requests`, and `jsonschema`.
  - Replaced `github/super-linter` with `trunk-io/trunk-action` in GitHub Actions.
  - Rewrote `README.md` to focus on core features and added a comprehensive "Report Preview" section with 7 interactive carousels.
- Captured and added 7 screenshots covering all major report pages to `.github/assets/`.
- Corrected the Alpine example report URL in `README.md` to point to the versioned documentation path.
- Added `README.md` to `release-please-config.json` `extra-files` to ensure consistent versioning and updates.
- Redesign of `README.md` now properly redirects all technical documentation to the official Antora site.
- Fixed `bootstrap` command failure in Docker image:
  - Moved `cookiecutters/` directory into the `regis` package.
  - Updated `cli.py` to use `importlib.resources.files` for finding templates, ensuring compatibility with installed packages.
  - Updated `pyproject.toml` to include `cookiecutters/**/*` in package data.
- Fixed `fatal: ambiguous argument 'HEAD^2'` in Trunk Check workflow:
  - Enabled `fetch-depth: 0` for full history checkout.
  - Removed explicit `ref` override to allow Trunk's default merge-base detection on PRs.
  - Updated auto-commit step to explicitly push to the PR branch.
- Migrated Documentation from Antora to Docusaurus (located in `docs/website`).
- Relocated JSON schemas from `reference/schemas/` to `regis/schemas/` to ensure they are properly packaged.
- Added `__init__.py` files to `regis/schemas/` and subdirectories to support `importlib.resources`.
- Updated `pyproject.toml` to include the new schemas directory in package data.
- Exported JSON schemas to `docs/website/static/schemas/` for Docusaurus referencing.
- Configured Docusaurus versioning:
  - Added `stable` version for the latest tag.
  - Configured `docusaurus.config.ts` to support multiple versions.
  - Updated `release-please-config.json` to include `docs/website/versions.json`.
- Updated `docs-publish.yml` workflow to only trigger versioning for tags starting with `v`.
- Fixed lint error in `cli.py` (unused variable `exc`).
- Added **Post-install notes** feature to `bootstrap` commands:
  - CLI now reads and displays `.regis-post-install.md` from the generated project.
  - Templates for repository and playbook include personalized setup instructions (GitHub/GitLab setup, next steps).
  - Updated `commands.adoc` to document this behavior.
- Improved Docusaurus versioning:
  - Updated `.github/workflows/docs-publish.yml` to use `${{ github.ref_name }}` for dynamic versioning on tags.
  - Cleaned up redundant `version-current` files and `versions.json` entries.
- Fixed CI Warnings and Errors:
  - Added `regis/schemas/playbook/jsonlogic.schema.json` to resolve schema generation warnings.
  - Updated `docs-publish.yml` to copy all schemas to a shared static directory, fixing cross-category references.
  - Resolved `fatal: ambiguous argument 'HEAD^2'` in Trunk Check CI by refining checkout and specifying `check-mode`.
  - Suppressed `RequestsDependencyWarning` by pinning `urllib3`, `chardet`, and `charset-normalizer` in `Pipfile`.
- Added `--format` and `--output` options to `regis rules list` to support Markdown documentation generation.
- Generated `docs/website/docs/reference/rules.md` rules reference documentation using the new CLI capabilities.
- Migrated the report viewer to a modern Docusaurus-based application (located in `apps/dashboard`).
- Updated `regis/cli.py` and `regis/report/docusaurus.py` to support the new report generation flow.
- Added `--base-url` option to `regis analyze` and `evaluate` for correct asset loading in static viewers (GitLab artifacts).
- Updated the `.gitlab-ci.yml` template in the repository cookiecutter to dynamically calculate and pass the `baseUrl`.
- Removed legacy Jinja2-based HTML templates from `regis/templates/default/`.
- Updated `pnpm-workspace.yaml` and `release-please-config.json` to include the new report viewer application.
- Updated documentation site (`cli.md`, `analyze-image.md`, `gitlab.md`) with report viewer and artifact viewing details.

- Monitor CI/CD results for the new PR.
- Merge PR for `feat/dashboard-tremor`.

## Current Objective

## Recent Changes (main branch)

- **GitHub Actions Auth Unification**: All 6 workflows migrated to use `actions/create-github-app-token@v1` with `REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY` secrets.
  - **`release-please.yml`**: Replaced `secrets.RELEASE_TOKEN` (PAT) with GitHub App token.
  - **`viewer-publish.yml`** and **`docs-publish.yml`**: Changed `github_token:` to `personal_token:` for `peaceiris/actions-gh-pages` (required for non-GITHUB_TOKEN).
  - **`trunk.yml`**: Uses App token so auto-committed formatting fixes trigger downstream CI runs (GITHUB_TOKEN commits don't trigger).
  - **Motivation**: Centralized auth mechanism ensures bot-created PRs and auto-commits trigger proper CI/CD workflows.
- [2026-04-21] Migrated Memory Bank protocol to point at `docs/memory-bank/` and deprecated the root-level duplicate.
- [2026-04-22] **M002/S02 completed — Snapshot publication date**:
  - Backfilled v0.27.0/v0.26.2 snapshot dates in both JSON data files.
  - Added `--markdown` flag to `regis analyze` (no `-m` shorthand; conflicts with `--meta`).
  - New `_render_markdown()` in `report.py` follows the `elif fmt == '<ext>':` pattern.
  - 12 slice tests pass, 460 total pass. `scripts/verify_s02.py` exits 0 (7/7 checks).
  - Key decision: `-m` shorthand dropped; `_render_markdown` guards `snapshot_date` on truthiness.
- [2026-04-22] **Claude Workflows CI/CD Fixes**:
  - SHA-pinned all GitHub Actions in `claude-code-review.yml` and `claude.yml` workflows to comply with lint pipeline requirements.
  - Resolved Checkov CKV2_GHA_1 security check by adding workflow-level default permissions.
  - Fixed YAML linting issues (redundantly quoted strings).
  - All trunk checks passing. PR merged to main.
