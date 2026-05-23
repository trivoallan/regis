# System Patterns

## Architecture

`regis` follows a modular, pluggable architecture.

### Key Components

- **CLI (Click)**: Entry point for user interaction.
- **Engine**: Orchestrates analysis and playbook evaluation.
- **Analyzers**: Pluggable modules that extract specific data (e.g., Skopeo, Trivy, Hadolint).
- **Playbook Engine**: Evaluates JSON logic rules against analyzer results.
- **Report Generators**: Produces interactive SPA dashboards and machine-readable JSON.

## Report Output Format Extension Pattern

New report output formats in `regis/utils/report.py` follow the `elif fmt == '<ext>':` pattern in `render_and_save_reports()`, delegating to a dedicated `_render_<fmt>()` helper.

Adding a format requires:

1. New `_render_<fmt>()` helper function in `report.py`
2. `elif fmt == '<ext>':` branch in `render_and_save_reports()`
3. CLI flag in `analyze.py` wired into both the main analysis path and the `--rerun` path

**Gotcha**: The `-m` shorthand is already taken by `--meta` in `regis analyze`. When adding new short flags to `analyze.py`, check existing shorthands first. `--markdown` has no short flag for this reason.

## Rules and Standards

- **Python**: Use `pipenv` for dependency management.
- **CI/CD**: GitHub Actions with Release Please and Trunk (see CI/CD Gotchas below for full details).
- **Documentation**: Docusaurus for documentation as code.
- **Aesthetics**: High priority on visual excellence for HTML reports.

## CI/CD Gotchas

- **`ci-test.yml`** includes `pip-audit` and enforces a HIGH/CRITICAL severity gate via `scripts/enforce_pip_audit_severity.py` (severity is resolved from OSV metadata).
- **`cd-docker.yml`** emits CycloneDX/SPDX SBOM artifacts and provenance attestations via `actions/attest-build-provenance`.
- **GitHub App authentication**: All workflows use `actions/create-github-app-token@v1` with `REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY`. Never use `GITHUB_TOKEN` for checkouts that need to trigger downstream CI runs — it won't.
- **`peaceiris/actions-gh-pages`** with the App token requires `personal_token:`, not `github_token:`.
- **Trunk auto-fmt in CI**: the trunk workflow commits formatting fixes via `stefanzweifel/git-auto-commit-action`. The checkout must use the App token so the commit triggers a new workflow run.
- **Trunk pre-commit**: locally, `trunk-check-fix-pre-commit` runs `trunk check --fix` on `git commit`. Commit the auto-fixed files it produces.
- **Dependabot PRs + secrets**: workflows triggered by Dependabot via `pull_request` run with read-only `GITHUB_TOKEN` and no secrets. Use `pull_request_target` for any workflow that must act on Dependabot PRs (safe when no PR code is checked out).
- **Release Please PRs** are labelled `autorelease: pending`. Exclude them from auto-merge with `!contains(github.event.pull_request.labels.*.name, 'autorelease: pending')`. Don't manually edit Release Please PRs unless necessary.
- **Auto-rebase + squash merge no-op**: if a fix branch is auto-rebased after `main` already contains the same change, the squash merge becomes a no-op. Always branch from the latest `main` immediately before committing.
- **mypy** is excluded for `tests/**` (crashes on Linux CI with stale cache on `http.server`).

## Commit Scopes (mandatory)

Extrapolate the scope from the architectural component modified.

### Core & Logic

- `cli` — CLI, argument parsing, main console output
- `playbook` — rule evaluation engine, section parsing, `jsonLogic`, context management
- `schema` — data interfaces, structure definitions, JSON validation files
- `registry` — registry communication (HTTP, auth, manifest fetching)

### Analyzers

- `analyzer` — base analyzer class or shared analyzer interfaces
- `analyzer/trivy` — vulnerability scanning and SBOM generation via Trivy
- `analyzer/sbom` — SBOM analysis and CycloneDX/SPDX generation
- `analyzer/hadolint` — Dockerfile linting
- `analyzer/skopeo` — base metadata extraction
- `analyzer/freshness` — image age and freshness score
- `analyzer/size` — size and layer calculations
- `analyzer/popularity` — registry popularity metrics
- `analyzer/endoflife` — version support status
- `analyzer/scorecarddev` — OpenSSF Scorecard checks
- `analyzer/provenance` — provenance and supply chain evidence

### Rendering & Reporting

- `report` — high-level report generation (folder creation, file writing)
- `templates` / `theme` — visual aspects, HTML, CSS, React/Docusaurus SPA

### Tooling & CI

- `ci` — GitHub Actions workflows
- `deps` / `build` — environment management (Pipenv, pyproject.toml, Dockerfiles)
- `docs` — Docusaurus documentation, READMEs, Memory Bank updates
