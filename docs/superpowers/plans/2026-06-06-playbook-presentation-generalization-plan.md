# Playbook Presentation Generalization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the playbook's GitLab-specific `spec.integrations.gitlab` into a platform-neutral `spec.presentation` section, rename the GitLab-flavoured `report.json` output fields (`mr_*`) to neutral names, and bump `REPORT_SCHEMA_VERSION` — so the core no longer knows any platform.

**Architecture:** The resolution logic is already generic; this is mostly a rename + relocation. The playbook schema gains `spec.presentation` (badges/checklists/templates) and loses `spec.integrations`. `playbook/integrations/gitlab.py` becomes `playbook/presentation.py` (`resolve_presentation`, reading the normalized flat `playbook["presentation"]`). Report fields `mr_description_checklists`/`mr_templates` become `checklists`/`templates`. `REPORT_SCHEMA_VERSION` goes 1 → 2 (hard-cut; downstream repos migrate in follow-up cycles). A `regis playbook migrate` codemod step moves `integrations.gitlab` → `presentation`.

**Tech Stack:** Python 3.10+, Click, JSON Schema, ruamel.yaml, pytest.

**Spec:** `docs/superpowers/specs/2026-06-06-playbook-presentation-generalization-design.md`.

**Branch:** fresh branch off the latest `main` **after PR #652 (GitLab extraction) is merged** — this plan renames `regis/playbook/integrations/gitlab.py`, which #652 keeps; branching before #652 merges risks a rename conflict.

**Breaking:** `feat(playbook)!` — playbook schema + report contract + `REPORT_SCHEMA_VERSION` bump.

---

## Task 1: Playbook schema — replace `spec.integrations` with `spec.presentation`

**Files:**

- Modify: `regis/schemas/playbook/v1alpha1/playbook.schema.json`
- Test: `tests/test_playbook_schema.py` (or wherever playbook-schema validation is tested — search with `grep -rln "playbook.schema" tests/`; if no dedicated file, add `tests/test_presentation_schema.py`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_presentation_schema.py`:

```python
"""Schema validation for the spec.presentation section."""

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA = json.loads(
    Path("regis/schemas/playbook/v1alpha1/playbook.schema.json").read_text()
)


def _doc(spec_extra: dict) -> dict:
    return {
        "apiVersion": "regis.trivoallan.dev/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "p", "labels": {"app.kubernetes.io/version": "1.0.0"}},
        "spec": {"rules": [], **spec_extra},
    }


def test_presentation_section_validates():
    doc = _doc(
        {
            "presentation": {
                "badges": ["score"],
                "checklists": [{"title": "T", "items": [{"label": "do X"}]}],
                "templates": [{"url": "gh:org/tmpl"}],
            }
        }
    )
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)


def test_integrations_section_is_rejected():
    doc = _doc({"integrations": {"gitlab": {"badges": ["score"]}}})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(SCHEMA).validate(doc)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pipenv run pytest tests/test_presentation_schema.py -q`
Expected: FAIL (`presentation` not yet allowed; `integrations` still allowed so the second test fails).

- [ ] **Step 3: Edit the schema**

In `regis/schemas/playbook/v1alpha1/playbook.schema.json`, under `properties.spec.properties`, **remove** the `integrations` property entirely and **add** `presentation`:

```json
"presentation": {
  "type": "object",
  "description": "Platform-neutral presentation directives surfaced to downstream integrations (labels, checklists, templates).",
  "additionalProperties": false,
  "properties": {
    "badges": {
      "type": "array",
      "description": "Badge slugs to surface as labels for consuming integrations.",
      "items": { "type": "string" }
    },
    "checklists": {
      "type": "array",
      "description": "Conditional checklists surfaced by integrations (e.g. in an MR/PR description).",
      "items": {
        "type": "object",
        "required": ["items"],
        "properties": {
          "title": { "type": "string", "description": "Display title for the checklist." },
          "items": {
            "type": "array",
            "description": "Items in this checklist.",
            "items": { "$ref": "#/$defs/checklist_item" }
          }
        }
      }
    },
    "templates": {
      "type": "array",
      "description": "Conditional Cookiecutter templates surfaced to integrations.",
      "items": {
        "type": "object",
        "required": ["url"],
        "additionalProperties": false,
        "properties": {
          "url": { "type": "string", "description": "Cookiecutter template URL or path." },
          "directory": { "type": "string", "description": "Optional subdirectory containing the template." },
          "condition": {
            "description": "JSON Logic expression to conditionally surface the template.",
            "$ref": "../jsonlogic.schema.json"
          }
        }
      }
    }
  }
}
```

Note: the deprecated singular `checklist` is intentionally NOT carried over (the migration folds it into `checklists`). Keep the existing `$defs/checklist_item` definition (still referenced).

- [ ] **Step 4: Run the test to confirm it passes**

Run: `pipenv run pytest tests/test_presentation_schema.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/schemas/playbook/v1alpha1/playbook.schema.json tests/test_presentation_schema.py
git commit -m "$(cat <<'EOF'
feat(playbook)!: add spec.presentation, remove spec.integrations

