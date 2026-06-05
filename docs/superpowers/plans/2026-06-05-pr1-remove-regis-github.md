# PR1 — Remove the `regis github` command — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the redundant `regis github` CLI command (superseded by the extracted `trivoallan/regis-action`).

**Architecture:** Pure deletion. Drop the `github_cli` module, its CLI wiring in `regis/cli.py`, its test file, and the user-facing doc section. No replacement code — the reusable GitHub Action already posts PR comments.

**Tech Stack:** Python 3.10+, Click, pytest, Docusaurus (docs).

**Spec:** `docs/superpowers/specs/2026-06-05-feature-pruning-design.md` (§2).

**Branch:** fresh branch off the latest `main`.

---

## Task 1: Remove the command, its wiring, and its test

**Files:**

- Delete: `regis/github_cli.py`
- Modify: `regis/cli.py` (remove import line 17 and registration line 79)
- Delete: `tests/test_github_cli.py`

- [ ] **Step 1: Confirm the command currently exists (baseline)**

Run: `pipenv run regis --help`
Expected: the output lists a `github` command.

- [ ] **Step 2: Remove the CLI registration in `regis/cli.py`**

Delete this line (currently line 79):

```python
main.add_command(github_cmd, name="github")
```

And delete the import (currently line 17):

```python
from regis.github_cli import github_cmd
```

Leave `gitlab_cmd` (line 18 import, line 80 registration) untouched — `regis gitlab` is intentionally kept.

- [ ] **Step 3: Delete the module and its test**

Run:

```bash
git rm regis/github_cli.py tests/test_github_cli.py
```

- [ ] **Step 4: Verify the command is gone and nothing else imports it**

Run: `pipenv run regis --help`
Expected: no `github` command listed; `gitlab` still listed.

Run: `grep -rn "github_cli\|github_cmd\|update-pr" regis/ tests/`
Expected: no matches.

- [ ] **Step 5: Run the full test suite**

Run: `pipenv run pytest --no-cov -q`
Expected: PASS, no import errors, no collection errors for the removed test.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(cli)!: remove the regis github PR-integration command

The reusable GitHub Action (trivoallan/regis-action) already posts PR
comments and applies labels, making `regis github update-pr` redundant.

BREAKING CHANGE: the `regis github` command is removed. Use
`trivoallan/regis-action@v1` for PR integration.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Prune the documentation

**Files:**

- Modify: `docs/website/docs/usage/integrations/github.md` (remove the "Posting Results to Pull Requests" section, currently ~l. 279–319)
- Modify: `docs/website/docs/roadmap.md` (remove/adjust the feature-history line, currently l. 47)

- [ ] **Step 1: Remove the PR-posting section from `github.md`**

Open `docs/website/docs/usage/integrations/github.md`. Delete the entire `## Posting Results to Pull Requests` section, including its `### CLI reference` subsection and the two `regis github update-pr` code blocks (the section runs from the `## Posting Results to Pull Requests` heading up to — but not including — the next top-level heading `## Viewing Reports`).

If the surrounding prose implied PR comments are a core CLI feature, add one sentence pointing readers to the reusable action instead:

```markdown
PR comments are posted automatically by the reusable action
[`trivoallan/regis-action@v1`](https://github.com/trivoallan/regis-action).
```

- [ ] **Step 2: Adjust the roadmap history line**

Open `docs/website/docs/roadmap.md`. Find the line (l. 47) referencing:

> `regis github update-pr` command posts analysis results as PR comments

Either remove the row, or update the "Status/Notes" cell to read: `Moved to trivoallan/regis-action (command removed from core in vNEXT)`. Keep the historical milestone marker if the table documents past releases.

- [ ] **Step 3: Verify no dangling references in current docs**

Run: `grep -rn "regis github" docs/website/docs/ | grep -v versioned_docs`
Expected: no matches.

Note: `docs/website/versioned_docs/**` are frozen snapshots — leave them intact.

- [ ] **Step 4: Build the docs to confirm no broken links**

Run the Docusaurus build for `docs/website` (per the project's doc-build command) and confirm it completes without broken-link errors for the edited pages.

- [ ] **Step 5: Commit**

```bash
git add docs/website/docs/usage/integrations/github.md docs/website/docs/roadmap.md
git commit -m "$(cat <<'EOF'
docs(integrations): drop regis github CLI from PR-integration guide

Point readers to trivoallan/regis-action@v1 for PR comments.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Final verification & PR

- [ ] **Step 1: Run lint + full suite with coverage**

Run: `pipenv run ruff check . && pipenv run pytest`
Expected: lint clean; suite PASS; coverage ≥ 90 %.

- [ ] **Step 2: Run trunk**

Run: `trunk check`
Expected: green (commit any auto-fixes).

- [ ] **Step 3: Open the PR**

Push the branch and open a PR titled `feat(cli)!: remove the regis github command`. In the `## Summary`, note the breaking change and the migration to `trivoallan/regis-action@v1`. Confirm Release Please will bump the minor version (pre-v1, `bump-minor-pre-major`).
