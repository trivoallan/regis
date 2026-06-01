# Phase 2 — Dashboard Core Removal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all dashboard/site/server/archive-scaffold code from the **core** `regis` Python package now that it lives in the standalone `regis-dashboard` repo, shipping a clean breaking `0.33` release.

**Architecture:** The core becomes "analyzer + self-contained report formats". It keeps `regis analyze --json` (the machine contract, now carrying `schemaVersion`), `regis analyze --html` (Jinja2 single-file, self-contained), and `regis analyze --archive <dir>` (writes a report into a local archive directory via `regis/archive/store.py`, consumed by the external dashboard). Everything that renders or serves the Docusaurus SPA, runs the FastAPI backend, or scaffolds the dashboard project is deleted. **Clean removal — no redirect stubs** (per decision): old invocations get Click's default error. Docs are updated in this same phase so `0.33` ships without stale references.

**Tech Stack:** Python 3.10+, Click, pytest (≥90% coverage gate), ruff, Trunk, release-please (drives the `0.32 → 0.33` bump from the breaking commit), pnpm workspace (only `docs/website` remains).

---

## Scope & boundaries

**Removed (per the design spec `docs/superpowers/specs/2026-05-31-dashboard-full-decouple-design.md`):**

- `regis/commands/dashboard.py` (the `regis dashboard` group) + `regis/server/` (FastAPI backend).
- `regis/commands/archive.py` (the `regis archive add|configure` group).
- `bootstrap archive` subcommand + `regis/cookiecutters/archive/`.
- `--site` flag + `html-site` format branch + `regis/report/docusaurus.py`.
- `[server]` optional extra (fastapi/uvicorn) + `dashboard_assets` packaging references.
- `apps/dashboard/`, `pnpm-workspace.yaml` `apps/*` glob, `cd-dashboard.yml`, the `ci-image-size.yml` `apps/dashboard/**` trigger, and the dependabot npm entry for `/apps/dashboard`.

**Retained (verified — `analyze --archive` imports `add_to_archive` from `regis.archive.store`, NOT from the removed `commands/archive.py`):**

- `regis/archive/store.py` + its tests (`tests/test_archive_store.py`) — used by `analyze --archive`.
- `regis analyze --archive <dir>`, `--html` (`regis/report/html.py`), `--json`.
- `regis bootstrap playbook`, `regis bootstrap gitlab-ci`, `regis bootstrap tools` (the `bootstrap` group stays; only its `archive` subcommand leaves).
- `regis/cookiecutters/gitlab-ci/` and `regis/cookiecutters/playbook/`.

**Out of scope:** rewriting the GitLab CI guide into the full two-tool (`analyze --json` + `regis-dashboard render`) flow — that is a forward-looking doc effort. This plan only makes the **generated** gitlab-ci template valid post-removal by switching `--site` → `--html`, and removes/redirects doc references to deleted commands.

**Decision — no redirect stubs:** removing `regis dashboard` and `--site` outright. Users invoking them post-`0.33` get Click's standard "No such command 'dashboard'" / "No such option: --site". Documented in the migration note (Task 10). This deviates from the spec's stub recommendation per explicit user choice; it also removes the only future-dated cleanup obligation, so **no `/schedule` follow-up is needed**.

## File Structure