BREAKING CHANGE: the playbook `spec.integrations.gitlab` section is
replaced by the platform-neutral `spec.presentation` (badges, checklists,
templates). Run `regis playbook migrate` to update playbooks.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Rename the resolver to `presentation.py` and read `presentation`

**Files:**

- Rename: `regis/playbook/integrations/gitlab.py` → `regis/playbook/presentation.py`
- Delete: `regis/playbook/integrations/__init__.py` (and the now-empty `integrations/` dir)
- Modify: `regis/playbook/evaluator.py` (import + call + docstring)

- [ ] **Step 1: Move the module**

```bash
git mv regis/playbook/integrations/gitlab.py regis/playbook/presentation.py
git rm regis/playbook/integrations/__init__.py
```

(`integrations/` is now empty; `git rm` of its `__init__.py` removes the package.)

- [ ] **Step 2: Edit `regis/playbook/presentation.py`**

Update the module docstring + the public function. Change the docstring (lines 1-5) to:

```python
"""Presentation resolvers for the playbook engine.

Evaluates platform-neutral presentation directives (labels from badges,
checklists, templates) against the full evaluation context. Consumed by
downstream integrations (GitLab MR, GitHub PR, Backstage, …).
"""
```

Rename the public function and change the section it reads — replace:

```python
def resolve_gitlab_integration(
    playbook: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve all GitLab integration directives (badges, checklists, templates).

    Returns a dict merged into the evaluation result by the orchestrator.
    """
    integration = playbook.get("integrations", {}).get("gitlab", {})
    result: dict[str, Any] = {}
    result.update(_resolve_badge_labels(integration, full_context))
    result.update(_resolve_checklists(integration, full_context))
    result.update(_resolve_templates(integration, full_context))

    return result
```

with:

```python
def resolve_presentation(
    playbook: dict[str, Any],
    full_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve all presentation directives (badges, checklists, templates).

    Reads the normalized flat ``playbook["presentation"]`` (the loader projects
    ``spec.presentation`` onto the top level). Returns a dict merged into the
    evaluation result by the orchestrator.
    """
    presentation = playbook.get("presentation", {})
    result: dict[str, Any] = {}
    result.update(_resolve_badge_labels(presentation, full_context))
    result.update(_resolve_checklists(presentation, full_context))
    result.update(_resolve_templates(presentation, full_context))

    return result
```

Leave `_resolve_badge_labels`, `_resolve_checklists`, `_resolve_templates` bodies as-is for now (their output keys are renamed in Task 3). The parameter name `integration` inside those helpers can stay or be renamed to `directives` — cosmetic, optional.

- [ ] **Step 3: Edit `regis/playbook/evaluator.py`**

Replace the import (currently line 17):

```python
from regis.playbook.integrations.gitlab import resolve_gitlab_integration
```

