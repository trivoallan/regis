# Analyzer source freshness metadata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generic optional `source` block (freshness/provenance of each analyzer's external data source) to all analyzer schemas — populated by cve (grype DB), scorecarddev (assessment), popularity (Docker Hub) — and remove the misleading `snapshot_date` editorial marker, bumping `REPORT_SCHEMA_VERSION` 4 → 5.

**Architecture:** Each analyzer result schema declares an identical optional `source` object (`fetched_at` / `built_at` / `version` / `checksum`); a consistency test guarantees the shape is uniform across schemas (no cross-file `$ref`, because per-analyzer validation in `base.py` uses a bare `jsonschema.validate` with no registry). The HTML report renders the source freshness per-analyzer (detail mode already does so generically via `render_detail`; compact mode gets an explicit line). `snapshot_date` is deleted from the schema, the data file, the injection path, and both renderers.

**Tech Stack:** Python 3, `jsonschema` + `referencing`, pytest (with global ≥ 90 % and per-file ≥ 90 % coverage gates), Jinja2 HTML template, ruff/trunk.

**Reference spec:** `docs/superpowers/specs/2026-06-10-analyzer-source-metadata-design.md`

**Conventions:** Conventional Commits with mandatory scope (`analyzers`, `report`). Use `pipenv run pytest --no-cov` for fast loops; run the full suite before the final task. Trunk's pre-commit hook auto-formats — re-stage and include produced changes.

---

## File Structure

**Schemas (declare `source`):**
- `regis/schemas/analyzer/{cve,dockle,endoflife,freshness,hadolint,oci,popularity,provenance,sbom,scorecarddev,secrets,size,versioning}.schema.json` — add identical optional `source` property. `popularity` additionally drops `last_updated`.
- `regis/schemas/report/report.schema.json` — remove `snapshot_date` property.

**Analyzers (emit `source`):**
- `regis/analyzers/cve.py` — emit `source` from `descriptor.db.status`.
- `regis/analyzers/scorecarddev.py` — emit `source` from API `date` + `scorecard.version`.
- `regis/analyzers/popularity.py` — emit `source.built_at` (migrated from `last_updated`), drop top-level `last_updated`.

**Report core / rendering:**
- `regis/utils/report.py` — bump `REPORT_SCHEMA_VERSION`; remove markdown `Snapshot date` line.
- `regis/commands/analyze.py` — remove the `snapshot_date` injection block.
- `regis/templates/html/report.html.j2` — remove `Snapshot date` header rows; add compact-mode per-analyzer source line.
- `regis/data/snapshot_dates.json` — delete.

**Tests:**
- New: `tests/schemas/test_source_block_consistency.py`.
- Modify: `tests/test_analyzer_cve.py` (or nearest cve test), `tests/test_scorecarddev.py`, `tests/test_analyzer_popularity.py` (or nearest), `tests/report/test_html_single.py`, `tests/commands/test_analyze_markdown.py`, `tests/test_report_schema_version.py`, `tests/test_analyze_rerun.py`, `tests/test_cli.py`.
- Delete: `tests/commands/test_analyze_snapshot_date.py`.

---

## Task 1: The `source` block in every analyzer schema + consistency test

**Files:**
- Create: `tests/schemas/test_source_block_consistency.py`
- Modify: all 13 `regis/schemas/analyzer/*.schema.json`

- [ ] **Step 1: Write the failing consistency test**

Create `tests/schemas/test_source_block_consistency.py`:

```python
"""Every analyzer schema must declare the identical optional `source` block."""

import json
from importlib.resources import files

ANALYZERS = [
    "cve", "dockle", "endoflife", "freshness", "hadolint", "oci",
    "popularity", "provenance", "sbom", "scorecarddev", "secrets",
    "size", "versioning",
]

SOURCE_BLOCK = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "fetched_at": {"type": "string", "format": "date-time"},
        "built_at": {"type": "string", "format": "date-time"},
        "version": {"type": "string"},
        "checksum": {"type": "string"},
    },
}


def _schema(name: str) -> dict:
    text = (
        files("regis")
        .joinpath(f"schemas/analyzer/{name}.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def test_every_analyzer_schema_declares_source():
    for name in ANALYZERS:
        schema = _schema(name)
        assert "source" in schema["properties"], f"{name} missing source"


def test_source_block_is_identical_everywhere():
    for name in ANALYZERS:
        schema = _schema(name)
        assert schema["properties"]["source"] == SOURCE_BLOCK, (
            f"{name} source block differs from canonical shape"
        )
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pipenv run pytest tests/schemas/test_source_block_consistency.py -v --no-cov`
Expected: FAIL — `cve missing source` (no schema declares `source` yet).

