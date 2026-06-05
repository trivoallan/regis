# PR3 — Remove the report archive feature (+ purge dashboard-viewer docs) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `--archive` feature (its sole consumer, `regis-dashboard`, is being abandoned in favour of `regis-backstage`, which does not consume the archive format) and purge the now-stale dashboard-viewer documentation.

**Architecture:** Remove the `--archive` Click option from `regis analyze` and the branches that fed the standalone dashboard, simplifying the report-output path so JSON is always produced (unless `--html` makes a self-contained report). Delete the `regis/archive/` package, the archive JSON Schema (source + published copy), the archive-only and dashboard-viewer doc pages, and prune scattered mentions. The self-contained `--html` report (`regis/report/html.py`) is independent and kept.

**Tech Stack:** Python 3.10+, Click, pytest, JSON Schema, Docusaurus.

**Spec:** `docs/superpowers/specs/2026-06-05-feature-pruning-design.md` (§4).

**Branch:** fresh branch off the latest `main`.

---

## Task 1: Remove `--archive` from `regis analyze`

**Files:**

- Modify: `regis/commands/analyze.py` (option, param, validation, output branches)
- Modify: `tests/commands/test_analyze_html.py` (delete the mutual-exclusion test)

- [ ] **Step 1: Delete the now-obsolete test first (red baseline)**

In `tests/commands/test_analyze_html.py`, delete the entire test (currently l. 97–104):

```python
def test_html_archive_mutually_exclusive(runner, tmp_path, _mock_analyze_infra):
    """--html and --archive together produce a UsageError."""
    result = runner.invoke(
        analyze,
        ["nginx:latest", "--html", "--archive", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()
```

(Match the exact body in the file; the decorator/signature shown here is illustrative — remove the whole `def test_html_archive_mutually_exclusive` function.)

- [ ] **Step 2: Run the suite to confirm it still imports (baseline green minus the deleted test)**

Run: `pipenv run pytest tests/commands/test_analyze_html.py --no-cov -q`
Expected: PASS (the remaining `--html` tests).

- [ ] **Step 3: Remove the `--archive` Click option**

In `regis/commands/analyze.py`, delete this option decorator (currently l. 259–266):

```python
@click.option(
    "--archive",
    "-A",
    "archive_dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    help="Archive directory: persist the report and update manifest.json / data.json.",
)
```

- [ ] **Step 4: Remove the `archive_dir` function parameter**

In the same file, in the `analyze` callback signature (currently l. 310), delete the line:

```python
    archive_dir: Path | None = None,
```

- [ ] **Step 5: Remove the mutual-exclusion check**

Delete (currently l. 430–431):

```python
    if html_single and archive_dir:
        raise click.UsageError("--html and --archive are mutually exclusive.")

```

- [ ] **Step 6: Simplify the `formats` initialisation**

Replace (currently l. 433–435):

```python
    formats = []
    if not archive_dir:
        formats.append("json")
```

with:

```python
    formats = ["json"]
```

- [ ] **Step 7: Simplify the report-output branch**

Replace this block (currently l. 642–658):

```python
    if archive_dir:
        from regis.archive.store import add_to_archive

        add_to_archive(final_report, archive_dir)
    else:
        render_and_save_reports(
            final_report,
            formats,
            output_template,
            output_dir_template,
            theme,
            pretty,
            sections=sections,
        )

    if not archive_dir:
        render_mr_templates(final_report, output_dir_template)
```

with:

```python
    render_and_save_reports(
        final_report,
        formats,
        output_template,
        output_dir_template,
        theme,
        pretty,
        sections=sections,
    )

    render_mr_templates(final_report, output_dir_template)
```

- [ ] **Step 8: Simplify the discoverability hint**

Replace (currently l. 660–667):

```python
    # Discoverability: the interactive viewer now ships separately. Only point to
    # it for the plain machine-report path (not --html, which is self-contained,
    # and not --archive, which feeds the standalone dashboard directly).
    if not html_single and not archive_dir:
        _info(
            "  Explore interactively: https://github.com/trivoallan/regis-dashboard",
            quiet=quiet,
        )
```