| File                                                                                                  | Action                                                   | Task |
| ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ---- |
| `regis/commands/dashboard.py`                                                                         | **delete**                                               | 1    |
| `regis/server/**`                                                                                     | **delete** (dir)                                         | 1    |
| `tests/test_dashboard.py`, `tests/test_server_*.py`                                                   | **delete**                                               | 1    |
| `regis/cli.py`                                                                                        | modify (unregister `dashboard`, `archive`)               | 1, 2 |
| `regis/commands/archive.py`                                                                           | **delete**                                               | 2    |
| `tests/test_archive_command.py`, `tests/test_archive_configure.py`                                    | **delete**                                               | 2    |
| `regis/commands/bootstrap.py`                                                                         | modify (drop `archive` subcommand)                       | 3    |
| `regis/cookiecutters/archive/**`                                                                      | **delete** (dir)                                         | 3    |
| `tests/test_bootstrap.py`                                                                             | modify (drop archive tests)                              | 3    |
| `regis/commands/analyze.py`                                                                           | modify (drop `--site` on `analyze` + `evaluate`)         | 4    |
| `regis/utils/report.py`                                                                               | modify (drop `html-site` branch)                         | 4    |
| `regis/report/docusaurus.py`                                                                          | **delete**                                               | 4    |
| `tests/test_docusaurus.py`                                                                            | **delete**; `tests/test_cli.py` modify (`--site`)        | 4    |
| `pyproject.toml`                                                                                      | modify (server extra, deps, package-data, coverage omit) | 5    |
| `apps/dashboard/**`, `pnpm-workspace.yaml`, `cd-dashboard.yml`, `ci-image-size.yml`, `dependabot.yml` | delete/modify                                            | 6    |
| `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/.gitlab-ci.yml`                          | modify (`--site`→`--html`)                               | 7    |
| `regis/commands/analyze.py`, `tests/commands/test_analyze_*.py`                                       | modify (post-analyze message + test)                     | 8    |
| `docs/website/**`, `README.md`                                                                        | modify (remove dashboard/archive/`--site` references)    | 9    |

---

### Task 1: Remove the `regis dashboard` command + FastAPI server

**Files:**

- Delete: `regis/commands/dashboard.py`, `regis/server/` (whole dir), `tests/test_dashboard.py`, `tests/test_server_app.py`, `tests/test_server_gitlab.py`, `tests/test_server_webhooks.py`, `tests/test_server_trigger.py`
- Modify: `regis/cli.py`

- [ ] **Step 1: Delete the modules and their tests**

```bash
git rm regis/commands/dashboard.py \
       tests/test_dashboard.py \
       tests/test_server_app.py tests/test_server_gitlab.py \
       tests/test_server_webhooks.py tests/test_server_trigger.py
git rm -r regis/server
```

- [ ] **Step 2: Unregister `dashboard` in `regis/cli.py`**

Remove the import line (currently line 15):

```python
from regis.commands.dashboard import dashboard_group
```

and the registration line (currently line 91):

```python
main.add_command(dashboard_group, name="dashboard")
```

- [ ] **Step 3: Verify the CLI imports and `dashboard` is gone**

Run:

```bash
pipenv run regis --help 2>&1 | grep -c dashboard   # expect 0
pipenv run regis dashboard 2>&1 | grep -qi "No such command" && echo "OK: clean removal"
```

Expected: `0`; "OK: clean removal".

- [ ] **Step 4: Run the test suite (fast, no coverage gate)**

Run: `pipenv run pytest --no-cov -q`
Expected: PASS (no import errors; the deleted tests are gone). If any remaining test imports `regis.server` or `regis.commands.dashboard`, fix/remove that reference and re-run.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(cli)!: remove 'regis dashboard' command and FastAPI server"
```

---

### Task 2: Remove the `regis archive` command group (keep the store)

**Files:**

- Delete: `regis/commands/archive.py`, `tests/test_archive_command.py`, `tests/test_archive_configure.py`
- Modify: `regis/cli.py`
- **Keep:** `regis/archive/store.py`, `tests/test_archive_store.py` (used by `analyze --archive`).

- [ ] **Step 1: Delete the command module + its two command tests**

```bash
git rm regis/commands/archive.py \
       tests/test_archive_command.py \
       tests/test_archive_configure.py
```

- [ ] **Step 2: Unregister `archive` in `regis/cli.py`**

Remove the import line (currently line 12):

```python
from regis.commands.archive import archive
```

and the registration line (currently line 87):

```python
main.add_command(archive)
```

- [ ] **Step 3: Confirm the store is still wired to `analyze --archive`**

Run:

```bash
grep -n "from regis.archive.store import add_to_archive" regis/commands/analyze.py   # expect 1 hit
pipenv run regis archive 2>&1 | grep -qi "No such command" && echo "OK: archive group gone"
```

Expected: one grep hit (the retained import in `analyze.py`); "OK: archive group gone".

- [ ] **Step 4: Run the store tests + full fast suite**

Run: `pipenv run pytest --no-cov -q tests/test_archive_store.py` then `pipenv run pytest --no-cov -q`
Expected: store tests PASS (store retained); full suite PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(cli)!: remove 'regis archive' add/configure commands (store retained for --archive)"
```

