# Playbook Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `schemaVersion` (integer, required) and `version` (SemVer string, required) to the playbook format, enforce them via a versioned schema registry, and propagate playbook + regis identity into the report for audit traceability.

**Architecture:** A schema registry under `regis/schemas/playbook/v1/` with a dispatch table in `regis/playbook/schema_registry.py` lets the loader pick the right JSON Schema based on the playbook's declared `schemaVersion`. Missing or unknown versions hard-fail with a guiding error. Playbook metadata (`name`, `version`, `schemaVersion`) is injected into the playbook evaluation result; regis binary version is already propagated through `analysis_report["version"]`.

**Tech Stack:** Python 3.x, `pyyaml`, `jsonschema`, `click`, `pipenv`/`pytest`, `ruamel.yaml` (added for the upgrade helper if Task 11 is kept).

**Reference spec:** [docs/superpowers/specs/2026-05-31-playbook-versioning-design.md](../specs/2026-05-31-playbook-versioning-design.md)

---

## File Structure

**Created:**
- `regis/schemas/playbook/v1/__init__.py` — empty (package marker)
- `regis/schemas/playbook/v1/definition.schema.json` — moved from parent dir, with new required fields
- `regis/playbook/schema_registry.py` — version → schema dispatch
- `tests/test_schema_registry.py` — registry unit tests
- `docs/website/docs/reference/playbook-schema.md` — public reference doc

**Modified:**
- `regis/playbook/loader.py` — adds `PlaybookVersionError`, version extraction, registry dispatch, JSON Schema validation
- `regis/schemas/playbook/result.schema.json` — declare `playbook_version` and `schema_version` properties
- `regis/playbook/evaluator.py` — inject `playbook_version` and `schema_version` into the result
- `regis/commands/playbook.py` — `validate` command uses the registry and reports detected `schemaVersion`
- `regis/playbooks/default/playbook.yaml` — add `schemaVersion: 1` + `version: 1.0.0`
- `.claude/skills/create-playbook/SKILL.md` (or its scaffolding files) — emit new fields by default
- `tests/test_playbook_loader.py` — error-path tests
- `tests/test_utils_report.py` — report propagation tests
- `tests/test_playbook_engine.py` — fixtures get the new required fields
- `tests/test_remote_playbook.py` — fixtures get the new required fields
- `tests/test_coverage_engine.py` — fixtures get the new required fields
- `tests/test_rules_config.py` — fixtures get the new required fields
- Docs YAML snippets in `docs/website/docs/usage/custom-playbook.md`, `configuration.md`, etc.

**Deleted:**
- `regis/schemas/playbook/definition.schema.json` — moved into `v1/`

---

## Task 1: Move the schema file into a v1/ subdirectory

**Goal:** Establish the registry layout without changing semantics yet. After this task, the schema still validates the same playbook shape, just from a new path.

**Files:**
- Create: `regis/schemas/playbook/v1/__init__.py` (empty)
- Move: `regis/schemas/playbook/definition.schema.json` → `regis/schemas/playbook/v1/definition.schema.json`
- Modify: `regis/commands/playbook.py` — update path lookup

### Steps

- [ ] **Step 1: Create the v1 package marker**

```bash
mkdir -p regis/schemas/playbook/v1
touch regis/schemas/playbook/v1/__init__.py
```

- [ ] **Step 2: Move the schema file**

```bash
git mv regis/schemas/playbook/definition.schema.json regis/schemas/playbook/v1/definition.schema.json
```

- [ ] **Step 3: Update `$id` in the moved schema**

In `regis/schemas/playbook/v1/definition.schema.json` line 3, change:

```json
"$id": "https://trivoallan.github.io/regis/schemas/playbook/definition.schema.json",
```

to:

```json
"$id": "https://trivoallan.github.io/regis/schemas/playbook/v1/definition.schema.json",
```

- [ ] **Step 4: Update the `$ref` to jsonlogic.schema.json**

The schema references `jsonlogic.schema.json` (relative). Since we moved up a directory, change every occurrence of:

```json
"$ref": "jsonlogic.schema.json"
```

to:

```json
"$ref": "../jsonlogic.schema.json"
```

There are multiple occurrences (around lines 40, 184, 256, 283 in the current file). Use `Edit` with `replace_all: true`, or fix each manually after a grep.

- [ ] **Step 5: Update path lookup in `regis/commands/playbook.py`**

Around line 41, change:

```python
schema_pkg.joinpath("definition.schema.json").read_text(encoding="utf-8")
```

to:

```python
schema_pkg.joinpath("v1", "definition.schema.json").read_text(encoding="utf-8")
```

Adjust the `schema_pkg` resolution if the package import points one level too high. Read the surrounding 20 lines to be sure the path is correct.

- [ ] **Step 6: Run the suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: all tests pass (no behavioral change).

- [ ] **Step 7: Commit**

```bash
git add regis/schemas/playbook/v1/__init__.py regis/schemas/playbook/v1/definition.schema.json regis/commands/playbook.py
git commit -m "refactor(playbook): move definition.schema.json into v1/ subdirectory

Prepare for multi-version dispatch: \`$id\` and \`$ref\` paths updated,
\`regis playbook validate\` follows the new location. Behavior unchanged."
```

---

## Task 2: Pre-migrate the default playbook with new fields (still optional)

