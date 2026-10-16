# regis — Project Overview

**Purpose**: CLI tool for analyzing container images and generating security/quality reports. Pluggable analyzer architecture with a playbook evaluation engine.

**Tech stack**: Python (uv), Ruff (lint/format), mypy, import-linter, pytest, `make` (common CI contract), GitHub Actions (CI socle shared with `knock` and `uske`), Release Please (releases). Documentation is plain Markdown in `docs/`, read on GitHub.

**Key architecture** (hexagonal, ports & adapters — see `CLAUDE.md` § Architecture):

- `regis/core/` — Click-free core: `model/`, `ports/`, `domain/` (analyzers, playbook engine, JSON Logic rules), `application/` (use-cases)
- `regis/adapters/driven/` — registry client, tool runner, report sinks and renderers
- `regis/adapters/driving/cli/` — `regis` console script and commands
- `regis/schemas/` — JSON Schemas; `regis/playbooks/default/` — built-in playbook
- `docs/memory-bank/` — cross-session memory bank (ALWAYS read at session start)

**Style**: Google Python Style Guide, type hints required, ruff for formatting.

**CI/CD**: the common socle (`ci`, `pr-title`, `release`, `renovate`, `settings`, `socle-drift`) plus `extra-*.yml` workflows. Workflows that write use the `oci-ci-ttc` GitHub App through `actions/create-github-app-token` (`client-id: ${{ secrets.CI_APP_CLIENT_ID }}`, `CI_APP_PRIVATE_KEY`). Repository settings live in `.github/settings.json`.