with:

```python
from regis.playbook.presentation import resolve_presentation
```

Replace the call (currently line 296):

```python
    result.update(resolve_gitlab_integration(playbook, full_context))
```

with:

```python
    result.update(resolve_presentation(playbook, full_context))
```

Update the comment on the line above (currently `# Resolve sidebar, links, and GitLab integration`) to `# Resolve sidebar, links, and presentation directives`, and the module docstring line 8 (`Resolves playbook-level links and GitLab integration directives.`) to `Resolves playbook-level links and presentation directives.`.

- [ ] **Step 4: Verify imports resolve and nothing else references the old path**

Run: `grep -rn "resolve_gitlab_integration\|playbook.integrations\|integrations.gitlab" regis/`
Expected: no matches.

Run: `pipenv run python -c "from regis.playbook.presentation import resolve_presentation; print('ok')"`
Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor(playbook): rename gitlab resolver to generic presentation

`playbook/integrations/gitlab.py` -> `playbook/presentation.py`;
`resolve_gitlab_integration` -> `resolve_presentation`, reading
`playbook["presentation"]`. Drops the hardcoded GitLab coupling from the
evaluator.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Rename report output fields `mr_*` → neutral

**Files:**

- Modify: `regis/playbook/presentation.py` (output keys)
- Modify: `regis/schemas/playbook/result.schema.json`
- Test: `tests/test_playbook_engine.py` (the presentation tests — see Task 6 for renaming the classes; here, update expected keys)

- [ ] **Step 1: Update the output keys in `presentation.py`**

In `_resolve_checklists`, change the returned key (currently `return {"mr_description_checklists": resolved_checklists}`):

```python
    if resolved_checklists:
        return {"checklists": resolved_checklists}
    return {}
```

In `_resolve_templates`, change the returned key (currently `return {"mr_templates": resolved_templates}`):

```python
    if resolved_templates:
        return {"templates": resolved_templates}
    return {}
```

`_resolve_badge_labels` keeps `{"badge_labels": ...}` (already neutral).

- [ ] **Step 2: Update `regis/schemas/playbook/result.schema.json`**

Rename the `mr_templates` property to `templates` (same shape) and, if present, `mr_description_checklists` to `checklists`. Run `grep -n "mr_templates\|mr_description_checklists\|badge_labels\|checklists\|templates" regis/schemas/playbook/result.schema.json` first to locate them; rename the `mr_`-prefixed keys, keep `badge_labels`. If `mr_description_checklists` is not explicitly in the schema (the result schema allows extra props), add a `checklists` property mirroring the old shape (array of `{title, items:[{label, checked}]}`).

- [ ] **Step 3: Update the engine tests' expected keys**

In `tests/test_playbook_engine.py`, update every assertion that reads `result["mr_description_checklists"]` → `result["checklists"]` and `result["mr_templates"]` → `result["templates"]`. (Use `grep -n "mr_description_checklists\|mr_templates" tests/test_playbook_engine.py` to find them.)

- [ ] **Step 4: Run the engine tests**

Run: `pipenv run pytest tests/test_playbook_engine.py -q`
Expected: PASS (after the key renames).

- [ ] **Step 5: Confirm no `mr_`-prefixed presentation keys remain**

Run: `grep -rn "mr_description_checklists\|mr_templates" regis/ tests/`
Expected: no matches.

- [ ] **Step 6: Commit**

