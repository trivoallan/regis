# Playbook versioning — design

**Date:** 2026-05-31
**Status:** Draft (pending user review)
**Scope:** Add explicit version fields to the playbook format to manage compatibility with future Regis changes and to enable audit traceability.

## Problem

Today, `regis/schemas/playbook/definition.schema.json` carries **no version information**. A playbook authored against today's Regis can fail in subtle, hard-to-diagnose ways when consumed by a different Regis version (forward or backward), and reports produced by `regis analyze` cannot be unambiguously attributed to a specific playbook revision.

Four scenarios need protection:

1. **Old Regis, recent playbook** — playbook references a field, operator, or rule template that does not yet exist in the older binary.
2. **Recent Regis, old playbook** — playbook uses a deprecated field or a rule option whose signature has changed.
3. **Rule/analyzer signature drift** — the global schema is unchanged, but a rule template's options shape changes underneath.
4. **Audit traceability** — given a report, identify which playbook (name + version) and which Regis binary produced it.

The current loader (`regis/playbook/loader.py:18`) is a thin YAML/JSON read; there is no point at which compatibility is checked.

## Decisions

| Axis | Decision |
| --- | --- |
| Versioning axes modeled | **Schema version** (format identifier) **and bundle version** (SemVer of the playbook itself). Regis app compat range and per-rule/analyzer fine-grained compat are explicitly out of scope. |
| Field placement | **Top-level keys** in `playbook.yaml`. No separate manifest file. |
| `schemaVersion` format | **Integer** (`1`, `2`, …). Each bump is breaking. |
| `version` format | **SemVer strict**, validated by a regex pattern (see "Schema fields" below for the exact pattern). |
| Both fields | **Required.** |
| Behavior on missing or unknown `schemaVersion` | **Hard fail** with an explicit, guiding error message. |
| Migration policy | **Hard fail on day 1** — no grace period. Pre-migrate every in-tree playbook (default, examples, fixtures) in the same PR that flips the field to required. Pre-v1 stage of Regis legitimizes the bold cut. |
| Report propagation | Inject `playbook.{name, version, schemaVersion}` and `regis.version` into the report metadata. |
| Architecture | **Schema registry** under `regis/schemas/playbook/v1/` with a dispatch table in a new `regis/playbook/schema_registry.py`. Each future bump = a new sibling directory + a new entry in the table, zero displacement of existing files. |

## Architecture

### 1. Schema fields

`regis/schemas/playbook/v1/definition.schema.json` gains:

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

The `required` array becomes `["schemaVersion", "version", "name"]`.

Bump semantics:

- **`schemaVersion`** bumps when a change is breaking (field removed, renamed, type or semantics changed). Purely **additive** changes (new optional fields, new JSON Logic operators) do **not** bump. Each version of the schema gets a dedicated changelog section in `docs/website/docs/reference/playbook-schema.md`.
- **`version`** is opaque to Regis — only the SemVer pattern is enforced. Discipline (major = removed rule, minor = added rule, patch = tweak) is documented as a convention but not validated.

### 2. File layout

```text
regis/schemas/playbook/
  __init__.py
  jsonlogic.schema.json          # shared, root-level
  result.schema.json             # report (not playbook-versioned)
  v1/
    __init__.py
    definition.schema.json       # current contents + new required fields
```

- `definition.schema.json` moves into `v1/`. Its `$id` becomes `https://trivoallan.github.io/regis/schemas/playbook/v1/definition.schema.json`.
- `$ref` to `jsonlogic.schema.json` is rewritten as `../jsonlogic.schema.json`. The shared file stays at the root until a future version of it diverges.
- The GitHub Pages publication mirrors the on-disk tree — no redirection from the old URL is set up (consistent with the hard-fail stance).
- `meta.schema.json` inside bundles (used for `inputs` validation) is **not** versioned at this stage; revisit if a breakage need surfaces.

### 3. Loader and validation flow

New module `regis/playbook/schema_registry.py`:

```python
SCHEMAS: dict[int, dict] = {1: _load_v1()}   # memoized lazy load
def get_schema(schema_version: int) -> dict: ...
def supported_versions() -> list[int]: ...
```

Updated `regis/playbook/loader.py`:

```python
class PlaybookVersionError(ValueError):
    """Raised when schemaVersion is missing, malformed, or unsupported."""

def load_playbook(path: str | Path) -> dict[str, Any]:
    raw = _read_raw(path)                                # YAML/JSON parsing only
    schema_version = _extract_schema_version(raw, path)  # hard fail if missing/wrong type
    schema = schema_registry.get_schema(schema_version)  # hard fail if unknown
    _validate(raw, schema, path)                          # jsonschema.validate
    return raw
```