---

### Task 3: Remove `bootstrap archive` + the archive cookiecutter

**Files:**

- Modify: `regis/commands/bootstrap.py` (delete the `@bootstrap.command(name="archive")` block — the `bootstrap_archive` function and its decorator, currently spanning ~line 178 to the start of the next command/`bootstrap_tools` at ~line 466; delete exactly that command and nothing else)
- Delete: `regis/cookiecutters/archive/` (whole dir)
- Modify: `tests/test_bootstrap.py` (remove the `bootstrap archive` tests)

- [ ] **Step 1: Delete the archive cookiecutter template**

```bash
git rm -r regis/cookiecutters/archive
```

- [ ] **Step 2: Delete the `bootstrap archive` command from `regis/commands/bootstrap.py`**

Remove the entire `@bootstrap.command(name="archive")` decorator + `def bootstrap_archive(...)` function body (the block that contains `template_path = resources.files("regis") / "cookiecutters" / "archive"`). Leave `bootstrap_playbook`, `bootstrap_gitlab_ci`, and `bootstrap_tools` intact. After the edit, confirm no dangling references:

```bash
grep -n "cookiecutters.*archive\|bootstrap_archive\|name=\"archive\"" regis/commands/bootstrap.py || echo "OK: no archive refs left"
```

Expected: "OK: no archive refs left".

- [ ] **Step 3: Remove the `bootstrap archive` tests**

In `tests/test_bootstrap.py`, delete the archive-specific tests (e.g. `test_bootstrap_archive_success`, `test_bootstrap_archive_dev_and_repo_mutually_exclusive`, and any other test invoking `bootstrap archive`). Keep the playbook / gitlab-ci / tools tests. Verify nothing references the removed command:

```bash
grep -n "bootstrap.*archive\|\"archive\"" tests/test_bootstrap.py || echo "OK: no archive tests left"
```

Expected: "OK: no archive tests left".

- [ ] **Step 4: Verify `bootstrap` still works without `archive`**

Run:

```bash
pipenv run regis bootstrap --help 2>&1 | grep -E "playbook|gitlab-ci|tools"   # the three retained subcommands
pipenv run regis bootstrap archive 2>&1 | grep -qi "No such command" && echo "OK: bootstrap archive gone"
pipenv run pytest --no-cov -q tests/test_bootstrap.py
```

Expected: the three subcommands listed; "OK: bootstrap archive gone"; bootstrap tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(cli)!: remove 'bootstrap archive' subcommand and archive cookiecutter"
```

---

### Task 4: Remove `--site` / `html-site` + the Docusaurus renderer

**Files:**

- Modify: `regis/commands/analyze.py` (drop `--site` on both the `analyze` and `evaluate` commands)
- Modify: `regis/utils/report.py` (drop the `html-site` branch)
- Delete: `regis/report/docusaurus.py`, `tests/test_docusaurus.py`
- Modify: `tests/test_cli.py` (remove the `--site` test)

- [ ] **Step 1: Delete the renderer and its tests**

```bash
git rm regis/report/docusaurus.py tests/test_docusaurus.py
```

- [ ] **Step 2: Remove the `--site` option from `analyze` (≈ line 203) and `evaluate` (≈ line 739) in `regis/commands/analyze.py`**

Delete both `--site` `click.option(...)` blocks and the corresponding `site` parameter in each function signature (around lines 320 and 789). Then delete the `if site: formats.append("html-site")` lines (≈ 459 and 812) and the now-stale `site` references in the mutual-exclusivity / warning lines. The mutual-exclusivity check at line 452-453 must become `--html`-only:

```python
# before:  if (site or html_single) and archive_dir:
#              raise click.UsageError("--site/--html and --archive are mutually exclusive.")
if html_single and archive_dir:
    raise click.UsageError("--html and --archive are mutually exclusive.")