**Goal:** Add `schemaVersion: 1` and `version: "1.0.0"` to the default playbook. Done BEFORE the fields become required so the test suite never sees a transient invalid state.

**Files:**
- Modify: `regis/playbooks/default/playbook.yaml`

### Steps

- [ ] **Step 1: Add the two fields**

At the top of `regis/playbooks/default/playbook.yaml`, immediately after the `yaml-language-server` comment line, insert:

```yaml
schemaVersion: 1
version: "1.0.0"
```

So the file starts with:

```yaml
# yaml-language-server: $schema=../schemas/playbook/v1/definition.schema.json
schemaVersion: 1
version: "1.0.0"
name: RegiS Default Playbook
```

Note: also update the `$schema` URL in the language-server comment to point to `v1/`.

- [ ] **Step 2: Run the suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: all tests pass — fields are silently ignored because the schema still has `additionalProperties: false` only on the root; the new fields are not yet declared. Actually wait: the schema HAS `"additionalProperties": false` on the root object. So adding unknown fields will fail validation immediately.

**Mitigation:** also update the schema in this commit to declare the two new fields as optional (not yet required). Add to `regis/schemas/playbook/v1/definition.schema.json` under `properties`:

```json
"schemaVersion": {
  "type": "integer",
  "description": "Schema version of the playbook format (added in this commit, not yet required)."
},
"version": {
  "type": "string",
  "description": "SemVer of the playbook bundle (added in this commit, not yet required)."
}
```

(No pattern, no const — those tighten later in Task 5.)

- [ ] **Step 3: Re-run the suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add regis/playbooks/default/playbook.yaml regis/schemas/playbook/v1/definition.schema.json
git commit -m "feat(playbook): seed schemaVersion and version on default playbook

Two new optional fields recognized by the schema. Default playbook gets
schemaVersion: 1 and version: 1.0.0. Enforcement comes in a follow-up commit."
```

---

## Task 3: Pre-migrate all in-tree playbook fixtures

**Goal:** Add the two new fields to every inline / file-based playbook used by the test suite and the docs, so that when the fields become required (Task 5), no fixture breaks.

**Files:** every test that constructs a playbook dict or YAML string, plus docs YAML snippets.

### Steps

- [ ] **Step 1: Inventory inline playbook fixtures**

Run:

```bash
grep -rln "tiers:\|name:.*[Pp]laybook\|load_playbook\|playbook = {\|playbook_yaml = " tests/ docs/website/docs/
```

Expected: list of files containing inline playbook YAML or dict literals. Likely candidates:

- `tests/test_playbook_engine.py`
- `tests/test_playbook_loader.py`
- `tests/test_remote_playbook.py`
- `tests/test_coverage_engine.py`
- `tests/test_rules_config.py`
- `tests/test_utils_report.py`
- `docs/website/docs/usage/custom-playbook.md`
- `docs/website/docs/usage/configuration.md`

- [ ] **Step 2: For each file, add the two fields**

For each playbook fixture (Python dict literal or YAML string), add at the top:

For dict literals:
```python
playbook = {
    "schemaVersion": 1,
    "version": "1.0.0",
    "name": "Test Playbook",
    # … existing keys …
}
```

For YAML strings:
```python
playbook_yaml = """
schemaVersion: 1
version: "1.0.0"
name: Test Playbook
…
"""
```

For docs YAML snippets in Markdown, prepend the same two lines to every ` ```yaml ` fenced block representing a full playbook (not partial snippets).

**Note:** partial snippets that don't carry `name:` don't need the new fields — they're illustrative fragments.

- [ ] **Step 3: Run the suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS. The fields are still optional at the schema level, so they're harmless.

- [ ] **Step 4: Commit**

```bash
git add tests/ docs/website/docs/
git commit -m "test(playbook): add schemaVersion and version to all in-tree playbook fixtures

Prepares the test suite for the upcoming enforcement of these fields as required."
```

---

## Task 4: Create the schema registry module

**Goal:** Introduce `regis/playbook/schema_registry.py` with a versioned dispatch table.

**Files:**
- Create: `regis/playbook/schema_registry.py`
- Create: `tests/test_schema_registry.py`

### Steps

- [ ] **Step 1: Write the registry tests**

Create `tests/test_schema_registry.py`:

```python
"""Tests for the playbook schema registry."""

from __future__ import annotations

import pytest

from regis.playbook import schema_registry


def test_supported_versions_lists_v1() -> None:
    assert schema_registry.supported_versions() == [1]


def test_get_schema_v1_returns_dict_with_expected_id() -> None:
    schema = schema_registry.get_schema(1)
    assert isinstance(schema, dict)
    assert schema["$id"].endswith("/v1/definition.schema.json")
    assert schema["title"] == "playbook.definition"


def test_get_schema_unknown_version_raises_key_error() -> None:
    with pytest.raises(KeyError):
        schema_registry.get_schema(99)
```

- [ ] **Step 2: Run the tests, expect failure**

```bash
pipenv run pytest tests/test_schema_registry.py --no-cov -q
```

Expected: FAIL with `ModuleNotFoundError: regis.playbook.schema_registry`.

- [ ] **Step 3: Implement the registry**

Create `regis/playbook/schema_registry.py`:

