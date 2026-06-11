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
- `uv` — Python dependency management (lockfile: `uv.lock`, dev deps in PEP 735 `[dependency-groups]`)
- Renovate (Mend hosted app) — dependency updates across the constellation, driven by the shared `renovate-constellation.json5` preset (replaces Dependabot + manual `pinact` runs).
- `setuptools-scm` — version from git tags

## External Binaries Required

These must be in `PATH` for the relevant analyzers to work:

| Binary       | Analyzer slug | Module                        |
| ------------ | ------------- | ----------------------------- |
| `grype`      | `cve`         | `regis/analyzers/cve.py`      |
| `trufflehog` | `secrets`     | `regis/analyzers/secrets.py`  |
| `syft`       | `sbom`        | `regis/analyzers/sbom.py`     |
| `regctl`     | `oci`         | `regis/analyzers/oci.py`      |
| `hadolint`   | `hadolint`    | `regis/analyzers/hadolint.py` |
| `dockle`     | `dockle`      | `regis/analyzers/dockle.py`   |

## Development Environment

### Prerequisites

- Python 3.10+
- `uv`
- Node.js + pnpm (for docs site work)

### Setup Commands

```bash
# Python deps
uv sync

# CLI locally
uv run regis --help

# Tests
uv run pytest
uv run pytest --no-cov

# Lint / format
uv run ruff check .
uv run ruff format .
trunk check
trunk check --fix

# Docs site dev server
pnpm --filter docs start

# Build the docs site (run from docs/website, as CI does)
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
- Workflows that push or trigger downstream CI use the GitHub App token (`REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY`); read-only jobs may use the default `GITHUB_TOKEN`
