# regis — Project Overview

**Purpose**: CLI tool for analyzing Docker images and generating security/quality reports. Pluggable analyzer architecture with a playbook evaluation engine.

**Tech stack**: Python (pipenv), Ruff (lint/format), pytest, Trunk (CI linter orchestrator), Docusaurus (docs), GitHub Actions (CI/CD), Release Please (releases).

**Key architecture**:

- `regis/cli.py` — main entrypoint
- `regis/analyzers/` — pluggable analyzers (entry-points in pyproject.toml)
- `regis/commands/` — CLI commands (analyze, archive, bootstrap, check, rules)
- `regis/playbook/` — playbook evaluation engine
- `regis/rules/` — JSON Logic rule evaluation
- `regis/registry/` — registry client
- `regis/report/` — report generation (Docusaurus SPA)
- `docs/memory-bank/` — cross-session memory bank (ALWAYS read at session start)

**Style**: Google Python Style Guide, type hints required, ruff for formatting.

**CI/CD**: GitHub Actions with GitHub App token auth (`REGIS_CI_APP_ID` + `REGIS_CI_APP_PRIVATE_KEY`). All workflows use `actions/create-github-app-token` with `client-id` input.