with **nothing** — delete the whole block (comment + `if` + `_info` call), since the dashboard is being abandoned.

If a discoverability hint is still desired, point to the self-contained report instead:

```python
    if not html_single:
        _info("  Tip: add --html for a self-contained report.html", quiet=quiet)
```

Pick the removal (empty) unless the maintainer prefers the `--html` tip; the spec leaves this as an editorial choice.

- [ ] **Step 9: Verify `--archive` is gone and no archive symbols remain in analyze.py**

Run: `pipenv run regis analyze --help`
Expected: no `--archive` / `-A` option.

Run: `grep -n "archive" regis/commands/analyze.py`
Expected: no matches.

- [ ] **Step 10: Run the analyze tests**

Run: `pipenv run pytest tests/commands/test_analyze_html.py tests/commands -k analyze --no-cov -q`
Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add regis/commands/analyze.py tests/commands/test_analyze_html.py
git commit -m "$(cat <<'EOF'
feat(cli)!: remove the --archive option from regis analyze

The archive format (manifest.json / data.json) was consumed only by the
standalone regis-dashboard, which is being retired in favour of the
regis-backstage plugin (the latter reads report.json and aggregates
itself). JSON output is now always produced unless --html is requested.

BREAKING CHANGE: the `--archive` / `-A` option is removed. Use `--html`
for a self-contained report, or the regis-backstage plugin for catalog
integration.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Delete the archive package, its test, and the schema

**Files:**

- Delete: `regis/archive/` (`store.py`, `__init__.py`)
- Delete: `tests/test_archive_store.py`
- Delete: `regis/schemas/archives.schema.json`
- Delete: `docs/website/static/schemas/archives.schema.json` (published copy)

- [ ] **Step 1: Confirm nothing imports the package anymore**

Run: `grep -rn "regis.archive\|add_to_archive\|archives.schema" regis/ tests/`
Expected: no matches (Task 1 removed the only importer).

- [ ] **Step 2: Delete the package, test, and schemas**

Run:

```bash
git rm -r regis/archive
git rm tests/test_archive_store.py
git rm regis/schemas/archives.schema.json docs/website/static/schemas/archives.schema.json
```

- [ ] **Step 3: Check for stray references to the published schema URL**

Run: `grep -rn "archives.schema.json" docs/ regis/ | grep -v versioned`
Expected: no matches. If a schemas index page lists it, remove that entry.

- [ ] **Step 4: Run the full suite**

Run: `pipenv run pytest --no-cov -q`
Expected: PASS, no collection errors for the deleted test.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor(schema): delete the orphaned archive package and schema

Removes regis/archive (store.py), its test, and the archives JSON Schema
(source + published copy) now that --archive is gone.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Delete archive-only and dashboard-viewer doc pages

**Files (delete):**

- `docs/website/docs/concepts/archives.md`
- `docs/website/docs/usage/multi-archive.md`
- `docs/website/docs/usage/integrations/archive-repo.md`
- `docs/website/docs/usage/integrations/archive-customize.md`
- `docs/website/docs/usage/report-viewer.md`
- `docs/website/docs/tools/viewer.mdx`

- [ ] **Step 1: Delete the pages**

Run:

```bash
git rm \
  docs/website/docs/concepts/archives.md \
  docs/website/docs/usage/multi-archive.md \
  docs/website/docs/usage/integrations/archive-repo.md \
  docs/website/docs/usage/integrations/archive-customize.md \
  docs/website/docs/usage/report-viewer.md \
  docs/website/docs/tools/viewer.mdx
```

- [ ] **Step 2: Find inbound links to the deleted pages**

Run:

```bash
grep -rn "archives\.md\|multi-archive\|archive-repo\|archive-customize\|report-viewer\|tools/viewer" docs/website/docs/ | grep -v versioned_docs
```

Expected after fix: no matches. For each hit found in a _surviving_ page, remove the link (next task also touches these files — coordinate to avoid double edits).

- [ ] **Step 3: Confirm the sidebar is autogenerated (no manual edit needed)**