```

Apply the equivalent edit in the `evaluate` command. After editing, confirm no `site` / `html-site` tokens remain in the file:

```bash
grep -n -E "\-\-site|html-site|[^a-z]site[^a-z=]" regis/commands/analyze.py || echo "OK: no site refs"
```

Expected: "OK: no site refs" (or only unrelated substrings like "website" — eyeball any hit).

- [ ] **Step 3: Remove the `html-site` branch from `regis/utils/report.py`**

Delete the `if fmt == "html-site":` block (≈ line 342-359, the branch that does `from regis.report.docusaurus import build_report_site` and calls it). Also fix the guard at ≈ line 170 (`if "html-site" not in formats or len(formats) > 1:`) — re-derive it without `html-site` (the surrounding logic decides when to also write `report.json`; preserve that intent for the remaining `json`/`html`/`md` formats). Confirm:

```bash
grep -n -E "html-site|docusaurus|build_report_site" regis/utils/report.py || echo "OK: no html-site refs"
```

Expected: "OK: no html-site refs".

- [ ] **Step 4: Remove the `--site` test from `tests/test_cli.py`**

Delete the test that invokes `analyze ... --site`. Keep `--html` / `--json` tests.

- [ ] **Step 5: Verify `--html` and `--json` still work; full fast suite**

Run:

```bash
pipenv run regis analyze --help 2>&1 | grep -c -- "--site"     # expect 0
pipenv run regis analyze --help 2>&1 | grep -E -- "--html|--json|--archive"   # all present
pipenv run pytest --no-cov -q
```

Expected: `0` for `--site`; `--html`/`--json`/`--archive` present; suite PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(report)!: remove --site flag, html-site format, and Docusaurus renderer"
```

---

### Task 5: Strip dashboard/server from packaging (`pyproject.toml`)

**Files:**

- Modify: `pyproject.toml`

- [ ] **Step 1: Remove the `[server]` extra and its deps from `dev`**

In `[project.optional-dependencies]`, delete the line `server = ["fastapi>=0.115.0", "uvicorn[standard]>=0.34"]` (line 47), and remove `"fastapi>=0.115.0"` + `"uvicorn[standard]>=0.34"` from the `dev = [ ... ]` list (lines 54-55).

- [ ] **Step 2: Remove `dashboard_assets` packaging + coverage references**

In `[tool.setuptools.package-data]`, delete `"dashboard_assets/**/*"` (line 67) — keep `"cookiecutters/**/*"` (the gitlab-ci and playbook cookiecutters still ship). In `[tool.coverage.report]` `omit`, change line 83 from `omit = ["regis/cookiecutters/*", "regis/dashboard_assets/*"]` to `omit = ["regis/cookiecutters/*"]`.

- [ ] **Step 3: Verify the project still builds + installs cleanly**

Run:

```bash
grep -n -E "fastapi|uvicorn|dashboard_assets|server =" pyproject.toml || echo "OK: no server/dashboard packaging refs"
pipenv install --dev 2>&1 | tail -3
pipenv run regis --help >/dev/null 2>&1 && echo "OK: CLI loads after dep change"
```

