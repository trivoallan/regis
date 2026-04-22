# Progress

## Completed

- Memory Bank source of truth consolidated under `docs/memory-bank/`.
- Supplemental planning history retained in `docs/memory-bank/decisionLog.md` and `docs/memory-bank/roadmap.md`.

- Core CLI functionality.
- Key analyzers (Skopeo, Trivy, Hadolint, etc.).
- Playbook evaluation with JSON logic.
- Jinja2-based HTML report generation.
- GitHub Actions workflows for release and Docker publishing.
- Docusaurus documentation structure initialized and migrated from Antora, including versioning setup.
- Relocated JSON schemas to `regis/schemas/` for better packaging.
- Fixed Skopeo architecture mismatch handling for multi-arch image indexes.
- Automated Antora documentation publishing to GitHub Pages (Legacy).
- Automated `trunk fmt` in CI with auto-commit of style changes.
- Fixed Trunk Check `HEAD^2` error by optimizing git checkout and auto-commit configuration.
- Refactored `generate` command into a `bootstrap` command group (`bootstrap playbook` and `bootstrap archive`); removed deprecated `repository` cookiecutter.
- Display post-install notes after bootstrap.
- Fixed Trunk Check `HEAD^2` error by optimizing git checkout and auto-commit configuration.
- Added post-install notes feature to `bootstrap` commands and updated documentation.

- Unified linting experience by migrating to Trunk.
- Migrated documentation to Docusaurus, established dynamic versioning strategy with tag names, and cleaned up redundant folders.
- Added support for Markdown output in `regis rules list` and generated rules reference documentation.
- **Implemented modern Docusaurus-based report viewer** (`apps/dashboard`).
- Replaced legacy Jinja2 HTML report generation with the new React/Docusaurus architecture.
- Integrated the new report viewer into the workspace (`pnpm`).
- **Added GitLab artifact support** with dynamic `baseUrl` calculation and `--base-url` flag.
- **Updated documentation** across the site to reflect the new report architecture.
- Added `bootstrap archive-repo` command: full end-to-end scaffold → remote repo creation → GitHub/GitLab Pages activation in a single command.
  - `--platform [github|gitlab]` flag skips the cookiecutter prompt via `extra_context`.
  - Robust `ARCHIVE_BASE_URL` derivation: GitLab uses `CI_PAGES_URL` (handles subgroups and custom domains); GitHub exposes `vars.ARCHIVE_BASE_URL` override.
  - Idempotent retry: if the remote repo already exists, creation is skipped and push continues.
- **Tremor UI overhaul** of the report viewer (branch: `feature/dashboard-tremor`):
  - Navbar identity badges (Registry, Repository, Tag, Digest) with clipboard copy.
  - Raw JSON link uses dynamic `siteConfig.baseUrl` (fixes broken link with non-root baseUrl).
  - Shared `StatCard` KPI component used across all 12 analyzer pages.
  - 12 individual analyzer pages in sidebar submenu (replaces monolithic Playbook page).
  - All analyzer sections homogenized: StatCards + Tremor Tables.
  - TrivySection: paginated Critical/High CVE tables sorted by most recent date.
  - Analyzer badges in rules tables link to their respective analyzer page.

## In Progress

- Keep `docs/memory-bank/` as the single source of truth for ongoing updates.
- Capture future code or workflow changes in this memory bank as they land.

## Completed (Recent)

- **M002/S02 — Snapshot publication date (2026-04-22)**:
  - Backfilled snapshot dates for v0.27.0 (→ 2026-04-09) and v0.26.2 (→ 2026-04-03) in both `regis/data/snapshot_dates.json` and `docs/website/snapshot-dates.json`.
  - Added `--markdown` flag to `regis analyze` (no `-m` shorthand — conflicts with existing `-m`/`--meta`).
  - Added `_render_markdown()` helper and `elif fmt == 'md':` branch in `regis/utils/report.py`.
  - Markdown output: image-ref header, analysis timestamp, optional `snapshot_date` line (guarded on truthiness), playbook results table.
  - 8 unit tests in `tests/commands/test_analyze_markdown.py` + structural acceptance script `scripts/verify_s02.py` (7/7 checks pass).
  - 460 total tests pass, no regressions.

- **Claude Workflows CI/CD Fixes (2026-04-22)**:
  - SHA-pinned GitHub Actions to commit SHAs (`actions/checkout` and `anthropics/claude-code-action`)
  - Added workflow-level permissions block to satisfy security checks
  - Fixed YAML linting issues
  - All trunk checks passing, PR merged to main

## Future Roadmap

- Additional analyzers (e.g., custom compliance checks).
- More HTML themes.
- Enhanced reporting features.
