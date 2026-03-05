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

## Next Steps

- Commit and open a PR with conventional commit message covering these changes.