- [ ] **Step 3: Add the `source` block to every analyzer schema**

For **each** of the 13 files `regis/schemas/analyzer/<name>.schema.json`, add this property inside the top-level `"properties": { ... }` object (do **not** add it to `required`; keep `additionalProperties: false`). Insert it as the last property for consistency:

```json
    "source": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "fetched_at": { "type": "string", "format": "date-time" },
        "built_at": { "type": "string", "format": "date-time" },
        "version": { "type": "string" },
        "checksum": { "type": "string" }
      }
    }
```

Remember to add a comma after the previous property's closing brace. The 13 files: `cve`, `dockle`, `endoflife`, `freshness`, `hadolint`, `oci`, `popularity`, `provenance`, `sbom`, `scorecarddev`, `secrets`, `size`, `versioning`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pipenv run pytest tests/schemas/test_source_block_consistency.py -v --no-cov`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add tests/schemas/test_source_block_consistency.py regis/schemas/analyzer/
git commit -m "feat(analyzers): declare optional source freshness block in every schema"
```

---

## Task 2: cve analyzer emits `source` from grype DB status

**Files:**
- Modify: `regis/analyzers/cve.py:128-139` (the `return { ... }` of `analyze`)
- Test: `tests/test_analyzer_cve.py` (use the existing cve test module; if unsure, run `ls tests | grep -i cve` and pick the analyzer test file)

The grype fixture `tests/fixtures/grype/debian11_json.json` carries:
`descriptor.db.status.built = "2026-05-30T07:21:01Z"`, `descriptor.db.status.schemaVersion = "v6.1.4"`, and `descriptor.db.status.from = "https://...vulnerability-db_v6.1.4_...tar.zst?checksum=sha256%3A88f6f4182111eeb714982e5534be5bd8f1f478aafafe83ad6c6fcccf9d015d06"`.

- [ ] **Step 1: Write the failing test**

Add to the cve analyzer test module:

```python
def test_cve_source_extracted_from_grype_db_status():
    import json
    from importlib.resources import files as _files
    from regis.analyzers.cve import CveAnalyzer

    raw = json.loads(
        _files("tests").joinpath("fixtures/grype/debian11_json.json").read_text()
    )
    source = CveAnalyzer._source_from_descriptor(raw.get("descriptor", {}))

    assert source["built_at"] == "2026-05-30T07:21:01Z"
    assert source["version"] == "v6.1.4"
    assert source["checksum"] == (
        "sha256:88f6f4182111eeb714982e5534be5bd8f1f478aafafe83ad6c6fcccf9d015d06"
    )
    assert isinstance(source["fetched_at"], str) and source["fetched_at"]


def test_cve_source_tolerates_missing_db_status():
    from regis.analyzers.cve import CveAnalyzer

    source = CveAnalyzer._source_from_descriptor({})
    assert "built_at" not in source
    assert isinstance(source["fetched_at"], str) and source["fetched_at"]
```

> If `tests` is not an importable package, read the fixture with an absolute path:
> `Path(__file__).parent / "fixtures/grype/debian11_json.json"`. Match the convention already used in the cve test module.

- [ ] **Step 2: Run it to verify it fails**

Run: `pipenv run pytest tests/test_analyzer_cve.py -k source -v --no-cov`
Expected: FAIL — `AttributeError: ... has no attribute '_source_from_descriptor'`.

- [ ] **Step 3: Implement the extractor and wire it into the return**

At the top of `regis/analyzers/cve.py`, ensure these imports exist:

```python
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlparse
```

Add this static method to the analyzer class:

```python
    @staticmethod
    def _source_from_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
        """Build the source freshness block from grype's descriptor.db.status."""
        status = (descriptor.get("db") or {}).get("status") or {}
        source: dict[str, Any] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        if status.get("built"):
            source["built_at"] = status["built"]
        if status.get("schemaVersion"):
            source["version"] = status["schemaVersion"]
        frm = status.get("from") or ""
        if frm:
            checksum = parse_qs(urlparse(frm).query).get("checksum", [None])[0]
            if checksum:
                source["checksum"] = unquote(checksum)
        return source