Three error gates, each with a guiding message:

1. **`schemaVersion` missing or not an integer.**
   ```text
   PlaybookVersionError: playbook 'path/to/playbook.yaml' is missing required field 'schemaVersion'.
   Add `schemaVersion: 1` at the top of the file.
   Supported versions: [1].
   ```
2. **`schemaVersion` unknown.**
   ```text
   PlaybookVersionError: playbook 'path/to/playbook.yaml' declares schemaVersion=2 but this
   regis (v0.33.0) only supports [1]. Upgrade regis or use a compatible playbook.
   ```
3. **JSON Schema validation failure.** Standard `jsonschema` message, prefixed with the playbook path and the dispatched `schemaVersion`.

`_extract_schema_version()` runs before JSON Schema validation — it only checks that the key exists, is an integer, and is dispatched. Everything else stays under `jsonschema.validate`.

The URL loader (`http://`, `https://`) and the bundle loader (directory containing `playbook.yaml`) reuse the exact same flow — no special case.

The CLI `regis playbook validate` switches to `schema_registry.get_schema()` and prints the detected `schemaVersion` in its success output (`Validated as schemaVersion=1, OK`).

### 4. Report propagation

`regis/schemas/playbook/result.schema.json` is extended with a `metadata` object (enrich it if it already exists):

```json
"metadata": {
  "type": "object",
  "required": ["regis", "playbook"],
  "properties": {
    "regis": {
      "type": "object",
      "required": ["version"],
      "properties": {
        "version": { "type": "string" }
      }
    },
    "playbook": {
      "type": "object",
      "required": ["name", "version", "schemaVersion"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string", "pattern": "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$" },
        "schemaVersion": { "type": "integer", "minimum": 1 }
      }
    }
  }
}
```

In `regis/utils/report.py`, before writing the report:

```python
report["metadata"]["regis"] = {"version": importlib.metadata.version("regis")}
report["metadata"]["playbook"] = {
    "name": playbook["name"],
    "version": playbook["version"],
    "schemaVersion": playbook["schemaVersion"],
}
```

**Audit verification needed during implementation:** the existing `version` field in `result.schema.json` must be confirmed to refer to the report schema version (not the playbook). If it currently refers to the playbook, rename it to avoid semantic collision.

**Dashboard UI** (`apps/dashboard/`) is out of scope for this spec but earmarked as a natural follow-up: surface `regis vX.Y.Z` and `playbook name@X.Y.Z` pastilles next to the existing navbar identity badges.

**Backward compatibility of old reports:** propagation happens at write time, so no read-side compat is required. Consumers reading legacy reports without the `metadata` block display "unknown" defensively.

### 5. Migration

Single PR, two ordered commits so the test suite stays green at every step:

**Commit 1 — Migrate in-tree playbooks.** Add `schemaVersion: 1` + `version: 1.0.0` to:

- `regis/playbooks/default/playbook.yaml` — first version under the new regime is `1.0.0` (independent cadence from Regis itself; called out in the release notes).
- All playbook YAML/JSON files under `docs/website/docs/**` and `docs/website/blog/**`, plus inline snippets in Markdown.
- All test fixtures under `tests/**` that load a playbook.
- The scaffolding in `.claude/skills/create-playbook/` so new playbooks ship with both fields by default. No new user-facing question — `version` initializes to `1.0.0` automatically.

**Commit 2 — Enforce.** Land the schema/loader changes that make both fields `required` and dispatch through the registry.

**Documentation:**

- New (or enriched) `docs/website/docs/reference/playbook-schema.md` describing `schemaVersion` (integer, bump = breaking) and `version` (SemVer of the bundle), with a per-version changelog.
- Upgrade guide entry under `docs/website/docs/upgrade/`: "Migrating to schemaVersion 1" — covers the optional `regis playbook upgrade` helper (below) and the manual edit path.

**Conventional Commits.** PR is `feat(playbook)!:` (breaking change) — Release Please bumps minor pre-v1 (`bump-minor-pre-major: true` is already on). The PR body includes an explicit `BREAKING CHANGE:` footer.

**Open question — `regis playbook upgrade` helper.** Recommended (in-scope) but droppable to a follow-up:

- Minimal scope: read playbook YAML, inject `schemaVersion: 1` and `version: 1.0.0` if absent, write back preserving comments via `ruamel.yaml`. ~30 lines + tests.
- Massively eases migration for clients with playbooks in CI ("we can pipe through `regis playbook upgrade` to auto-fix").

