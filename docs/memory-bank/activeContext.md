# Active Context

## Current Objective

Documentation update following the pipeline refactoring and checklist enhancement.

## Recent Changes

- Refactored `.gitlab-ci.yml` (consumer cookiecutter): split monolithic `analyze_image` into four independent jobs:
  - `analyze_image` — runs `regis-cli analyze`, produces `reports/` artifacts.
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
- Refactored `generate` command into a `bootstrap` command group:
  - `bootstrap repository` — recreates the project repository from renamed `cookiecutters/repository` template.
  - `bootstrap playbook` — creates a new custom playbook from the newly added `cookiecutters/playbook` template.
  - Removed the monolithic `generate` command.
  - Updated `tests/test_bootstrap.py` (3 tests pass).
  - Updated `get-started.adoc` and `cookiecutter.adoc` documentation.
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
- Added OCI-compliant labels to `Dockerfile` for better GitHub Packages integration (`source`, `description`, `licenses`).

## Next Steps

- Push the changes and open a PR.
