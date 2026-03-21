# CLAUDE.md

## Craftsmanship

- Prefer existing, established, state-of-the-art libraries over starting from scratch.
- Prefer Python over ECMAScript languages when possible.

## Git Workflow

- Simple workflow for a small team based on feature/bug branches merged to `main` before release.
- `main` branch is protected — PRs are mandatory.

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Allowed types follow the [Angular convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type).

- **Scopes are mandatory** — extrapolate them from the architectural component modified (see list below).
- Commit description style: [Google Blockly guide](https://developers.google.com/blockly/guides/contribute/get-started/commits).
- The description should be written to be easily readable in the changelog and link to documentation when possible. Favor the functional aspect. Reserve technical details for the commit body.

### Allowed Scopes

**Core & Logic**

- `cli` — CLI, argument parsing, main console output
- `playbook` — rule evaluation engine, section parsing, `jsonLogic`, context management
- `schema` — data interfaces, structure definitions, JSON validation files
- `registry` — registry communication (HTTP, auth, manifest fetching)

**Analyzers**

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

**Rendering & Reporting**

- `report` — high-level report generation (folder creation, file writing)
- `templates` / `theme` — visual aspects, HTML, CSS, Jinja2 macros

**Tooling & CI**

- `ci` — GitHub Actions workflows
- `deps` / `build` — environment management (Pipenv, pyproject.toml, Dockerfiles)
- `docs` — Antora documentation, READMEs, Memory Bank updates

## CI/CD

- Use **GitHub Actions** and [Release Please](https://github.com/googleapis/release-please).
- GitHub project configuration as code via the [GitHub Settings App](https://github.com/apps/settings).
- [Semantic Versioning](https://semver.org/).
- [Super Linter](https://github.com/marketplace/actions/super-linter) — always check results in PRs.
- Do not manually edit Release Please PRs unless necessary.

## Python

- Styleguide: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Use [pipenv](https://pipenv.pypa.io/en/latest) for dependency management.
- Use and maintain unit tests with `pytest`.
- Use [ruff](https://github.com/astral-sh/ruff) for linting and formatting (replaces black, flake8, isort).
- Enforce type hinting for all new functions and classes.

## HTML / CSS

- Styleguide: [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)

## Diagrams

- Draw diagrams using **Mermaid**.
- Preferred format for architecture diagrams: **C4**.

## Dev Containers

- Use devcontainers where possible.

## Documentation

- Documentation as code using **Docusaurus** in the `docs/` directory.
- Short project presentation in `/README.md` with links to dive in.
- Keep documentation up to date at the root of the repository or inside `docs/`.
- Maintain the **memory bank** up to date in `docs/memory-bank/` after any significant change.
- Writing styleguide: [Google developer documentation style guide](https://developers.google.com/style)