```bash
git add regis/playbook/presentation.py regis/schemas/playbook/result.schema.json tests/test_playbook_engine.py
git commit -m "$(cat <<'EOF'
feat(playbook)!: neutralize report presentation field names

BREAKING CHANGE: report fields `mr_description_checklists` -> `checklists`
and `mr_templates` -> `templates` (`badge_labels` unchanged). Downstream
consumers must read the new field names.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Bump `REPORT_SCHEMA_VERSION` 1 → 2

**Files:**

- Modify: `regis/utils/report.py` (line 17)
- Modify: contract fixture(s) — find with `grep -rln "schemaVersion" tests/fixtures/`

- [ ] **Step 1: Bump the constant**

In `regis/utils/report.py`, change:

```python
REPORT_SCHEMA_VERSION = 1
```

to:

```python
REPORT_SCHEMA_VERSION = 2
```

- [ ] **Step 2: Update the contract fixture**

Run: `grep -rln "schemaVersion" tests/fixtures/`. For each report fixture (e.g. `tests/fixtures/report.v1.json`), update its `schemaVersion` to `2` (and rename the file to `report.v2.json` if the test references the version in the filename; update the referencing test accordingly). If a test asserts the exact integer, update it to `2`.

- [ ] **Step 3: Run the report/schema tests**

Run: `pipenv run pytest -q -k "schema_version or report_schema or ensure_schema"`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/utils/report.py tests/fixtures/
git commit -m "$(cat <<'EOF'
feat(schema)!: bump REPORT_SCHEMA_VERSION to 2

BREAKING CHANGE: the report envelope advertises schemaVersion 2 (neutral
presentation fields). Consumers gating on schemaVersion must widen their
accepted range.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Migration codemod — `integrations.gitlab` → `presentation`

**Files:**

- Modify: `regis/commands/playbook.py` (`_migrate_playbook_data` + the `migrate` command docstring)
- Test: `tests/commands/test_playbook_migrate.py` (or wherever migrate is tested — `grep -rln "playbook.*migrate\|_migrate_playbook_data" tests/`)

- [ ] **Step 1: Write the failing test**

Add to the migrate test file:

```python
def test_migrate_integrations_gitlab_to_presentation():
    from regis.commands.playbook import _migrate_playbook_data

    data = {
        "apiVersion": "regis.trivoallan.dev/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "p"},
        "spec": {
            "rules": [],
            "integrations": {
                "gitlab": {
                    "badges": ["score"],
                    "checklist": [{"label": "legacy item"}],
                    "templates": [{"url": "gh:org/t"}],
                }
            },
        },
    }
    _migrate_playbook_data(data)

    assert "integrations" not in data["spec"]
    pres = data["spec"]["presentation"]
    assert pres["badges"] == ["score"]
    # the deprecated singular `checklist` is folded into `checklists`
    assert pres["checklists"] == [{"items": [{"label": "legacy item"}]}]
    assert pres["templates"] == [{"url": "gh:org/t"}]


def test_migrate_presentation_is_idempotent():
    from regis.commands.playbook import _migrate_playbook_data

    data = {
        "apiVersion": "regis.trivoallan.dev/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "p"},
        "spec": {"rules": [], "presentation": {"badges": ["score"]}},
    }
    _migrate_playbook_data(data)
    assert data["spec"]["presentation"] == {"badges": ["score"]}
    assert "integrations" not in data["spec"]
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `pipenv run pytest tests/commands/test_playbook_migrate.py -q -k presentation`
Expected: FAIL (`presentation` not produced; `integrations` still present).

- [ ] **Step 3: Add the migration helper + wire it into `_migrate_playbook_data`**

In `regis/commands/playbook.py`, add a helper above `_migrate_playbook_data`:

```python
def _migrate_integrations_to_presentation(container: Any) -> None:
    """Move ``integrations.gitlab.{badges,checklist,checklists,templates}`` to a
    platform-neutral ``presentation`` block on the same container. Idempotent.

    Folds the deprecated singular ``checklist`` into ``checklists``.
    """
    if not isinstance(container, dict):
        return
    integrations = container.get("integrations")
    if not isinstance(integrations, dict):
        return
    gitlab = integrations.get("gitlab")
    if not isinstance(gitlab, dict):
        return

    presentation = container.get("presentation")
    if not isinstance(presentation, dict):
        presentation = {}

    if "badges" in gitlab and "badges" not in presentation:
        presentation["badges"] = gitlab["badges"]
    if "templates" in gitlab and "templates" not in presentation:
        presentation["templates"] = gitlab["templates"]

    checklists = gitlab.get("checklists")
    if not checklists and gitlab.get("checklist"):
        # fold the deprecated singular `checklist` into the `checklists` shape
        checklists = [{"items": gitlab["checklist"]}]
    if checklists and "checklists" not in presentation:
        presentation["checklists"] = checklists

    if presentation:
        container["presentation"] = presentation

    # remove the now-migrated gitlab integration; drop `integrations` if empty
    integrations.pop("gitlab", None)
    if not integrations:
        container.pop("integrations", None)
```