```python
"""Playbook schema registry — version → JSON Schema dispatch."""

from __future__ import annotations

import functools
import importlib.resources
import json
from typing import Any


@functools.lru_cache(maxsize=None)
def _load_schema_v1() -> dict[str, Any]:
    pkg = importlib.resources.files("regis.schemas.playbook.v1")
    text = pkg.joinpath("definition.schema.json").read_text(encoding="utf-8")
    return json.loads(text)


_SCHEMAS: dict[int, callable] = {
    1: _load_schema_v1,
}


def supported_versions() -> list[int]:
    """Return the sorted list of supported schema versions."""
    return sorted(_SCHEMAS.keys())


def get_schema(schema_version: int) -> dict[str, Any]:
    """Return the JSON Schema for *schema_version*.

    Raises KeyError if the version is not supported.
    """
    try:
        loader = _SCHEMAS[schema_version]
    except KeyError:
        raise KeyError(
            f"Unsupported schemaVersion {schema_version!r}. "
            f"Supported: {supported_versions()}."
        ) from None
    return loader()
```

- [ ] **Step 4: Run the tests, expect pass**

```bash
pipenv run pytest tests/test_schema_registry.py --no-cov -q
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add regis/playbook/schema_registry.py tests/test_schema_registry.py
git commit -m "feat(playbook): add schema registry for versioned dispatch

Introduces schema_registry.get_schema(version) and supported_versions().
Currently exposes v1; future versions plug in by adding a sibling loader."
```

---

## Task 5: Enforce schemaVersion and version in the v1 schema

**Goal:** Tighten the v1 schema so both fields are required, `schemaVersion` is a `const: 1`, and `version` matches the SemVer pattern.

**Files:**
- Modify: `regis/schemas/playbook/v1/definition.schema.json`

### Steps

- [ ] **Step 1: Update the field definitions**

In `regis/schemas/playbook/v1/definition.schema.json`, replace the loose declarations added in Task 2 with:

```json
"schemaVersion": {
  "const": 1,
  "description": "Schema version of the playbook format. Must equal 1 for this schema."
},
"version": {
  "type": "string",
  "pattern": "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$",
  "description": "SemVer of the playbook bundle (e.g. \"1.2.3\")."
}
```

- [ ] **Step 2: Promote both fields to the `required` array**

Change `"required": ["name"]` (line 7) to:

```json
"required": ["schemaVersion", "version", "name"],
```

- [ ] **Step 3: Run the suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS. All fixtures were pre-migrated in Tasks 2–3.

If any test fails with `'schemaVersion' is a required property`, find the missing fixture, add the two fields, and re-run.

- [ ] **Step 4: Commit**

```bash
git add regis/schemas/playbook/v1/definition.schema.json
git commit -m "feat(playbook)!: require schemaVersion and version in v1 schema

BREAKING CHANGE: every playbook must now declare \`schemaVersion: 1\` and a
SemVer-formatted \`version\`. Existing playbooks must be migrated; see the
upgrade guide."
```

---

## Task 6: Refactor the loader with hard-fail dispatch

**Goal:** `load_playbook()` now extracts `schemaVersion`, dispatches via the registry, and validates against the right schema — with guiding error messages.

**Files:**
- Modify: `regis/playbook/loader.py`
- Modify: `tests/test_playbook_loader.py` (or create new tests if file is sparse)

### Steps

- [ ] **Step 1: Write tests for the error paths**

Append to `tests/test_playbook_loader.py` (or create the file if absent):

```python
"""Tests for playbook loader version dispatch."""

from __future__ import annotations

import pytest
import yaml

from regis.playbook.loader import PlaybookVersionError, load_playbook


def _write(tmp_path, content: str) -> str:
    path = tmp_path / "playbook.yaml"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_loads_valid_v1_playbook(tmp_path) -> None:
    content = """
schemaVersion: 1
version: "1.0.0"
name: Valid Playbook
"""
    pb = load_playbook(_write(tmp_path, content))
    assert pb["schemaVersion"] == 1
    assert pb["version"] == "1.0.0"
    assert pb["name"] == "Valid Playbook"


def test_missing_schema_version_raises(tmp_path) -> None:
    content = """
version: "1.0.0"
name: No Schema Version
"""
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "schemaVersion" in str(exc.value)
    assert "Add `schemaVersion: 1`" in str(exc.value)
    assert "[1]" in str(exc.value)


def test_schema_version_not_integer_raises(tmp_path) -> None:
    content = """
schemaVersion: "1"
version: "1.0.0"
name: String Schema Version
"""
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "must be an integer" in str(exc.value)


def test_unknown_schema_version_raises(tmp_path) -> None:
    content = """
schemaVersion: 99
version: "1.0.0"
name: Future Playbook
"""
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "schemaVersion=99" in str(exc.value)
    assert "[1]" in str(exc.value)


def test_missing_version_field_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = """
schemaVersion: 1
name: No Version
"""
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))


def test_invalid_semver_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = """
schemaVersion: 1
version: "1.2"
name: Invalid SemVer
"""
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))
```

- [ ] **Step 2: Run tests, expect failure**

```bash
pipenv run pytest tests/test_playbook_loader.py --no-cov -q
```

Expected: most tests fail because `PlaybookVersionError` does not exist and the loader does no validation.

- [ ] **Step 3: Rewrite `regis/playbook/loader.py`**

Note on `$ref` resolution: the schema references `../jsonlogic.schema.json` relatively. The project already uses the `referencing` library (see how `regis/commands/playbook.py` builds its `Registry`). We reuse the same pattern.