```

In the `analyze` return dict (`regis/analyzers/cve.py:128-139`), add a `source` key after `"targets": targets,`:

```python
            "targets": targets,
            "source": self._source_from_descriptor(data.get("descriptor", {})),
        }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pipenv run pytest tests/test_analyzer_cve.py -v --no-cov`
Expected: PASS (new tests + existing cve tests unchanged — `scanner_version` is untouched).

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/cve.py tests/test_analyzer_cve.py
git commit -m "feat(analyzers): capture grype vuln-DB build date in cve source block"
```

---

## Task 3: scorecarddev analyzer emits `source` from the API response

**Files:**
- Modify: `regis/analyzers/scorecarddev.py:214-221` (the available-result `return { ... }`)
- Test: `tests/test_scorecarddev.py`

The OpenSSF Scorecard API response includes top-level `date` (when the scorecard was computed) and `scorecard.version`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_scorecarddev.py`:

```python
def test_scorecard_source_extracted_from_raw(monkeypatch):
    from regis.analyzers import scorecarddev as mod

    raw = {
        "date": "2026-06-01T00:00:00Z",
        "scorecard": {"version": "v5.0.0"},
        "score": 7.5,
        "checks": [],
    }
    monkeypatch.setattr(mod, "_fetch_scorecard", lambda *a, **k: raw)
    monkeypatch.setattr(
        mod, "_resolve_source_repo", lambda *a, **k: ("gh", "owner", "repo")
    )

    analyzer = mod.ScorecardDevAnalyzer()
    result = analyzer.analyze(client=None, repository="library/nginx", tag="latest")

    assert result["scorecard_available"] is True
    assert result["source"]["built_at"] == "2026-06-01T00:00:00Z"
    assert result["source"]["version"] == "v5.0.0"
    assert isinstance(result["source"]["fetched_at"], str)
```

> Read the top of `tests/test_scorecarddev.py` first to copy its exact patching style and the analyzer's real class/constructor and `analyze` signature; adjust the two `monkeypatch.setattr` targets and the `analyze(...)` call to match.

- [ ] **Step 2: Run it to verify it fails**

Run: `pipenv run pytest tests/test_scorecarddev.py -k source -v --no-cov`
Expected: FAIL — `KeyError: 'source'`.

- [ ] **Step 3: Implement**

At the top of `regis/analyzers/scorecarddev.py`, ensure:

```python
from datetime import datetime, timezone
```

In the available-result return (`regis/analyzers/scorecarddev.py:214-221`), build and add `source`:

```python
        source: dict[str, Any] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        if raw.get("date"):
            source["built_at"] = raw["date"]
        scorecard_version = (raw.get("scorecard") or {}).get("version")
        if scorecard_version:
            source["version"] = scorecard_version

        return {
            "analyzer": self.name,
            "repository": repository,
            "source_repo": source_url,
            "scorecard_available": True,
            "score": raw.get("score"),
            "checks": checks,
            "source": source,
        }
```

Leave the two unavailable-result returns (no `raw`) untouched — they carry no `source`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pipenv run pytest tests/test_scorecarddev.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/scorecarddev.py tests/test_scorecarddev.py
git commit -m "feat(analyzers): capture scorecard assessment date in source block"
```

---

## Task 4: popularity migrates `last_updated` → `source.built_at`

**Files:**
- Modify: `regis/analyzers/popularity.py:43-54` (the `analyze` return) and `:56-67` (`_empty`)
- Modify: `regis/schemas/analyzer/popularity.schema.json` (drop `last_updated` from `required` and `properties`)
- Test: `tests/test_analyzer_popularity.py` (the popularity test module — confirm with `ls tests | grep -i popular`)

- [ ] **Step 1: Write/adjust the failing test**

Add to the popularity test module (and remove any existing assertion expecting a top-level `last_updated`):