Then, inside `_migrate_playbook_data`, after the rule-migration loop, add the presentation migration for both the envelope and flat shapes:

```python
    # presentation migration (integrations.gitlab -> presentation)
    if isinstance(spec, dict):
        _migrate_integrations_to_presentation(spec)
    else:
        _migrate_integrations_to_presentation(data)
```

(Place this at the end of `_migrate_playbook_data`. `spec` is already computed earlier in that function; reuse it.)

- [ ] **Step 4: Update the `migrate` command docstring**

In `migrate_playbook`'s docstring, add a third bullet:

```text
    3. ``spec.integrations.gitlab`` → platform-neutral ``spec.presentation``
       (folding the deprecated singular ``checklist`` into ``checklists``).
```

- [ ] **Step 5: Run the migration tests**

Run: `pipenv run pytest tests/commands/test_playbook_migrate.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add regis/commands/playbook.py tests/commands/test_playbook_migrate.py
git commit -m "$(cat <<'EOF'
feat(playbook): migrate integrations.gitlab to presentation in codemod

`regis playbook migrate` now moves spec.integrations.gitlab to the
neutral spec.presentation (idempotent; folds singular checklist).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Dogfood — migrate the default playbook + cookiecutters + test class names

**Files:**

- Modify: `regis/playbooks/default/playbook.yaml` (lines ~153–end of integrations)
- Modify: `regis/cookiecutters/playbook/` (any `integrations:` in the templated playbook)
- Modify: `tests/test_playbook_engine.py` (rename `TestGitLabChecklist`/`TestGitLabTemplates` and their playbook fixtures)

- [ ] **Step 1: Migrate the default playbook in place**

Run: `pipenv run regis playbook migrate regis/playbooks/default/playbook.yaml --in-place`
Then open `regis/playbooks/default/playbook.yaml` and confirm `spec.integrations` is gone and `spec.presentation` carries `badges`/`checklists`/`templates`. Validate:
Run: `pipenv run regis playbook validate regis/playbooks/default/playbook.yaml`
Expected: `✓ ... is valid`.

- [ ] **Step 2: Migrate the cookiecutter playbook(s)**

Run: `grep -rln "integrations:" regis/cookiecutters/playbook/`. For each hit, change `integrations:\n  gitlab:` to a `presentation:` block with the same `badges`/`checklists`/`templates` children (drop the `gitlab:` nesting). Keep any Jinja/cookiecutter placeholders intact.

- [ ] **Step 3: Rename the engine test classes + their playbook fixtures**

In `tests/test_playbook_engine.py`: rename `class TestGitLabChecklist` → `class TestPresentationChecklists` and `class TestGitLabTemplates` → `class TestPresentationTemplates`. In their inline playbook fixtures, change `integrations: {gitlab: {...}}` → `presentation: {...}` (drop the `gitlab` nesting). Expected result keys are already `checklists`/`templates` from Task 3.

- [ ] **Step 4: Run the relevant tests**

Run: `pipenv run pytest tests/test_playbook_engine.py -q`
Expected: PASS.

- [ ] **Step 5: Confirm no `integrations.gitlab` remains in shipped playbooks/tests**

Run: `grep -rn "integrations:" regis/playbooks regis/cookiecutters tests/ | grep -v versioned`
Expected: no matches (or only unrelated uses).

- [ ] **Step 6: Commit**

```bash
git add regis/playbooks regis/cookiecutters tests/test_playbook_engine.py
git commit -m "$(cat <<'EOF'
chore(playbook): migrate default playbook and cookiecutters to presentation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Documentation