Replace the body of `regis/playbook/loader.py` with:

```python
"""Playbook loading utilities.

Supports loading playbook definitions from:
- Local YAML or JSON files
- Local bundle directories (containing playbook.yaml)
- Remote HTTP/HTTPS URLs

Every playbook must declare ``schemaVersion`` (integer) at the top level.
The loader dispatches to the matching JSON Schema via the schema registry.
"""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource

from regis.playbook import schema_registry


class PlaybookVersionError(ValueError):
    """Raised when schemaVersion is missing, malformed, or unsupported."""


def load_playbook(path: str | Path) -> dict[str, Any]:
    """Load and validate a playbook from a file, bundle dir, or URL."""
    raw = _read_raw(path)
    schema_version = _extract_schema_version(raw, path)
    schema = _get_schema_or_raise(schema_version, path)
    _validate(raw, schema, path, schema_version)
    return raw


def _read_raw(path: str | Path) -> dict[str, Any]:
    if isinstance(path, str) and (
        path.startswith("http://") or path.startswith("https://")
    ):
        import requests

        try:
            response = requests.get(path, timeout=30)
            response.raise_for_status()
            text = response.text
            if path.lower().endswith(".json"):
                return json.loads(text)
            return yaml.safe_load(text)
        except Exception as exc:
            raise ValueError(f"Failed to download playbook from {path}: {exc}") from exc

    path = Path(path)
    if path.is_dir():
        path = path / "playbook.yaml"
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def _extract_schema_version(raw: dict[str, Any], path: str | Path) -> int:
    if "schemaVersion" not in raw:
        raise PlaybookVersionError(
            f"playbook '{path}' is missing required field 'schemaVersion'.\n"
            f"Add `schemaVersion: 1` at the top of the file.\n"
            f"Supported versions: {schema_registry.supported_versions()}."
        )
    value = raw["schemaVersion"]
    # YAML parses booleans before integers; reject bool explicitly so True/False don't slip in.
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlaybookVersionError(
            f"playbook '{path}' has an invalid schemaVersion: {value!r} must be an integer.\n"
            f"Supported versions: {schema_registry.supported_versions()}."
        )
    return value


def _get_schema_or_raise(schema_version: int, path: str | Path) -> dict[str, Any]:
    try:
        return schema_registry.get_schema(schema_version)
    except KeyError as exc:
        from importlib.metadata import version as _pkg_version

        raise PlaybookVersionError(
            f"playbook '{path}' declares schemaVersion={schema_version} but this "
            f"regis (v{_pkg_version('regis')}) only supports "
            f"{schema_registry.supported_versions()}. "
            f"Upgrade regis or use a compatible playbook."
        ) from exc


def _build_validator_registry(schema: dict[str, Any]) -> Registry:
    """Build a referencing.Registry that resolves the schema's relative $refs."""
    pkg_root = importlib.resources.files("regis.schemas.playbook")
    jsonlogic_schema = json.loads(
        pkg_root.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
    )
    return Registry().with_resources(
        [
            (schema.get("$id", ""), Resource.from_contents(schema)),
            (jsonlogic_schema.get("$id", ""), Resource.from_contents(jsonlogic_schema)),
            # The v1 schema references jsonlogic.schema.json as ../jsonlogic.schema.json.
            # Provide both spellings so the ref resolves regardless of the resolver's URI base.
            ("../jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
            ("jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
        ]
    )


def _validate(
    raw: dict[str, Any],
    schema: dict[str, Any],
    path: str | Path,
    schema_version: int,
) -> None:
    registry = _build_validator_registry(schema)
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    try:
        validator.validate(raw)
    except jsonschema.ValidationError as exc:
        exc.message = (
            f"playbook '{path}' failed validation against schemaVersion={schema_version}: "
            f"{exc.message}"
        )
        raise


def is_bundle(path: str | Path) -> bool:
    """Return True if *path* is a local directory (i.e. a playbook bundle)."""
    if isinstance(path, str) and (
        path.startswith("http://") or path.startswith("https://")
    ):
        return False
    return Path(path).is_dir()


def bundle_meta_schema_path(path: str | Path) -> Path | None:
    """Return the path to meta.schema.json inside a bundle, or None if absent."""
    schema = Path(path) / "meta.schema.json"
    return schema if schema.exists() else None
```

- [ ] **Step 4: Run tests, expect pass**

```bash
pipenv run pytest tests/test_playbook_loader.py tests/test_schema_registry.py --no-cov -q
```

Expected: all loader and registry tests pass.

- [ ] **Step 5: Run the full suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS. Fixture migration in Task 3 + schema enforcement in Task 5 should mean the loader now enforces what every test already complies with.

If any test fails with a missing `schemaVersion`, treat it as a missed fixture in Task 3 — add the field, re-run.

- [ ] **Step 6: Commit**

```bash
git add regis/playbook/loader.py tests/test_playbook_loader.py
git commit -m "feat(playbook)!: dispatch loader via schema registry, hard-fail on version mismatch

BREAKING CHANGE: \`load_playbook()\` now raises \`PlaybookVersionError\` when
\`schemaVersion\` is missing, malformed, or not in {1}. JSON Schema validation
is performed at load time."
```

---

## Task 7: Propagate playbook metadata into the evaluation result

**Goal:** Inject `playbook_version` and `schema_version` into the playbook result dict so `result.schema.json` consumers (dashboard, markdown rendering) can attribute reports to a specific playbook revision.

