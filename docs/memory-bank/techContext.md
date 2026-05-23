# Technical Context

## Tech Stack

### Core (Python)

- Python 3.10+
- `click` — CLI framework
- `requests` — HTTP client
- `jsonschema` — JSON Schema validation
- `semver` — semantic version parsing
- `json-logic-qubit` — JSON Logic rule evaluation
- `pyyaml` — YAML parsing
- `jinja2` — templating (HTML reports)
- `cookiecutter` — project scaffolding
- `python-gitlab` — GitLab API client
- `fastapi` + `uvicorn` — local dev server

### Dashboard / Docs (Node)

- Docusaurus — documentation site + dashboard app (`apps/dashboard`)
- Tailwind CSS — styling in the dashboard
- pnpm workspaces — monorepo Node toolchain

### State & Data

- JSON Schema validation
- JSON Logic rule evaluation
- Schema-driven analyzer and report payloads

### Testing

- `pytest` + `pytest-cov`
- `responses` — HTTP mocking
- `httpx` — async HTTP client in tests

### Dev Tools

- `ruff` — linting and formatting
- `trunk` — linter/formatter orchestrator (local + CI)
- `pipenv` — Python dependency management
- `setuptools-scm` — version from git tags

## External Binaries Required

These must be in `PATH` for the relevant analyzers to work:

| Binary     | Analyzer              |
| ---------- | --------------------- |
| `trivy`    | `analyzer/trivy`      |
| `skopeo`   | `analyzer/skopeo`     |
| `hadolint` | `analyzer/hadolint`   |
| `dockle`   | (image best-practice) |

## Development Environment

### Prerequisites

- Python 3.10+
- `pipenv`
- Node.js + pnpm (for docs/dashboard work)

### Setup Commands

```bash
# Python deps
pipenv install --dev

# CLI locally
pipenv run regis --help

# Tests
pipenv run pytest
pipenv run pytest --no-cov

# Lint / format
pipenv run ruff check .
pipenv run ruff format .
trunk check
trunk check --fix

# Dashboard dev server
pnpm --filter @regis/dashboard dev

# Build all Node packages
pnpm run build
```

## Project Structure

```text
project-root/
├── regis/            # Python package (CLI, analyzers, playbook engine, report)
│   ├── analyzers/
│   ├── commands/
│   ├── playbook/
│   ├── rules/
│   ├── registry/
│   ├── report/
│   ├── schemas/
│   └── templates/
├── apps/
│   └── dashboard/    # React/Docusaurus report viewer
├── docs/
│   ├── website/      # Docusaurus documentation site
│   └── memory-bank/  # Agent context (this directory)
├── scripts/          # Utility scripts
├── tests/            # pytest test suite
└── cookiecutters/    # Project scaffolding templates (bundled in package)
```

## Build & Deploy

- GitHub Actions workflows in `.github/workflows/`
- Release Please — automated changelog and releases
- `cd-docker.yml` — CycloneDX/SPDX SBOM generation + provenance attestation
- Docusaurus docs + dashboard deployed to GitHub Pages
- All workflows use GitHub App token (`REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY`) — never bare `GITHUB_TOKEN` for checkouts that must trigger downstream CI