**Files:**

- Modify: `docs/website/docs/concepts/playbooks.md`
- Modify: `docs/website/docs/roadmap.md`
- Regenerate: `docs/website/docs/reference/schemas/playbook/*.md` (if generated; else edit by hand)

- [ ] **Step 1: Reframe `concepts/playbooks.md`**

Find the GitLab-integration / MR-description-checklists section(s): `grep -n "integrations\|gitlab\|mr_description\|MR description\|Merge Request" docs/website/docs/concepts/playbooks.md`. Rewrite them around `spec.presentation` (badges → labels, checklists, templates) as platform-neutral directives that integrations (GitLab MR, GitHub PR, Backstage) render. Keep anchors used by other pages working (e.g. if `#mr-description-checklists` is linked elsewhere, add a redirecting note or update the linkers — check with `grep -rn "mr-description-checklists" docs/website/docs/ | grep -v versioned`).

- [ ] **Step 2: Update `roadmap.md` "Stable API surface"**

In `docs/website/docs/roadmap.md`, the stable-API bullet lists `mr_description_checklists`. Replace it with the neutral `presentation` / `checklists` naming, and note the `report.json` `schemaVersion` is now `2`.

- [ ] **Step 3: Regenerate / fix the schema reference docs**

If `docs/website/docs/reference/schemas/playbook/*.md` are generated from the JSON schemas, regenerate them (find the generator: `grep -rln "json-schema-for-humans\|schema.*\.md" scripts/ docs/`); else hand-edit the `playbook.schema.md` / `result.schema.md` to reflect `presentation` and the renamed result fields.

- [ ] **Step 4: Verify docs build with no broken links**

Run the Docusaurus build under `docs/website`. Confirm success and no broken-link errors. Run `grep -rn "integrations.gitlab\|mr_description_checklists\|mr_templates" docs/website/docs/ | grep -v versioned_docs` → expect no matches.

- [ ] **Step 5: Commit**

```bash
git add docs/website/docs
git commit -m "$(cat <<'EOF'
docs(playbook): document spec.presentation and neutral report fields

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Final verification & PR

- [ ] **Step 1: Full lint + suite with coverage**

Run: `pipenv run ruff check . && pipenv run pytest`
Expected: lint clean; suite PASS; coverage ≥ 90 %.

- [ ] **Step 2: Confirm the platform coupling is gone**

Run: `grep -rn "integrations.gitlab\|resolve_gitlab_integration\|mr_description_checklists\|mr_templates\|playbook.integrations" regis/ tests/`
Expected: no matches.

Run: `pipenv run regis analyze --help` (sanity — the CLI still loads).

- [ ] **Step 3: Run trunk**

Run: `trunk check`
Expected: green (commit any auto-fixes).

- [ ] **Step 4: Open the PR**

Push the branch and open a PR titled `feat(playbook)!: generalize integrations.gitlab into spec.presentation`. In `## Summary`, document the breaking changes (playbook schema, report fields, `REPORT_SCHEMA_VERSION` 1→2) and that follow-up cycles update regis-gitlab (#2), regis-backstage (#3), and regis-action (#4) to the neutral contract. Confirm Release Please bumps the minor version (pre-v1, `bump-minor-pre-major`).

---

## Notes for the implementer

- Branch off `main` **after PR #652 merges** (this renames `playbook/integrations/gitlab.py`, kept by #652).
- This is breaking on three surfaces (playbook schema, report fields, schemaVersion) → one `feat(playbook)!` PR, pre-v1 minor bump.
- Downstream repos are explicitly out of scope (follow-up sub-projects #2/#3/#4); they degrade gracefully until updated (backstage gates on schemaVersion; the regis-gitlab template uses `// []`).
- `versioned_docs/**` are frozen — never edit them.