**Files:**
- Modify: `regis/playbook/evaluator.py`
- Modify: `tests/test_playbook_engine.py` (add assertion) OR `tests/test_utils_report.py`

### Steps

- [ ] **Step 1: Write the assertion test**

Add to `tests/test_playbook_engine.py` (or a relevant existing test file):

```python
def test_evaluate_propagates_playbook_metadata() -> None:
    from regis.playbook.evaluator import evaluate

    playbook = {
        "schemaVersion": 1,
        "version": "2.3.4",
        "name": "MetadataPlaybook",
    }
    report: dict = {"results": {}}
    result = evaluate(playbook, report)

    assert result["playbook_name"] == "MetadataPlaybook"
    assert result["playbook_version"] == "2.3.4"
    assert result["schema_version"] == 1
```

- [ ] **Step 2: Run test, expect failure**

```bash
pipenv run pytest tests/test_playbook_engine.py::test_evaluate_propagates_playbook_metadata --no-cov -q
```

Expected: FAIL — `KeyError: 'playbook_version'` or assertion error.

- [ ] **Step 3: Update `evaluate()` to inject the fields**

In `regis/playbook/evaluator.py`, locate the result dict assembly (around line 194, after the spec). Change:

```python
result: dict[str, Any] = {
    "playbook_name": playbook.get("name", "unnamed"),
    "score": (
        round(total_passed_all / total_scorecards_all * 100)
        if total_scorecards_all
        else 0
    ),
    "total_scorecards": total_scorecards_all,
    "passed_scorecards": total_passed_all,
    "pages": NamedList(pages_results),
    "rules": report["rules"],
    "rules_summary": report["rules_summary"],
    "slug": playbook.get("slug"),
}
```

to:

```python
result: dict[str, Any] = {
    "playbook_name": playbook.get("name", "unnamed"),
    "playbook_version": playbook.get("version"),
    "schema_version": playbook.get("schemaVersion"),
    "score": (
        round(total_passed_all / total_scorecards_all * 100)
        if total_scorecards_all
        else 0
    ),
    "total_scorecards": total_scorecards_all,
    "passed_scorecards": total_passed_all,
    "pages": NamedList(pages_results),
    "rules": report["rules"],
    "rules_summary": report["rules_summary"],
    "slug": playbook.get("slug"),
}
```

- [ ] **Step 4: Run the test, expect pass**

```bash
pipenv run pytest tests/test_playbook_engine.py::test_evaluate_propagates_playbook_metadata --no-cov -q
```

Expected: PASS.

- [ ] **Step 5: Run the full suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add regis/playbook/evaluator.py tests/test_playbook_engine.py
git commit -m "feat(playbook): propagate playbook_version and schema_version into the report

The playbook result now carries enough information to attribute the report
to a specific playbook revision. Regis binary version remains in the
top-level analysis_report['version']."
```

---

## Task 8: Declare the new fields in result.schema.json

**Goal:** Document the new fields in the report schema and add a validation test.

**Files:**
- Modify: `regis/schemas/playbook/result.schema.json`
- Modify: `tests/test_utils_report.py`

### Steps

- [ ] **Step 1: Add the field declarations**

In `regis/schemas/playbook/result.schema.json`, alongside the existing `playbook_name`:

```json
"playbook_version": {
  "type": ["string", "null"],
  "description": "SemVer of the playbook that produced this report."
},
"schema_version": {
  "type": ["integer", "null"],
  "description": "schemaVersion of the playbook format that produced this report."
}
```

No change to the `required` array (these fields are optional in the report schema — they can be null if a playbook predates the migration, but in practice the loader guarantees they're set).

- [ ] **Step 2: Add a validation test**

In `tests/test_utils_report.py`, add:

```python
def test_result_schema_accepts_playbook_metadata() -> None:
    import json
    import importlib.resources

    import jsonschema

    schema_text = (
        importlib.resources.files("regis.schemas.playbook")
        .joinpath("result.schema.json")
        .read_text(encoding="utf-8")
    )
    schema = json.loads(schema_text)

    report = {
        "playbook_name": "Test",
        "playbook_version": "1.2.3",
        "schema_version": 1,
        "score": 100,
        "total_scorecards": 1,
        "passed_scorecards": 1,
        "pages": [],
    }
    # Should not raise
    jsonschema.validate(instance=report, schema=schema)
```

- [ ] **Step 3: Run the test**

```bash
pipenv run pytest tests/test_utils_report.py::test_result_schema_accepts_playbook_metadata --no-cov -q
```

Expected: PASS.

- [ ] **Step 4: Run the full suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/schemas/playbook/result.schema.json tests/test_utils_report.py
git commit -m "feat(report): declare playbook_version and schema_version in result schema"
```

---

## Task 9: Update `regis playbook validate` CLI

**Goal:** The `validate` CLI subcommand reports the detected `schemaVersion` on success and gives the user a useful diagnostic on failure.

**Files:**
- Modify: `regis/commands/playbook.py`
- Modify: `tests/test_cli.py` (or equivalent CLI test file)

### Steps

- [ ] **Step 1: Inspect the current `validate` implementation**

Open `regis/commands/playbook.py` and read the `validate` command body (around line 30–60).

- [ ] **Step 2: Refactor `validate` to use the registry**

Replace the current path-based schema loading with `schema_registry.get_schema()`. On success, print the detected version. Example:

```python
from regis.playbook import schema_registry
from regis.playbook.loader import PlaybookVersionError, load_playbook


@click.command(name="validate")
@click.argument("path", type=click.Path(exists=True))
def validate_cmd(path: str) -> None:
    """Validate a playbook file or bundle against the JSON Schema."""
    try:
        pb = load_playbook(path)
    except PlaybookVersionError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # jsonschema.ValidationError, yaml.YAMLError, etc.
        raise click.ClickException(f"{path}: {exc}") from exc

    click.echo(
        f"  Validated '{path}' as schemaVersion={pb['schemaVersion']}, "
        f"version={pb['version']}. OK."
    )
```

(Adapt to the existing structure — preserve any `--strict` flag or output format already in place.)

- [ ] **Step 3: Add a CLI test**

In the appropriate test file (likely `tests/test_cli.py`):

```python
def test_playbook_validate_reports_schema_version(tmp_path) -> None:
    from click.testing import CliRunner

    from regis.cli import cli  # or wherever the root group is

    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(
        """
schemaVersion: 1
version: "1.2.3"
name: ValidatorTest
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["playbook", "validate", str(playbook)])
    assert result.exit_code == 0, result.output
    assert "schemaVersion=1" in result.output
    assert "version=1.2.3" in result.output


def test_playbook_validate_fails_on_missing_schema_version(tmp_path) -> None:
    from click.testing import CliRunner

    from regis.cli import cli

    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(
        """
version: "1.2.3"
name: NoSchemaVersion
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["playbook", "validate", str(playbook)])
    assert result.exit_code != 0
    assert "schemaVersion" in result.output
```

- [ ] **Step 4: Run the CLI tests**

```bash
pipenv run pytest tests/test_cli.py --no-cov -q -k playbook_validate
```

Expected: PASS.

- [ ] **Step 5: Run the full suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add regis/commands/playbook.py tests/test_cli.py
git commit -m "feat(cli): \`regis playbook validate\` reports detected schemaVersion"
```

---

## Task 10: Update the create-playbook skill scaffolding

**Goal:** The `/create-playbook` skill emits `schemaVersion: 1` + `version: 1.0.0` by default in any new playbook it scaffolds.

**Files:**
- Modify: `.claude/skills/create-playbook/SKILL.md` and any template files it references

### Steps

- [ ] **Step 1: Inspect the skill's scaffolding template**

```bash
ls -la .claude/skills/create-playbook/
cat .claude/skills/create-playbook/SKILL.md
```

Find the template fragment that emits the initial `playbook.yaml`.

- [ ] **Step 2: Insert the two fields at the top of the scaffolded YAML**

Wherever the skill's template renders the playbook, ensure it produces:

```yaml
schemaVersion: 1
version: "1.0.0"
name: {{ name }}
# … rest of the scaffold …
```

If the skill prompts the user for inputs, **do not** add a question for `schemaVersion` or `version` — both are auto-populated.

- [ ] **Step 3: Manually verify by invoking the skill (smoke test, optional)**

If feasible, walk through the skill once and check the output. Otherwise, code-review the template diff.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/create-playbook/
git commit -m "feat(skill): create-playbook scaffolds schemaVersion and version

New playbooks created via the skill ship with \`schemaVersion: 1\` and
\`version: 1.0.0\` by default."
```

---

## Task 11: Add the `regis playbook upgrade` helper (OPTIONAL — can be split off)

**Goal:** Convenience subcommand that injects `schemaVersion: 1` + `version: 1.0.0` into a legacy playbook, preserving YAML comments and formatting.

**Decision:** include in this plan, but if scope pressure mounts, drop and re-file as a follow-up. The migration guide must still work without it (manual edits documented).

**Files:**
- Modify: `regis/commands/playbook.py` (add `upgrade` subcommand)
- Modify: `Pipfile` / `pyproject.toml` (add `ruamel.yaml` dependency)
- Create: `tests/test_playbook_upgrade.py`

### Steps

- [ ] **Step 1: Add `ruamel.yaml` to project deps**

```bash
pipenv install ruamel.yaml
```

This updates `Pipfile` and `Pipfile.lock`. Also add to `pyproject.toml` under `[project.dependencies]` if not auto-synced.

- [ ] **Step 2: Write the upgrade test**

Create `tests/test_playbook_upgrade.py`:

```python
"""Tests for `regis playbook upgrade`."""

from __future__ import annotations

from click.testing import CliRunner

from regis.cli import cli


def test_upgrade_injects_missing_fields_preserving_comments(tmp_path) -> None:
    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(
        """# Important business context for this playbook
name: LegacyPlaybook
# Tiers come from compliance team
tiers:
  - name: Gold
    condition: { ">": [{ var: rules_summary.score }, 90] }
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["playbook", "upgrade", str(playbook)])
    assert result.exit_code == 0, result.output

    text = playbook.read_text(encoding="utf-8")
    assert "schemaVersion: 1" in text
    assert 'version: "1.0.0"' in text or "version: '1.0.0'" in text
    assert "# Important business context" in text  # comment preserved
    assert "# Tiers come from compliance team" in text  # comment preserved
    assert "name: LegacyPlaybook" in text


def test_upgrade_noop_when_fields_present(tmp_path) -> None:
    original = """schemaVersion: 1
version: "2.0.0"
name: AlreadyUpgraded
"""
    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["playbook", "upgrade", str(playbook)])
    assert result.exit_code == 0, result.output
    # Version unchanged
    assert playbook.read_text(encoding="utf-8") == original
```