```python
def test_popularity_last_updated_migrated_to_source(monkeypatch):
    import regis.analyzers.popularity as mod

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {
                "pull_count": 10,
                "star_count": 2,
                "description": "d",
                "last_updated": "2026-06-05T12:00:00Z",
                "date_registered": "2020-01-01T00:00:00Z",
            }

    monkeypatch.setattr(mod.requests, "get", lambda *a, **k: _Resp())

    analyzer = mod.PopularityAnalyzer()
    result = analyzer.analyze(client=None, repository="library/nginx", tag="latest")

    assert "last_updated" not in result
    assert result["source"]["built_at"] == "2026-06-05T12:00:00Z"
    assert result["date_registered"] == "2020-01-01T00:00:00Z"
```

> Confirm the analyzer's real class name and `analyze` signature from the test module / `regis/analyzers/popularity.py`, and copy the module's existing `requests.get` patching style if it differs.

- [ ] **Step 2: Run it to verify it fails**

Run: `pipenv run pytest tests/test_analyzer_popularity.py -k source -v --no-cov`
Expected: FAIL — `KeyError: 'source'` (and/or `last_updated` still present).

- [ ] **Step 3: Implement**

At the top of `regis/analyzers/popularity.py`, ensure:

```python
from datetime import datetime, timezone
```

Replace the success return (`regis/analyzers/popularity.py:43-54`) — drop `last_updated`, add `source`:

```python
        return {
            "analyzer": self.name,
            "repository": repository,
            "available": True,
            "pull_count": data.get("pull_count", 0),
            "star_count": data.get("star_count", 0),
            "description": data.get("description", ""),
            "date_registered": data.get("date_registered"),
            "is_official": repository.startswith("library/"),
            "source": {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                **(
                    {"built_at": data["last_updated"]}
                    if data.get("last_updated")
                    else {}
                ),
            },
        }
```

Update `_empty` (`regis/analyzers/popularity.py:56-67`) — drop the `last_updated` key:

```python
    def _empty(self, repository: str) -> dict[str, Any]:
        return {
            "analyzer": self.name,
            "repository": repository,
            "available": False,
            "pull_count": None,
            "star_count": None,
            "description": None,
            "date_registered": None,
            "is_official": repository.startswith("library/"),
        }
```