Expected: "OK: no server/dashboard packaging refs"; install succeeds; "OK: CLI loads after dep change".

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml Pipfile.lock 2>/dev/null; git add pyproject.toml
git commit -m "build!: drop [server] extra (fastapi/uvicorn) and dashboard_assets packaging"
```

---

### Task 6: Remove the dashboard app + its repo plumbing

**Files:**

- Delete: `apps/dashboard/` (whole dir), `.github/workflows/cd-dashboard.yml`
- Modify: `pnpm-workspace.yaml`, `.github/workflows/ci-image-size.yml`, `.github/dependabot.yml`

- [ ] **Step 1: Delete the app and its publish workflow**

```bash
git rm -r apps/dashboard
git rm .github/workflows/cd-dashboard.yml
```

- [ ] **Step 2: Update `pnpm-workspace.yaml`** — drop the `apps/*` glob (the dashboard was the only app; `docs/website` remains):

```yaml
packages:
  - docs/website
```

- [ ] **Step 3: Remove the `apps/dashboard/**`trigger from`.github/workflows/ci-image-size.yml`\*\*

Delete the `- apps/dashboard/**` line (line 14) from the `paths:` list. If that leaves `paths:` referencing only unrelated entries, keep them; if it empties the list, leave the remaining real entries intact (do not delete `paths:` wholesale).

- [ ] **Step 4: Remove the dashboard npm entry from `.github/dependabot.yml`**

Delete the `npm` update block whose `directory: /apps/dashboard` (lines ≈ 9-19, the whole `- package-ecosystem: npm` entry for that directory). Keep the `/docs/website` npm entry and the others.

- [ ] **Step 5: Verify no lingering references**

Run:

```bash
grep -rn "apps/dashboard" .github/ pnpm-workspace.yaml || echo "OK: no apps/dashboard refs"
test ! -d apps/dashboard && echo "OK: apps/dashboard gone"
```

Expected: "OK: no apps/dashboard refs"; "OK: apps/dashboard gone".

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "ci!: remove apps/dashboard, cd-dashboard workflow, and its CI/dependabot wiring"
```

---

### Task 7: Keep the generated GitLab CI template valid (`--site` → `--html`)

**Files:**

- Modify: `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/.gitlab-ci.yml`
- Modify (if it asserts on `--site`): `tests/test_bootstrap_gitlab_ci.py`

- [ ] **Step 1: Switch the generated pipeline from `--site` to `--html`**

In the template, replace the `--site` invocation (≈ line 55) so the generated pipeline produces a self-contained single-file report instead of a Docusaurus site. Remove the now-irrelevant `--base-url` line (only `--site` consumed it) and the `REPORT_BASE_URL` export above it:

```yaml
regis analyze "$IMAGE_URL" \
--playbook playbook.yaml \
--html \
--output-dir reports \
--meta "trigger.user=$GITLAB_USER_LOGIN" \
--meta "trigger.url=$CI_JOB_URL" \
--meta "gitlab.mr_url=$CI_MERGE_REQUEST_PROJECT_URL/-/merge_requests/$CI_MERGE_REQUEST_IID"
```

(If later jobs in the template publish a `report/` Pages site from the `--site` output, repoint them at the `report.html` artifact. Read the rest of the template and adjust the artifact paths accordingly.)

- [ ] **Step 2: Update the gitlab-ci bootstrap test if it asserts `--site`**

```bash
grep -n -- "--site\|base-url\|REPORT_BASE_URL" tests/test_bootstrap_gitlab_ci.py
```

If hits, update the assertions to expect `--html` and the absence of `--site`/`--base-url`.

- [ ] **Step 3: Verify a scaffold renders a valid pipeline**

Run:

```bash
grep -rn -- "--site" regis/cookiecutters/ || echo "OK: no --site in cookiecutters"
pipenv run pytest --no-cov -q tests/test_bootstrap_gitlab_ci.py
```

Expected: "OK: no --site in cookiecutters"; the gitlab-ci bootstrap test PASS.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "fix(templates): generated gitlab-ci uses --html (single-file) instead of removed --site"
```

---

### Task 8: Add the post-analyze discoverability message (TDD)

**Files:**

- Modify: `regis/commands/analyze.py`
- Test: `tests/commands/test_analyze_html.py` (or the closest existing analyze-command test module — add a new test there)

When `analyze` writes a machine `report.json` (i.e. `--json`/default, **not** when `--html` is used and not when `--archive` is used), print a one-time pointer to the standalone dashboard, so interactive exploration is still discoverable.

- [ ] **Step 1: Write the failing test**

Add to `tests/commands/test_analyze_html.py`:

```python
def test_analyze_prints_dashboard_pointer_for_json(monkeypatch, tmp_path):
    """A plain (json) analyze run points the user at regis-dashboard; --html does not."""
    from click.testing import CliRunner
    from regis.cli import main

    # Stub the analysis so the command runs offline and writes a report.json.
    # (Reuse the module's existing analyze-stubbing fixture/pattern; this test only
    #  asserts on the trailing discoverability line, not on analyzer behavior.)
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["analyze", "alpine:3.20", "--output-dir", str(tmp_path)],
        catch_exceptions=False,
    )
    assert "regis-dashboard" in result.output
    assert "github.com/trivoallan/regis-dashboard" in result.output
```

> When implementing, wire this test to the module's existing offline-analyze stubbing (the same patch targets the other `test_analyze_*` tests use — patch `regis.commands.analyze.RegistryClient` and `regis.commands.analyze._discover_analyzers`). If the existing module already has a fixture that runs `analyze` offline and writes a report, build the assertion on top of that fixture instead of re-stubbing.

- [ ] **Step 2: Run to verify it fails**

Run: `pipenv run pytest --no-cov -q tests/commands/test_analyze_html.py -k dashboard_pointer`
Expected: FAIL — the pointer line is not printed yet.

- [ ] **Step 3: Implement the message**

In `regis/commands/analyze.py`, after the report is written (the block around line 666-690 where `--json` output / `--archive` is handled), add — gated so it only prints for the machine-report path and is silenced by `-q`:

```python
# Discoverability: the interactive viewer now ships separately.
if not html_single and not archive_dir:
    _info(
        "  Explore interactively: https://github.com/trivoallan/regis-dashboard",
        quiet=quiet,
    )
```

(Use the same `_info(..., quiet=quiet)` helper the command already uses for progress lines, so `-q` suppresses it. Place it after the success/“report written” line.)

- [ ] **Step 4: Run to verify pass**

Run: `pipenv run pytest --no-cov -q tests/commands/test_analyze_html.py -k dashboard_pointer`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/commands/analyze.py tests/commands/test_analyze_html.py
git commit -m "feat(cli): point to regis-dashboard after a machine-report analyze run"
```

---

### Task 9: Docs sweep — remove references to deleted commands

**Files (from the recon inventory):** `docs/website/docs/reference/cli.md`, `docs/website/docs/concepts/archives.md`, `docs/website/docs/concepts/reports.md`, `docs/website/docs/usage/report-viewer.md`, `docs/website/docs/usage/multi-archive.md`, `docs/website/docs/usage/integrations/archive-customize.md`, `docs/website/docs/usage/integrations/archive-repo.md`, `docs/website/docs/usage/integrations/github.md`, `docs/website/docs/usage/integrations/gitlab.md`, `docs/website/docs/usage/getting-started.md`, `docs/website/docs/usage/analyze-image.md`, `docs/website/docs/usage/custom-playbook.md`, `docs/website/docs/usage/troubleshooting.md`, `docs/website/docs/concepts/playbooks.md`, `docs/website/docs/reference/playbooks/default/examples/*.md`, `README.md`

- [ ] **Step 1: Inventory the exact references**

```bash
grep -rln -E "regis dashboard|regis archive|bootstrap archive|--site|report-viewer|html-site" docs/website README.md
```

Work the resulting list. For each file, apply one of:

- **Removed command/flag mention** (`regis dashboard`, `regis archive add|configure`, `bootstrap archive`, `--site`) → delete the line/section, or rewrite to the retained path (`regis analyze --html` for self-contained, `regis analyze --json` + a link to `https://github.com/trivoallan/regis-dashboard` for interactive).
- **Whole page about the removed feature** (e.g. `report-viewer.md`, `archive-customize.md`, `archive-repo.md`, `multi-archive.md`) → replace its body with a short "moved to regis-dashboard" stub linking the new repo, OR remove the page and its sidebar entry. If you remove a page, also remove its reference in `docs/website/sidebars.*` and any in-doc links to it (the Docs Link Check CI will fail on dangling links).

- [ ] **Step 2: Update `README.md`** — replace the `regis bootstrap archive --repo` mention with the retained flow (`regis analyze --html` / link to `regis-dashboard`).

- [ ] **Step 3: Verify no dangling references or links**

```bash
grep -rn -E "regis dashboard|regis archive|bootstrap archive|--site" docs/website README.md || echo "OK: no removed-command refs"
pnpm --filter @regis/docs... build 2>/dev/null || (cd docs/website && pnpm install && pnpm build) 2>&1 | tail -5
```

Expected: "OK: no removed-command refs"; the docs site builds (no broken-link failures). (Use whatever the repo's docs build command is — check `docs/website/package.json` scripts.)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "docs!: drop dashboard/archive/--site references from the doc site and README"
```

---

### Task 10: Full verification + migration note + PR

**Files:** none new (verification, changelog/migration prose lives in the PR body + a migration doc if the repo has one)

- [ ] **Step 1: Full suite with the coverage gate**

Run: `pipenv run pytest`
Expected: PASS with coverage **≥ 90%** (the gate). Removing tested code can move the ratio either way — if coverage dipped below 90%, add focused tests for retained-but-now-undertested paths (e.g. `analyze --archive`, `--html`) rather than lowering the gate.

- [ ] **Step 2: Lint + format + Trunk**

Run:

```bash
pipenv run ruff check . && pipenv run ruff format --check .
trunk check --no-fix 2>&1 | tail -20
```

Expected: ruff clean; Trunk reports no new issues (commit any Trunk auto-fmt changes).

- [ ] **Step 3: Smoke the retained surface end to end**

```bash
pipenv run regis --help                 # no dashboard/archive group; bootstrap/analyze present
pipenv run regis analyze --help | grep -E -- "--html|--json|--archive"   # retained flags
pipenv run regis bootstrap --help | grep -E "playbook|gitlab-ci|tools"   # retained subcommands
```

Expected: as annotated.

- [ ] **Step 4: Branch + push + open the PR**

The breaking commits (`feat(cli)!`, `feat(report)!`, `build!`, `ci!`) drive release-please to bump `0.32 → 0.33`. Do **not** hand-edit the version in `pyproject.toml`/manifest — release-please owns it.

```bash
git push -u origin <feature-branch>
gh pr create --base main --title "feat!: remove dashboard/site/server from the core (Phase 2)" --body "<summary + migration>"
```

PR body must include a **Migration** section:

```markdown
## Migration (0.32 → 0.33, breaking)

- `regis dashboard …`, `regis archive add|configure`, `regis bootstrap archive`, and
  `regis analyze --site` are **removed**. Interactive viewing now lives in
  https://github.com/trivoallan/regis-dashboard (`regis-dashboard render|serve|archive|bootstrap`).
- Retained in the core: `regis analyze --json` (machine contract, carries `schemaVersion`),
  `regis analyze --html` (self-contained single file), `regis analyze --archive <dir>`
  (writes archive data the standalone dashboard consumes).
- The `[server]` extra (FastAPI/uvicorn) is gone.
```

- [ ] **Step 5: Verify CI green on the PR**

Run: `gh pr checks --watch` (pytest, Trunk, pip-audit, CodeQL, Docs Link Check). Fix any failures before requesting merge.

---

## Self-review notes (reconciled against the spec)

- **Spec "Removed from the core" list** → Tasks 1 (`dashboard.py` + `server/`), 2 (`archive.py`), 3 (`bootstrap archive` + `cookiecutters/archive`), 4 (`--site` + `html-site` + `docusaurus.py`), 5 (`[server]` + `dashboard_assets`), 6 (`apps/dashboard`, `cd-dashboard.yml`, workspace).
- **Spec "Retained (visualization)" (`--html`, `--json`)** → preserved and explicitly smoke-tested in Tasks 4 & 10. `analyze --archive` + `regis/archive/store.py` retained (dependency verified: `analyze.py` imports the store directly, not the removed command).
- **Spec "post-analyze discoverability message"** → Task 8 (kept; it is not a stub).
- **Decision: no redirect stubs** → honored (clean removal); removes the spec's only future-dated obligation, so no `/schedule`.
- **Decision: docs in Phase 2** → Task 9 (the spec put docs in Phase 3; pulled forward per user choice).
- **Spec "bump 0.32 → 0.33 with changelog + migration"** → Task 10 (release-please-driven; migration in PR body).
- **Extra (not in spec): gitlab-ci cookiecutter `--site`** → Task 7 keeps the retained template valid.
- **Spec "core coverage ≥ 90% after removal"** → Task 10 Step 1 guards it.

## Risks / watch-points

- **Coverage ratio**: deleting ~10 test files removes both code and its tests; the 90% gate can move either way. Task 10 Step 1 is the gate; add focused tests for `--archive`/`--html` if it dips.
- **`report.py` shared guard (line ~170)**: that conditional currently special-cases `html-site`. Re-deriving it without `html-site` must not change behavior for `json`/`html`/`md`. Eyeball the surrounding `write_report` logic when editing Step 4.3.
- **Docs link breakage**: removing a whole doc page requires also removing its sidebar entry and inbound links, or the Docusaurus build / Docs Link Check fails (Task 9 Step 3 guards this).
- **`evaluate` mirrors `analyze`**: every `--site` edit in `analyze` has a twin in the `evaluate` command (≈ line 739+). Don't fix only one.
- **gitlab-ci template downstream jobs**: if the template's later stages publish a Pages site from `--site` output, switching to `--html` requires repointing those artifact paths (Task 7 Step 1 note).