- [ ] **Step 3: Run tests, expect failure**

```bash
pipenv run pytest tests/test_playbook_upgrade.py --no-cov -q
```

Expected: FAIL — `upgrade` subcommand doesn't exist.

- [ ] **Step 4: Implement the `upgrade` subcommand**

In `regis/commands/playbook.py`, add:

```python
@click.command(name="upgrade")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def upgrade_cmd(path: str) -> None:
    """Inject schemaVersion and version into a legacy playbook file.

    Preserves comments and formatting via ruamel.yaml. Idempotent: if both
    fields are already present, the file is left untouched.
    """
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(path, encoding="utf-8") as f:
        data = yaml.load(f)

    changed = False
    if "schemaVersion" not in data:
        # Insert at top
        data.insert(0, "schemaVersion", 1)
        changed = True
    if "version" not in data:
        # Insert after schemaVersion
        position = list(data.keys()).index("schemaVersion") + 1
        data.insert(position, "version", "1.0.0")
        changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        click.echo(f"  Upgraded {path}: schemaVersion + version added.")
    else:
        click.echo(f"  {path}: already at schemaVersion 1, nothing to do.")
```

Register the command on the `playbook` group (alongside `validate`).

- [ ] **Step 5: Run tests, expect pass**

```bash
pipenv run pytest tests/test_playbook_upgrade.py --no-cov -q
```

Expected: PASS.

- [ ] **Step 6: Run the full suite**

```bash
pipenv run pytest --no-cov -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add regis/commands/playbook.py tests/test_playbook_upgrade.py Pipfile Pipfile.lock pyproject.toml
git commit -m "feat(cli): add \`regis playbook upgrade\` to migrate legacy playbooks

Idempotent in-place rewrite: injects schemaVersion: 1 and version: 1.0.0 if
absent, preserves comments and formatting via ruamel.yaml."
```

---

## Task 12: Write public documentation

**Goal:** Reference doc for the new schema fields, plus an upgrade guide entry.

**Files:**
- Create: `docs/website/docs/reference/playbook-schema.md`
- Create or modify: `docs/website/docs/upgrade/playbook-schema-v1.md`

### Steps

- [ ] **Step 1: Write `playbook-schema.md`**

Create `docs/website/docs/reference/playbook-schema.md` with:

```markdown
---
sidebar_position: 5
---

# Playbook Schema Versioning

Every Regis playbook declares two version-related fields at its root:

| Field           | Type    | Required | Purpose                                                     |
| --------------- | ------- | -------- | ----------------------------------------------------------- |
| `schemaVersion` | integer | yes      | Identifies the format version of the playbook.              |
| `version`       | string  | yes      | SemVer of the playbook bundle (`MAJOR.MINOR.PATCH`).        |

## Example

\`\`\`yaml
schemaVersion: 1
version: "1.0.0"
name: My Playbook
…
\`\`\`

## `schemaVersion`

A monotonically increasing integer. Each bump is **breaking** — Regis ships
with a fixed set of supported `schemaVersion` values, and any playbook
declaring an unsupported value will fail to load with a clear error message.

Purely **additive** changes (new optional fields, new JSON Logic operators)
do **not** bump `schemaVersion`.

### Changelog

#### Version 1 (current)

Initial versioned schema. Includes: `name`, `description`, `slug`, `links`,
`integrations`, `rules`, `tiers`, `badges`. See the
[full definition.schema.json][schema] for the authoritative source.

[schema]: https://trivoallan.github.io/regis/schemas/playbook/v1/definition.schema.json

## `version`

A SemVer string (`MAJOR.MINOR.PATCH`, no pre-release or build metadata).
This is the version of **your playbook bundle**, independent from the
Regis binary version.

Suggested convention:

- **Major:** removed or renamed a rule.
- **Minor:** added a rule, tier, or badge.
- **Patch:** tweaked thresholds, descriptions, or labels.

Regis does not enforce this convention — only the format is validated.

## Error messages

\`\`\`text
PlaybookVersionError: playbook 'path/to/playbook.yaml' is missing required field 'schemaVersion'.
Add `schemaVersion: 1` at the top of the file.
Supported versions: [1].
\`\`\`

\`\`\`text
PlaybookVersionError: playbook 'path/to/playbook.yaml' declares schemaVersion=2 but this
regis (v0.33.0) only supports [1]. Upgrade regis or use a compatible playbook.
\`\`\`

## Migrating an existing playbook

See the [migration guide](../upgrade/playbook-schema-v1.md).
```

- [ ] **Step 2: Write the migration guide**

Create `docs/website/docs/upgrade/playbook-schema-v1.md` (or extend if a generic upgrade index exists):