Run: `find docs/website -maxdepth 2 -name "sidebars*"`
Expected: no standalone `sidebars.*` file (the sidebar is autogenerated from the folder tree, so deleting pages removes them from nav automatically). If a `sidebars.*` file _does_ exist, remove the entries for the deleted pages.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
docs(archive): remove archive and dashboard-viewer pages

Deletes the archive concept/usage/integration pages and the
dashboard-viewer redirect stubs (report-viewer.md, tools/viewer.mdx),
which pointed at the retired regis-dashboard repo.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Prune scattered archive / dashboard-viewer mentions

**Files (edit — remove archive/dashboard mentions, PRESERVE all `--html` content):**

- `docs/website/docs/usage/getting-started.md`
- `docs/website/docs/usage/analyze-image.md`
- `docs/website/docs/concepts/reports.md`
- `docs/website/docs/concepts/introduction.md`
- `docs/website/docs/usage/troubleshooting.md`
- `docs/website/docs/usage/integrations/github.md`
- `docs/website/docs/usage/integrations/gitlab.md`
- `docs/website/docs/reference/cli.md`
- `docs/website/docs/roadmap.md`
- `docs/website/docs/tags.yml`

- [ ] **Step 1: Enumerate the exact mention sites**

Run:

```bash
grep -rn "\-\-archive\|archive directory\|manifest.json\|data.json\|regis-dashboard\|report-viewer\|dashboard" \
  docs/website/docs/usage/getting-started.md \
  docs/website/docs/usage/analyze-image.md \
  docs/website/docs/concepts/reports.md \
  docs/website/docs/concepts/introduction.md \
  docs/website/docs/usage/troubleshooting.md \
  docs/website/docs/usage/integrations/github.md \
  docs/website/docs/usage/integrations/gitlab.md \
  docs/website/docs/reference/cli.md \
  docs/website/docs/roadmap.md \
  docs/website/docs/tags.yml
```

- [ ] **Step 2: Edit each hit**

For every match:

- Remove `--archive` flag descriptions, multi-archive workflow paragraphs, and links/pointers to `regis-dashboard` or the deleted pages.
- In `reference/cli.md`, delete the `--archive` row from the `regis analyze` options table.
- In `tags.yml`, remove the `dashboard` and `archives` tag definitions **only if** no surviving page still uses them (re-grep tags usage first).
- **Do NOT touch `--html` content** — the self-contained report is kept. Where a viewer pointer is removed, optionally replace it with: "Use `--html` for a self-contained `report.html`."

- [ ] **Step 3: Verify the docs are clean**

Run:

```bash
grep -rn "\-\-archive\|multi-archive\|regis-dashboard\|report-viewer\|tools/viewer" docs/website/docs/ | grep -v versioned_docs
```

Expected: no matches.

- [ ] **Step 4: Build the docs**

Run the Docusaurus build for `docs/website` and confirm it completes with **no broken-link errors**.

- [ ] **Step 5: Commit**

```bash
git add docs/website/docs
git commit -m "$(cat <<'EOF'
docs(archive): prune scattered archive and dashboard mentions

Removes --archive references and regis-dashboard pointers from guides,
the CLI reference, roadmap, and tags. Preserves all --html content.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Final verification & PR

- [ ] **Step 1: Full lint + suite with coverage**

Run: `pipenv run ruff check . && pipenv run pytest`
Expected: lint clean; suite PASS; coverage ≥ 90 %.

- [ ] **Step 2: Confirm the whole archive surface is gone**

Run: `grep -rn "archive" regis/ tests/ | grep -v "tests/test_bootstrap.py"`
Expected: no functional archive references. (`tests/test_bootstrap.py` keeps `assert "archive" not in result.output` — a valid guard that bootstrap exposes no archive subcommand; leave it.)

- [ ] **Step 3: Run trunk**

Run: `trunk check`
Expected: green (commit any auto-fixes).

- [ ] **Step 4: Open the PR**

Push the branch and open a PR titled `feat(cli)!: remove the report archive feature`. In `## Summary`, document the breaking change (`--archive` removed), the rationale (regis-dashboard retirement; regis-backstage does not consume the format), and the migration (`--html` or the Backstage plugin). Confirm Release Please bumps the minor version (pre-v1).
