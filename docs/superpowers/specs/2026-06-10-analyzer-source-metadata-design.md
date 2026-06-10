# Design — Analyzer source freshness metadata (`source` block) + drop `snapshot_date`

**Date:** 2026-06-10
**Status:** Approved (design), pending implementation plan
**Scope (commit):** `analyzers`, `report`

## Problem

The report header shows two dates: **Analysis date** (when `regis analyze` ran) and
**Snapshot date**. `snapshot_date` is read from `regis/data/snapshot_dates.json`,
keyed by the installed Regis version, and only records *which doc-site snapshot /
Regis release* produced the report (see `report.schema.json`: "ISO 8601 date when
this version was snapshotted in the doc site"). It is an **editorial/versioning
marker**, not a data-freshness marker.

This is misleading. A vulnerability scan is only as good as the data it ran against,
and that data freshness comes from the **tools and external sources the analyzers
consume** — not from Regis. `snapshot_date` looks like it tells the reader how fresh
the security data is, but it does not. Worse, the genuinely useful freshness signals
that the sources *do* expose are currently discarded.

## Findings — which analyzers consume a time-varying external source

Audited every analyzer. Three expose a capturable source-freshness indicator; the
rest read image/registry-embedded metadata or compute from scratch.

| Analyzer          | Source                | Freshness field exposed                                  | Today          |
| ----------------- | --------------------- | -------------------------------------------------------- | -------------- |
| **cve** (grype)   | downloaded vuln DB    | `descriptor.db.status.built` (+ `schemaVersion`, checksum) | **dropped**    |
| **scorecarddev**  | OpenSSF Scorecard API | `date` (when scorecard computed) + `scorecard.version`   | **dropped**    |
| **popularity**    | Docker Hub API        | `last_updated`, `date_registered`                        | captured (own fields) |
| endoflife         | endoflife.date API    | none (only product dates; no dataset timestamp)          | n/a            |
| secrets, dockle, hadolint, sbom, freshness, oci, provenance, versioning, size | image / registry / pure computation | none | n/a |

The three freshness signals are **semantically heterogeneous**: grype = *DB build
date*, scorecard = *assessment computed date + tool version*, popularity = *repo last
push*. A block named `db` would be a false friend. The shared concept is **"freshness
/ provenance of the analyzer's external data source"**.

## Decisions (settled during brainstorming)

| #   | Decision                          | Choice                                                                                                                                |
| --- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Generic block name & concept      | **`source`** — freshness/provenance of the external data source (not "db").                                                           |
| 2   | Generic framing mechanism         | **Inline block in every analyzer schema + inter-schema consistency test** (Option B). No cross-file `$ref` (per-analyzer validation in `base.py` uses a bare `jsonschema.validate` with no registry). |
| 3   | Block applies to                  | **All analyzer schemas** (optional, by convention). Only cve, scorecarddev, popularity populate it today.                            |
| 4   | `snapshot_date`                   | **Removed entirely** — schema property, `snapshot_dates.json` data file, injection block, all rendering.                              |
| 5   | `REPORT_SCHEMA_VERSION`           | **Bump 4 → 5.**                                                                                                                       |
| 6   | Header rendering                  | Header loses `snapshot_date`, **nothing replaces it.** No global DB/freshness line.                                                   |
| 7   | Per-analyzer rendering            | Each analyzer section shows its `source.built_at` / `source.version` when present.                                                    |
| 8   | popularity migration              | **Migrate** `last_updated` → `source.built_at`. `date_registered` (repo creation = provenance, not freshness) **stays** popularity-specific. |
| 9   | grype `scanner_version`           | **Stays** separate (grype CLI version); `source.version` = the **DB** schema version.                                                 |
| 10  | endoflife / category B & C        | **No `source` block for now** (YAGNI). The block is optional, so they simply omit it.                                                 |

## Architecture

### The `source` block (shared shape)

Added inline to every analyzer schema under `regis/schemas/analyzer/*.schema.json`:

```json
"source": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "fetched_at":     { "type": "string", "format": "date-time" },
    "built_at":       { "type": "string", "format": "date-time" },
    "version":        { "type": "string" },
    "checksum":       { "type": "string" }
  }
}
```

All fields optional. Semantics:

- `fetched_at` — when Regis queried the source during **this** run (`datetime.now(timezone.utc)`).
- `built_at` — when the source data itself was built / computed / last updated.
- `version` — version of the source dataset/tool (DB schema version, scorecard version).
- `checksum` — integrity hash when the source provides one (grype DB checksum).

Several analyzer result schemas set `additionalProperties: false` (e.g. cve,
secrets), so every analyzer schema must **declare** the `source` property for a
result carrying it to validate. A consistency test enforces that the declared shape
is identical across all `analyzer/*.schema.json`.

### Population per analyzer

| Analyzer         | `built_at`                          | `version`                       | `checksum`              | `fetched_at` |
| ---------------- | ----------------------------------- | ------------------------------- | ----------------------- | ------------ |
| **cve**          | `descriptor.db.status.built`        | `descriptor.db.status.schemaVersion` | `descriptor.db.status` checksum | now()  |
| **scorecarddev** | API `date`                          | `scorecard.version`             | —                       | now()        |
| **popularity**   | (migrated from) `last_updated`      | —                               | —                       | now()        |

- **cve** (`regis/analyzers/cve.py`): alongside the existing `scanner_version`,
  read `descriptor.db.status.{built, schemaVersion}` and the DB checksum, emit a
  `source` dict. Tolerate missing fields (older grype output, missing DB status).
- **scorecarddev** (`regis/analyzers/scorecarddev.py`): extract the top-level
  `date` and `scorecard.version` from the API response into `source`.
- **popularity** (`regis/analyzers/popularity.py`): stop emitting `last_updated` as a
  top-level field; emit it as `source.built_at` instead. Keep `date_registered`.

### `snapshot_date` removal

- `regis/schemas/report/report.schema.json` — delete the `snapshot_date` property.
  (Root schema has no `additionalProperties: false`, so old reports carrying the
  field still validate — removal is clean.)
- `regis/data/snapshot_dates.json` — delete the file.
- `regis/commands/analyze.py` — delete the injection block (the `importlib.resources`
  read + `analysis_report["snapshot_date"] = ...`).
- `regis/utils/report.py` — delete the markdown `**Snapshot date:**` line and the
  `snapshot_date` lookup. Remove the HTML-single header rendering of `snapshot_date`.
- Any other consumer in `apps/dashboard` / report SPA that renders `snapshot_date`.

### `REPORT_SCHEMA_VERSION`

`regis/utils/report.py`: `REPORT_SCHEMA_VERSION = 4` → `5`. Update any fixtures /
snapshot tests asserting the value.

### Rendering

- **Global header**: only change is the removal of the `snapshot_date` line.
- **Per-analyzer**: where an analyzer result carries a `source` block, render a small
  freshness line in that analyzer's section, e.g. `Data built: <built_at>` and, when
  present, `Source version: <version>`. Applies to markdown and HTML-single. Sections
  without a `source` block render unchanged.

## Testing (TDD)

1. **cve source extraction** — from the grype fixture
   (`tests/fixtures/grype/debian11_json.json`): asserts `source.built_at`,
   `source.version`, `source.checksum`, `source.fetched_at` populated; tolerant when
   `db.status` absent.
2. **scorecarddev source extraction** — from a scorecard API fixture: `source.built_at`
   = `date`, `source.version` = `scorecard.version`.
3. **popularity migration** — `last_updated` no longer top-level; appears as
   `source.built_at`; `date_registered` still present.
4. **schema accepts `source`** — each analyzer schema validates a result carrying a
   `source` block; rejects unknown keys inside it (`additionalProperties: false`).
5. **inter-schema consistency** — the `source` block declaration is identical across
   all `analyzer/*.schema.json`.
6. **per-analyzer rendering** — markdown/HTML show the freshness line when `source`
   present, omit it when absent.
7. **snapshot_date removal regression** — report no longer carries/render
   `snapshot_date`; `snapshot_dates.json` gone; injection path removed.
8. **`REPORT_SCHEMA_VERSION` == 5**.

Coverage gates (global ≥ 90 %, per-file ≥ 90 %) apply; new branches in the analyzers
need direct tests.

## Cross-repo coordination (follow-up, out of this worktree)

Two **breaking** changes for the three downstream consumers (`regis-gitlab`,
`regis-backstage`, `regis-action`):

1. **`schemaVersion` 4 → 5** — consumers gating on `==` break; `>=` are transparent.
   Verify each consumer's gate in its own repo.
2. **`popularity.last_updated` → `source.built_at`** — any consumer reading
   `popularity.last_updated` (dashboard/Backstage card, GitLab rendering) breaks.
   This is the most sensitive change; coordinate updates in the consumer repos.

These are tracked as follow-up work in the respective repositories; they are not part
of this change set.

## Out of scope (YAGNI)

- `source` block for endoflife (no dataset-freshness field; HTTP `Last-Modified`
  header capture is brittle and deferred).
- `source` block for category-C analyzers (image/registry-embedded, pure computation).
- Migrating `popularity.date_registered` (provenance, not freshness).
- Any global-header freshness summary.