```markdown
---
sidebar_position: 1
---

# Migrating to Playbook schemaVersion 1

Starting with the next minor release of Regis (Release Please will set
the exact tag at merge time — leave as "the upcoming release" in the doc
and let the release-notes template substitute the version), every playbook
must declare two top-level fields: `schemaVersion: 1` and `version: "1.0.0"`
(or another valid SemVer).

## Automated migration

If you have Regis vX.Y.Z installed locally:

\`\`\`bash
regis playbook upgrade path/to/playbook.yaml
\`\`\`

This injects the two fields, preserving your existing comments and
formatting. Idempotent: safe to re-run.

## Manual migration

Add the following two lines at the top of your `playbook.yaml`:

\`\`\`yaml
schemaVersion: 1
version: "1.0.0"
\`\`\`

`version` is your playbook's SemVer — bump it when you change rules
(see the [reference doc](../reference/playbook-schema.md) for conventions).

## Verifying

\`\`\`bash
regis playbook validate path/to/playbook.yaml
\`\`\`

A successful run prints `Validated 'path/to/playbook.yaml' as schemaVersion=1, version=1.0.0. OK.`
```

- [ ] **Step 3: Verify the doc renders**

If the Docusaurus dev server is convenient:

```bash
pnpm --filter @regis/dashboard start
```

Otherwise rely on the build step in CI.

- [ ] **Step 4: Update memory bank**

Per project convention (`docs/memory-bank/RULES.md`), update `activeContext.md` and `progress.md` with a one-line summary of this change.

- [ ] **Step 5: Commit**

```bash
git add docs/website/docs/reference/playbook-schema.md docs/website/docs/upgrade/playbook-schema-v1.md docs/memory-bank/
git commit -m "docs(playbook): add reference and migration guide for schemaVersion 1"
```

---

## Task 13: Open the PR

**Goal:** Push the branch and open a PR with a clear breaking-change note.

### Steps

- [ ] **Step 1: Rebase on the latest `main`** (per CLAUDE.md workflow)

```bash
git fetch origin main
git rebase origin/main
```

Resolve any conflicts (unlikely in this scope).

- [ ] **Step 2: Push**

```bash
git push -u origin tritri/exciting-northcutt-509246
```

- [ ] **Step 3: Open the PR**

```bash
gh pr create --title "feat(playbook)!: require schemaVersion and version + dispatch registry" --body "$(cat <<'EOF'
## Summary

- Adds two top-level required fields to the playbook format: `schemaVersion` (integer) and `version` (SemVer string).
- Introduces a versioned schema registry under `regis/schemas/playbook/v1/` and a dispatch table in `regis/playbook/schema_registry.py`.
- Loader (`regis/playbook/loader.py`) now hard-fails with a guiding `PlaybookVersionError` when `schemaVersion` is missing, malformed, or unsupported.
- Propagates `playbook_version` and `schema_version` into the playbook evaluation result for audit traceability.
- Ships `regis playbook upgrade` to migrate legacy playbooks in place (idempotent, preserves comments).
- Default playbook receives `schemaVersion: 1` and `version: 1.0.0`.
- Reference doc and migration guide added under `docs/website/docs/`.

## BREAKING CHANGE

Every playbook must now declare `schemaVersion: 1` and a SemVer-formatted `version`. Existing playbooks must be migrated either via `regis playbook upgrade` or by adding the two fields manually. See the [migration guide](docs/website/docs/upgrade/playbook-schema-v1.md).

## Test plan

- [x] Unit tests for schema registry, loader version dispatch, evaluator metadata propagation, result schema, CLI `validate`, CLI `upgrade`.
- [x] All in-tree playbook fixtures (default, docs snippets, test fixtures) migrated.
- [x] `pipenv run pytest` passes ≥ 90% coverage.
- [x] `pipenv run ruff check .` clean.
- [x] `trunk check` clean.
EOF
)"
```

Add the `whats-new` label if this should land in the What's New page (per CLAUDE.md, breaking schema changes qualify as user-facing).

- [ ] **Step 4: Report the PR URL back**

The PR URL is the deliverable for this plan.

---

## Self-review notes

This plan was written against [`docs/superpowers/specs/2026-05-31-playbook-versioning-design.md`](../specs/2026-05-31-playbook-versioning-design.md). Each spec requirement is covered:

| Spec requirement                                                | Covered by    |
| --------------------------------------------------------------- | ------------- |
| Two required top-level fields (`schemaVersion`, `version`)      | Task 5        |
| Top-level placement                                             | Task 5        |
| Integer `schemaVersion`, SemVer `version`                       | Task 5        |
| Hard fail on missing/unknown `schemaVersion`                    | Task 6        |
| Schema registry under `v1/`                                     | Tasks 1, 4    |
| Loader dispatches via registry                                  | Task 6        |
| Migration without grace period (in-tree fixtures pre-migrated)  | Tasks 2, 3    |
| Report propagation (`playbook_version`, `schema_version`)       | Tasks 7, 8    |
| CLI `validate` reports `schemaVersion`                          | Task 9        |
| `regis playbook upgrade` helper                                 | Task 11       |
| Default playbook ships with new fields                          | Task 2        |
| `create-playbook` skill scaffolds new fields                    | Task 10       |
| Reference doc + migration guide                                 | Task 12       |
| PR with `feat(playbook)!:` + BREAKING CHANGE                    | Task 13       |

**Note on regis binary version in the report:** the spec called for `metadata.regis.version`. Investigation in Task 0 (pre-plan) confirmed that the existing top-level `version` field in `analysis_report` (set in `regis/commands/analyze.py:612`) already carries the regis binary version. This plan therefore preserves that field as-is and does not introduce a nested `metadata.regis` structure, avoiding a breaking change for dashboard consumers. The playbook-level fields (`playbook_version`, `schema_version`) live alongside `playbook_name` in the playbook result, matching the existing flat shape.
