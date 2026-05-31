# Dashboard Decouple — Phase 0: report `schemaVersion` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a required integer `schemaVersion` field to the regis `report.json` envelope so a future standalone `regis-dashboard` can detect compatibility at runtime.

**Architecture:** Add `schemaVersion` (integer, ≥1) to the report JSON Schema as a required property. Stamp every freshly-produced report with `REPORT_SCHEMA_VERSION = 1`. Backfill the field on the two paths that load pre-existing reports (`--rerun` and `evaluate`) so legacy reports still validate. Ship a versioned contract fixture (`tests/fixtures/report.v1.json`) that the future dashboard repo's CI will fetch and render-test.

**Tech Stack:** Python 3.10+, Click, `jsonschema` + `referencing`, pytest. This is the non-breaking core prerequisite (Phase 0) from `docs/superpowers/specs/2026-05-31-dashboard-full-decouple-design.md`. Phases 1–3 (new repo, core removal, docs) get their own plans.

---

## Scope & boundaries

This plan covers **only Phase 0** of the full-decouple design. It is intentionally non-breaking: it adds a field, it removes nothing. It does **not** touch the dashboard, `ToolFetcher`, `tools/manifest.yaml`, or any CLI surface that will later be deleted.

**Distinct fields — do not conflate:**

- `version` — existing, string-or-null, the regis package version / snapshot date. **Unchanged.**
- `snapshot_date` — existing, ISO date. **Unchanged.**
- `schemaVersion` — **new**, integer ≥1, the report-structure contract version. This plan adds only this.

## File Structure

| File                                      | Responsibility                                                        | Action                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `regis/schemas/report/report.schema.json` | Report envelope JSON Schema                                           | Modify — add `schemaVersion` property + mark required                            |
| `regis/utils/report.py`                   | Report helpers (`validate_report`, etc.)                              | Modify — add `REPORT_SCHEMA_VERSION` constant + `ensure_schema_version()` helper |
| `regis/commands/analyze.py`               | `analyze` / `evaluate` commands; the report producer                  | Modify — stamp producer + backfill the two load paths                            |
| `tests/test_report_schema_version.py`     | Schema + helper unit tests                                            | Create                                                                           |
| `tests/fixtures/report.v1.json`           | Cross-repo contract fixture (consumed by future `regis-dashboard` CI) | Create                                                                           |
| `tests/test_analyze_rerun.py`             | Existing rerun integration tests                                      | Modify — add a real-validation backfill test                                     |

The root of `report.schema.json` is `"additionalProperties": false`, so the schema change (Task 1) is a hard prerequisite for the producer change — a report stamped with `schemaVersion` will **fail** validation until the schema permits the field. TDD order below respects this.

---

### Task 1: Add `schemaVersion` to the report schema

**Files:**

- Modify: `regis/schemas/report/report.schema.json` (root `properties` ~line 8, root `required` line 7)
- Test: `tests/test_report_schema_version.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_report_schema_version.py`:

```python
"""Schema and helper tests for the report schemaVersion contract (Phase 0)."""

import importlib.resources
import json

import jsonschema
import pytest


def _report_schema() -> dict:
    text = (
        importlib.resources.files("regis.schemas.report")
        .joinpath("report.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def _minimal_report(**overrides) -> dict:
    """A report with no playbooks/rules so no $ref resolution is triggered."""
    report = {
        "schemaVersion": 1,
        "version": "0.33.0",
        "request": {
            "url": "registry-1.docker.io/library/nginx:latest",
            "registry": "registry-1.docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "analyzers": ["metadata"],
            "timestamp": "2026-05-31T00:00:00+00:00",
        },
        "results": {"metadata": {}},
    }
    report.update(overrides)
    return report


class TestReportSchemaVersion:
    def test_accepts_report_with_schema_version(self):
        jsonschema.validate(instance=_minimal_report(), schema=_report_schema())

    def test_rejects_report_missing_schema_version(self):
        report = _minimal_report()
        del report["schemaVersion"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=report, schema=_report_schema())

    def test_rejects_non_integer_schema_version(self):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                instance=_minimal_report(schemaVersion="1"),
                schema=_report_schema(),
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/test_report_schema_version.py -v --no-cov`
Expected: `test_accepts_report_with_schema_version` FAILS (schema's `additionalProperties: false` rejects the unknown `schemaVersion` key); the two rejection tests may pass for the wrong reason. All three must pass after Step 3.

- [ ] **Step 3: Edit the schema**

In `regis/schemas/report/report.schema.json`, change the root `required` array (currently line 7):

```json
  "required": ["schemaVersion", "request", "results", "version"],
```

Add the `schemaVersion` property as the first entry of the root `properties` object (before `"version"` at line 9):

```json
    "schemaVersion": {
      "type": "integer",
      "minimum": 1,
      "description": "Report-structure contract version. Consumers (e.g. the standalone dashboard) gate rendering on this. Distinct from `version` (package/snapshot)."
    },
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_report_schema_version.py -v --no-cov`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add regis/schemas/report/report.schema.json tests/test_report_schema_version.py
git commit -m "feat(schema)!: require schemaVersion on report envelope"
```

---

### Task 2: Add the `REPORT_SCHEMA_VERSION` constant and `ensure_schema_version()` helper

**Files:**

- Modify: `regis/utils/report.py` (add constant near the top of the module, after imports; add helper near `validate_report` at line 235)
- Test: `tests/test_report_schema_version.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_report_schema_version.py`:

```python
class TestEnsureSchemaVersion:
    def test_constant_is_one(self):
        from regis.utils.report import REPORT_SCHEMA_VERSION

        assert REPORT_SCHEMA_VERSION == 1

    def test_sets_when_missing(self):
        from regis.utils.report import REPORT_SCHEMA_VERSION, ensure_schema_version

        report = {"request": {}, "results": {}}
        result = ensure_schema_version(report)

        assert result is report  # mutates in place and returns it
        assert report["schemaVersion"] == REPORT_SCHEMA_VERSION

    def test_preserves_existing_value(self):
        from regis.utils.report import ensure_schema_version

        report = {"schemaVersion": 7, "request": {}, "results": {}}
        ensure_schema_version(report)

        assert report["schemaVersion"] == 7
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pipenv run pytest tests/test_report_schema_version.py::TestEnsureSchemaVersion -v --no-cov`
Expected: FAIL with `ImportError: cannot import name 'REPORT_SCHEMA_VERSION'`.

- [ ] **Step 3: Add the constant and helper**

In `regis/utils/report.py`, add the constant after the module imports (before the first function, `format_output_path` at line 19):

```python
REPORT_SCHEMA_VERSION = 1
"""Current report-structure contract version (see report.schema.json)."""
```

Add the helper immediately before `def validate_report(` (line 235):

```python
def ensure_schema_version(report: dict[str, Any]) -> dict[str, Any]:
    """Stamp `schemaVersion` on a report if absent. Backfills legacy reports.

    Mutates `report` in place and returns it. Existing values are preserved so a
    future report carrying a higher version is never silently downgraded.
    """
    report.setdefault("schemaVersion", REPORT_SCHEMA_VERSION)
    return report
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pipenv run pytest tests/test_report_schema_version.py::TestEnsureSchemaVersion -v --no-cov`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add regis/utils/report.py tests/test_report_schema_version.py
git commit -m "feat(report): add REPORT_SCHEMA_VERSION constant and ensure_schema_version helper"
```

---

### Task 3: Stamp the producer and backfill the two load paths

**Files:**

- Modify: `regis/commands/analyze.py` (producer ~line 611; rerun load ~line 393; evaluate load ~line 797)
- Test: `tests/test_analyze_rerun.py` (append a real-validation backfill test)

**Context — three sites in `analyze.py`:**

1. **Producer** (~line 611) builds a fresh report dict literal starting with `"version": version("regis")`. Add `schemaVersion` here.
2. **Rerun load** (~line 393): an existing `report.json` is read from disk, mutated (`existing_report.setdefault("results", {})[rerun] = result`), then `validate_report(rerun_report)` runs at ~line 408. A legacy report lacking `schemaVersion` would now fail that validation — backfill first.
3. **Evaluate load** (~line 797): `if "results" in data: analysis_report = data` reads an existing report, then `validate_report(final_report)` runs at ~line 814. Same backfill need.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_analyze_rerun.py` (this test does **not** mock `validate_report` — it proves backfill lets a legacy report survive real validation):

```python
class TestRerunBackfillsSchemaVersion:
    """A legacy report (no schemaVersion) flows through --rerun under real validation."""

    @patch("regis.commands.analyze._discover_analyzers")
    def test_rerun_backfills_schema_version(self, mock_discover):
        mock_discover.return_value = {"metadata": MetadataAnalyzer}

        legacy_report = {
            "version": "0.1.0",
            "request": {
                "url": "r/repo:latest",
                "registry": "r",
                "repository": "repo",
                "tag": "latest",
                "analyzers": ["metadata"],
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            "results": {},
        }

        runner = CliRunner()
        with runner.isolated_filesystem():
            report_dir = Path("my_report")
            report_dir.mkdir()
            (report_dir / "report.json").write_text(
                json.dumps(legacy_report), encoding="utf-8"
            )

            result = runner.invoke(
                main,
                ["analyze", "--rerun", "metadata", "--report", str(report_dir),
                 "-m", "PROJECT_ID=PROJ-42"],
            )

            assert result.exit_code == 0, result.output
            updated = json.loads(
                (report_dir / "report.json").read_text(encoding="utf-8")
            )
            assert updated["schemaVersion"] == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pipenv run pytest tests/test_analyze_rerun.py::TestRerunBackfillsSchemaVersion -v --no-cov`
Expected: FAIL — either `validate_report` raises (missing required `schemaVersion`) giving a non-zero exit, or `updated["schemaVersion"]` raises `KeyError`.

- [ ] **Step 3: Stamp the producer**

In `regis/commands/analyze.py`, add `schemaVersion` as the first key of the producer dict (~line 611, currently `analysis_report = {` followed by `"version": version("regis"),`):

```python
        analysis_report = {
            "schemaVersion": REPORT_SCHEMA_VERSION,
            "version": version("regis"),
            "request": {
```

- [ ] **Step 4: Backfill the two load paths**

Update the existing `from regis.utils.report import (...)` block (line 24) to add the two new names. The resulting block (ruff will finalize member ordering on `ruff format`):

```python
from regis.utils.report import (
    REPORT_SCHEMA_VERSION,
    ensure_schema_version,
    format_output_path,
    render_and_save_reports,
    render_mr_templates,
    run_playbooks,
    set_nested_value,
    validate_report,
)
```

In the **rerun** path, the report read from disk is built into `rerun_report` by `run_playbooks(...)` (~line 404-406). Insert the backfill on the line **between** that assignment and `validate_report(rerun_report)` (~line 408):

```python
        rerun_report = run_playbooks(
            playbook_paths, existing_report, formats, show_rules=evaluate
        )
        ensure_schema_version(rerun_report)
        validate_report(rerun_report)
```

In the **evaluate** path, insert the backfill immediately after `analysis_report = data` (~line 798). `run_playbooks` shallow-copies `analysis_report` into `final_report`, so the stamped key flows through to `validate_report(final_report)` at ~line 814:

```python
    if "results" in data:
        analysis_report = data
        ensure_schema_version(analysis_report)
    else:
```

- [ ] **Step 5: Run the new test and the full rerun suite**

Run: `pipenv run pytest tests/test_analyze_rerun.py -v --no-cov`
Expected: all pass, including `TestRerunBackfillsSchemaVersion`.

- [ ] **Step 6: Commit**

```bash
git add regis/commands/analyze.py tests/test_analyze_rerun.py
git commit -m "feat(report): stamp schemaVersion on produced reports and backfill on load"
```

---

### Task 4: Ship the cross-repo contract fixture

**Files:**

- Create: `tests/fixtures/report.v1.json`
- Test: `tests/test_report_schema_version.py` (append)

This fixture is the **only file-level dependency** the future `regis-dashboard` repo will have on the core: its CI fetches this pinned file and asserts the dashboard renders it. It must be a realistic, schema-valid report at `schemaVersion: 1`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_report_schema_version.py`:

```python
class TestContractFixture:
    def test_fixture_validates_against_real_validator(self):
        import json
        from pathlib import Path

        from regis.utils.report import validate_report

        fixture = Path(__file__).parent / "fixtures" / "report.v1.json"
        report = json.loads(fixture.read_text(encoding="utf-8"))

        assert report["schemaVersion"] == 1
        validate_report(report)  # must not raise
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pipenv run pytest tests/test_report_schema_version.py::TestContractFixture -v --no-cov`
Expected: FAIL — `FileNotFoundError` (fixture does not exist yet).

- [ ] **Step 3: Create the fixture**

Create `tests/fixtures/report.v1.json`:

```json
{
  "schemaVersion": 1,
  "version": "0.33.0",
  "snapshot_date": "2026-05-31",
  "tier": "Gold",
  "request": {
    "url": "registry-1.docker.io/library/nginx:1.27",
    "registry": "registry-1.docker.io",
    "repository": "library/nginx",
    "tag": "1.27",
    "digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "analyzers": ["metadata", "cve"],
    "timestamp": "2026-05-31T12:00:00+00:00"
  },
  "results": {
    "metadata": { "created": "2026-05-20T00:00:00+00:00" },
    "cve": { "critical": 0, "high": 1, "medium": 4, "low": 12 }
  },
  "rules": [
    {
      "slug": "no-critical-cve",
      "description": "No critical CVEs",
      "level": "Gold",
      "tags": ["security"],
      "passed": true,
      "status": "passed",
      "message": "0 critical vulnerabilities found",
      "analyzers": ["cve"]
    }
  ],
  "rules_summary": {
    "score": 100,
    "total": ["no-critical-cve"],
    "passed": ["no-critical-cve"],
    "by_tag": {
      "security": {
        "rules": ["no-critical-cve"],
        "passed_rules": ["no-critical-cve"],
        "score": 100
      }
    }
  }
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pipenv run pytest tests/test_report_schema_version.py::TestContractFixture -v --no-cov`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/report.v1.json tests/test_report_schema_version.py
git commit -m "test(report): add report.v1 cross-repo contract fixture"
```

---

### Task 5: Full-suite verification and coverage gate

**Files:** none (verification only)

- [ ] **Step 1: Run the full suite with coverage**

Run: `pipenv run pytest`
Expected: all tests pass; coverage ≥ 90% (the project gate). The new constant/helper/producer lines are all exercised by Tasks 1–4.

- [ ] **Step 2: Lint and format**

Run: `pipenv run ruff check . && pipenv run ruff format --check .`
Expected: no errors.

- [ ] **Step 3: If anything fails, fix and re-run**

Diagnose with `superpowers:systematic-debugging` if a failure is non-obvious. Common surprise: an unrelated existing test asserts on a full report dict and now sees an extra `schemaVersion` key — update that assertion to include it. Do **not** weaken the schema or remove the field.

- [ ] **Step 4: Final commit (only if Step 3 made changes)**

```bash
git add -A
git commit -m "test(report): align existing assertions with schemaVersion field"
```

---

## Self-review notes (already reconciled against the spec)

- **Spec "Phase 0" bullet 1** (add `schemaVersion: 1` to schema + producers + tests) → Tasks 1, 2, 3.
- **Spec "Phase 0" bullet 2** (version contract fixtures `tests/fixtures/report.v1.json`) → Task 4.
- **Spec "distinct from `version`"** → enforced in Task 1 description and the fixture (both fields present, different values).
- **Spec "schemaVersion absent → treat as 0" (dashboard-side)** → intentionally **not** in this plan; that logic lives in the future dashboard repo (Phase 1), not the core. The core _backfills to 1_ on its own load paths (legacy reports it produced were structurally v1); it never emits 0.
- **Breaking-change note:** making `schemaVersion` required is schema-breaking for any external consumer that validates its own `report.json` against `report.schema.json`, so Task 1 commits with `feat(schema)!` (matching the [#626](https://github.com/trivoallan/regis/pull/626) `feat(playbook)!: require schemaVersion` precedent). regis itself stays user-facing-compatible because every core path stamps or backfills the field. Release-mechanics consequence: with `bump-minor-pre-major: true`, this `!` cuts a **pre-major minor** bump (0.32 → 0.33) when Phase 0 merges. Phase 2's removal then becomes the next bump (→ 0.34). The design doc's "0.33" label refers to the overall effort; the actual numbers fall out of merge order.

## Out of scope (later phases — do not implement here)

- Removing `regis dashboard` / `--site` / `bootstrap archive` (Phase 2).
- The new `regis-dashboard` repo, its CI, and the render-side compatibility check (Phase 1).
- Adding a `decisionLog.md` entry and updating `activeContext.md` / `progress.md` (Phase 3 / Memory-Bank update).

## Implementation deviations (recorded post-execution, 2026-05-31)

Two justified departures from the literal plan surfaced during subagent-driven execution and code review:

1. **Three report-load paths, not two.** Task 3 as written named the `--rerun` and `evaluate` load paths. A **third** path exists: the **cache-hit** path in `analyze.py` (`final_report = json.loads(cache_path.read_text(...))` inside `if cache_path.exists():`), which feeds `validate_report` at the main call site. A legacy cached `report.json` would have failed the now-required field. `ensure_schema_version(final_report)` was added there too. A code-reviewer grep confirmed `validate_report` has exactly three call sites and all are now covered; the other report readers (`commands/archive.py`, `rules.py`, the gh/gitlab CLIs) never validate, so they are not gaps.

2. **Contract fixture made schema-honest.** The plan's `tests/fixtures/report.v1.json` used invented `results.metadata` / `results.cve` payloads. Because this fixture is the cross-repo render contract, the blobs were replaced with minimal payloads that validate against the real `regis/schemas/analyzer/oci.schema.json` and `cve.schema.json` (slugs `oci` + `cve`, `request.analyzers: ["cve", "oci"]`), and `TestContractFixture` gained `test_analyzer_blobs_match_their_schemas` to lock that honesty against drift.

**Final state:** 5 task commits on the branch; full suite `626 passed`, coverage `91.18%`; `trunk check` reports no new issues on all changed files. Pre-existing, unrelated lint in untouched files (`regis/report/html.py` unused `json`; `ruff format` drift in two test files) was deliberately left out of scope.