In `regis/schemas/analyzer/popularity.schema.json`: remove `"last_updated"` from the `required` array, and remove the `"last_updated": { ... }` property block. (`source` was already added in Task 1.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pipenv run pytest tests/test_analyzer_popularity.py tests/schemas/test_source_block_consistency.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/analyzers/popularity.py regis/schemas/analyzer/popularity.schema.json tests/test_analyzer_popularity.py
git commit -m "feat(analyzers): migrate popularity last_updated into source block"
```

---

## Task 5: Remove `snapshot_date` and bump `REPORT_SCHEMA_VERSION` 4 → 5

**Files:**
- Delete: `regis/data/snapshot_dates.json`
- Delete: `tests/commands/test_analyze_snapshot_date.py`
- Modify: `regis/commands/analyze.py:585-599`, `regis/utils/report.py:17` and `:341-345`, `regis/schemas/report/report.schema.json`, `regis/templates/html/report.html.j2:159-161`
- Modify tests: `tests/commands/test_analyze_markdown.py`, `tests/report/test_html_single.py`, `tests/test_report_schema_version.py`, `tests/test_analyze_rerun.py`, `tests/test_cli.py`

- [ ] **Step 1: Update the version-constant test to fail (red)**

In `tests/test_report_schema_version.py:78`, change:

```python
        assert REPORT_SCHEMA_VERSION == 4
```
to:
```python
        assert REPORT_SCHEMA_VERSION == 5
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pipenv run pytest tests/test_report_schema_version.py -v --no-cov`
Expected: FAIL — `assert 4 == 5`.

- [ ] **Step 3: Bump the constant and remove the snapshot_date code paths**

In `regis/utils/report.py:17`:

```python
REPORT_SCHEMA_VERSION = 5
```

In `regis/utils/report.py`, delete the markdown snapshot block (`:341-345`):

```python
    snapshot_date = report.get("snapshot_date") or report.get("request", {}).get(
        "snapshot_date"
    )
    if snapshot_date:
        lines += [f"**Snapshot date:** {snapshot_date}", ""]
```

In `regis/commands/analyze.py`, delete the injection block (`:585-599`) — the whole `try:` that reads `data/snapshot_dates.json` and sets `analysis_report["snapshot_date"]`. Remove the now-unused `from importlib.resources import files as _res_files` only if it is local to that block.

In `regis/schemas/report/report.schema.json`, delete the `snapshot_date` property:

```json
    "snapshot_date": {
      "type": "string",
      "description": "ISO 8601 date when this version was snapshotted in the doc site."
    },
```

In `regis/templates/html/report.html.j2`, delete the header rows (`:159-161`):

```jinja
        {% if report.snapshot_date %}
        <dt>Snapshot date</dt><dd>{{ report.snapshot_date }}</dd>
        {% endif %}
```

Delete the data file and the dedicated test:

```bash
git rm regis/data/snapshot_dates.json tests/commands/test_analyze_snapshot_date.py
```

- [ ] **Step 4: Remove the remaining snapshot_date test assertions**

In `tests/commands/test_analyze_markdown.py`, delete the snapshot_date tests: `test_render_markdown_includes_snapshot_date`, `test_render_markdown_omits_snapshot_date_when_empty`, `test_render_markdown_omits_snapshot_date_when_absent`, and `test_render_markdown_no_snapshot_date_section_when_none`. If `_minimal_report`/helpers accept a `snapshot_date` kwarg only used by these, leave the helper as-is (harmless).

In `tests/report/test_html_single.py`, delete `test_snapshot_date_shown_when_present` and `test_snapshot_date_absent_when_missing` (`:65-71`).

In `tests/test_analyze_rerun.py:353` and `tests/test_cli.py:362`, change `assert ...["schemaVersion"] == 4` to `== 5`.

- [ ] **Step 5: Run the affected tests to verify they pass**

Run: `pipenv run pytest tests/test_report_schema_version.py tests/commands/test_analyze_markdown.py tests/report/test_html_single.py tests/test_analyze_rerun.py tests/test_cli.py -v --no-cov`
Expected: PASS (no snapshot_date references remain).

- [ ] **Step 6: Confirm no stray references remain**

Run: `grep -rIn "snapshot_date\|Snapshot date" regis/ tests/`
Expected: no matches (doc-site generated copies under `docs/website/` are regenerated separately — Task 7).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(report): drop snapshot_date marker and bump schema version to 5"
```

---

## Task 6: Per-analyzer source freshness in the HTML report (compact mode)

**Files:**
- Modify: `regis/templates/html/report.html.j2:243-255` (analyzer `an-body`)
- Test: `tests/report/test_html_single.py`

In detail mode (`show_details`), `render_detail(result)` already renders the nested `source` mapping as a table — no change needed. In compact mode the generic loop skips mappings (`{% if v is not mapping ... %}`), so add an explicit source line.

- [ ] **Step 1: Write the failing test**

Add to `tests/report/test_html_single.py`:

```python
    def test_analyzer_source_built_at_shown_in_compact_mode(self):
        report = _minimal_report(
            results={
                "cve": {
                    "analyzer": "cve",
                    "vulnerability_count": 0,
                    "source": {
                        "fetched_at": "2026-06-10T09:00:00+00:00",
                        "built_at": "2026-05-30T07:21:01Z",
                        "version": "v6.1.4",
                    },
                }
            }
        )
        html = render_html_single(report, sections="summary")
        assert "Data built" in html
        assert "2026-05-30T07:21:01Z" in html
```

> Confirm the `sections` value that yields compact mode by reading `render_html_single` / `_build_context` (the `show_details` flag). If `"summary"` is not the compact selector, use the value that sets `show_details=False`. If compact vs detail is not selectable via `sections`, instead assert against the default `render_html_single(report)` and check `"Data built"` appears.

- [ ] **Step 2: Run it to verify it fails**

Run: `pipenv run pytest tests/report/test_html_single.py -k source_built_at -v --no-cov`
Expected: FAIL — `"Data built" not in html`.

- [ ] **Step 3: Implement the template addition**

In `regis/templates/html/report.html.j2`, inside the compact branch (after the `</dl>` that closes the `scalars` list at `:251`, still within `{% if not show_details %}`), add:

```jinja
          {% if result.source %}
          <dl class="scalars source-meta">
            {% if result.source.built_at %}<dt>Data built</dt><dd>{{ result.source.built_at }}</dd>{% endif %}
            {% if result.source.version %}<dt>Source version</dt><dd>{{ result.source.version }}</dd>{% endif %}
          </dl>
          {% endif %}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pipenv run pytest tests/report/test_html_single.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/templates/html/report.html.j2 tests/report/test_html_single.py
git commit -m "feat(report): show analyzer data-source freshness in HTML report"
```

---

## Task 7: Full suite, generated docs, and final verification

**Files:**
- Possibly regenerated: `docs/website/static/schemas/**`, `docs/website/docs/reference/schemas/**` (generated assets)

- [ ] **Step 1: Run the full suite with coverage gates**

Run: `pipenv run pytest`
Expected: PASS, global coverage ≥ 90 % and every `regis/` file ≥ 90 %. If a new branch in an analyzer (`cve._source_from_descriptor`, scorecard/popularity source) is under-covered, add a focused unit test for the missing branch (e.g. cve with a `from` URL lacking a `checksum` query param; scorecard `raw` with no `date`).

- [ ] **Step 2: Regenerate the published schema docs**

The `report.schema` and analyzer schemas are mirrored under `docs/website/` by a generator. Run the project's docs/schema generation (check `scripts/` and `package.json`/`pyproject.toml`; e.g. a `jsonschema2md`-based step) so the published `report.schema.md` / `report.schema.json` no longer mention `snapshot_date` and the analyzer schema docs include `source`. If generation is CI-only, note it in the PR body and leave the `docs/website/**` regeneration to CI.

Run (discover the exact command first): `grep -rn "jsonschema2md\|schema" scripts/ package.json 2>/dev/null | head`

- [ ] **Step 3: Lint/format**

Run: `pipenv run ruff check . && pipenv run ruff format . && trunk check`
Expected: clean (Trunk's hook may auto-fix; re-stage produced changes).

- [ ] **Step 4: Commit any generated/lint changes**

```bash
git add -A
git commit -m "docs(report): refresh generated schema assets for source block + snapshot_date removal"
```

- [ ] **Step 5: Final sanity grep**

Run: `grep -rIn "snapshot_date" regis/ tests/`
Expected: no matches.

---

## Cross-repo follow-up (NOT part of this plan — separate repos)

After merge, coordinate in the three consumer repos (each gates on `schemaVersion` and/or reads `popularity.last_updated`):
- `regis-gitlab`, `regis-backstage`, `regis-action`.

Two breaking changes to handle there: (1) `schemaVersion` 4 → 5 (only breaks `==` gates); (2) `popularity.last_updated` is gone — read `popularity.source.built_at` instead. Track as issues in those repos.

---

## Self-Review notes

- **Spec coverage:** `source` block in all schemas (T1) ✓; cve population (T2) ✓; scorecarddev population (T3) ✓; popularity migration + `date_registered` kept (T4) ✓; snapshot_date full removal — schema/data/injection/markdown/html (T5) ✓; `REPORT_SCHEMA_VERSION` 4→5 (T5) ✓; per-analyzer rendering, header gains nothing (T6 + T5) ✓; cross-repo coordination noted ✓; endoflife/category-C excluded ✓.
- **Markdown per-analyzer note:** the markdown renderer has no per-analyzer sections, so per-analyzer source rendering is implemented in HTML only (compact via T6, detail mode automatic via `render_detail`). The spec's "markdown and HTML" intent reduces to HTML in practice — markdown only loses the `Snapshot date` line.
- **Type/name consistency:** `_source_from_descriptor` (T2), `source` keys `fetched_at`/`built_at`/`version`/`checksum` used identically in schema (T1), analyzers (T2-T4), and template (T6).
- **Class names confirmed:** `CveAnalyzer` (`regis/analyzers/cve.py:25`), `ScorecardDevAnalyzer` (`regis/analyzers/scorecarddev.py:130`, with module-level `_resolve_source_repo` / `_fetch_scorecard`), `PopularityAnalyzer` (`regis/analyzers/popularity.py:18`). `tests` is an importable package (`tests/__init__.py` present), so `importlib.resources.files("tests")` works for fixture loading.