### 6. Tests

**`tests/playbook/test_loader.py`** (create or extend):

1. `test_load_playbook_v1_valid` — minimal valid v1 playbook returns parsed dict.
2. `test_load_playbook_missing_schema_version` — raises `PlaybookVersionError`; message mentions `schemaVersion`, `Add schemaVersion: 1`, and the supported versions list.
3. `test_load_playbook_schema_version_not_integer` (`"1"`, `1.0`, `null`) — raises.
4. `test_load_playbook_unknown_schema_version` (`99`) — raises, message lists `[1]`.
5. `test_load_playbook_missing_version_field` — JSON Schema validation error with path `/version`.
6. `test_load_playbook_invalid_semver` (`"1.2"`, `"v1.2.3"`, `"1.2.3-rc1"`) — validation error, mentions pattern.
7. `test_load_playbook_from_bundle_directory` — same flow inside a bundle dir.
8. `test_load_playbook_from_url` — mocked `requests`, same flow.

**`tests/playbook/test_schema_registry.py`** (create):

9. `test_get_schema_v1_returns_dict` — `v1/definition.schema.json` is loadable and well-formed.
10. `test_supported_versions_lists_known_schemas` — returns `[1]`.
11. `test_get_schema_unknown_raises_key_error` — contract: registry raises `KeyError`, loader translates to `PlaybookVersionError` with context.

**`tests/utils/test_report.py`** (extend):

12. `test_write_report_includes_playbook_metadata` — asserts `report.metadata.playbook == {name, version, schemaVersion}`.
13. `test_write_report_includes_regis_version` — asserts equality with `importlib.metadata.version("regis")`.
14. `test_result_schema_validates_with_new_metadata` — generated report validates against the updated `result.schema.json`.

**CLI:**

15. `test_playbook_validate_reports_schema_version` — `regis playbook validate` output mentions `schemaVersion: 1`.
16. (Conditional on `upgrade` helper landing) `test_playbook_upgrade_adds_missing_fields_preserving_comments`.

**Default playbook regression guard:**

17. `test_default_playbook_passes_validation` — extend any existing equivalent to assert `schemaVersion == 1` and `version` matches the pattern.

The project's 90% coverage bar (`pipenv run pytest` in CI mode) is preserved: the additions cover the new code paths linearly with no risk of degradation.

## Out of scope

- **Regis app compatibility range** (`regis: "^0.32"` style) on the playbook side — explicitly excluded; the `schemaVersion` is the global compatibility lever.
- **Fine-grained per-rule / per-analyzer compatibility** declarations.
- **Hybrid manifest file** (`regis.yaml` alongside `playbook.yaml`) — top-level keys in `playbook.yaml` are sufficient.
- **Dashboard UI** changes to surface the new metadata — earmarked as a follow-up.
- **`meta.schema.json` (bundle inputs) versioning** — revisit if a breakage need surfaces.

## Risks and mitigations

| Risk                                                                                                               | Mitigation                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| External clients with custom playbooks break the moment they upgrade Regis.                                        | Ship `regis playbook upgrade` helper + clear upgrade guide. The breaking change is announced in release notes and reflected in the SemVer minor bump (pre-v1).                                                                                   |
| Future churn of `jsonlogic.schema.json` requires it to live under `v1/` after all.                                 | Pre-commit to a copy/duplication strategy if it diverges, rather than aliasing. Out of scope today.                                                                                                                                              |
| Existing `version` field in `result.schema.json` collides semantically with the new propagated `playbook.version`. | Audit during implementation; rename if needed (likely to `report_schema_version` or move under `metadata.report`).                                                                                                                               |
| Tests of the loader currently assume the old loader contract (no version checks).                                  | The loader change is centralized in `regis/playbook/loader.py` and the new `regis/playbook/schema_registry.py`. All in-tree playbook fixtures are co-migrated in commit 1 (see Migration), so commit 2 sees a green suite with the new contract. |

## Acceptance criteria

- `regis analyze --playbook <bundle-without-schemaVersion>` exits non-zero with the documented guiding error.
- `regis analyze --playbook <bundle-with-schemaVersion: 1 + valid version>` produces a report whose `metadata.regis.version` and `metadata.playbook.{name, version, schemaVersion}` are populated.
- `regis playbook validate <bundle>` reports the detected `schemaVersion`.
- The default playbook ships with `schemaVersion: 1` and `version: 1.0.0`.
- `pipenv run pytest` passes at ≥ 90% coverage.
- Docs include a per-version changelog and an upgrade guide entry.
