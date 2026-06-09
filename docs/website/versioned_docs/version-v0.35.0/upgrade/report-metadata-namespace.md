---
sidebar_position: 5
---

# Report metadata namespace — `schemaVersion` 3

Starting with report `schemaVersion: 3`, user metadata (`--meta`) lives at a
**single canonical location**: the top-level `metadata` object. The duplicate
`request.metadata` field has been **removed**, and the report schema now rejects
it (`request` is `additionalProperties: false`).

## What changed

- `report.metadata.*` is the only place user metadata is written.
- Rules reference it as `{"var": "metadata.<key>"}` (e.g. `metadata.ci.job.url`).
- `request.metadata` is gone.

## Action required

- **Rule authors:** use `metadata.*` paths. Any rule that referenced
  `request.metadata.*` must switch to `metadata.*`.
- **Downstream consumers** (dashboards, plugins) reading `request.metadata` must
  read top-level `metadata` instead, and gate on `schemaVersion >= 3`.
- **Stored reports** produced before this change that contain `request.metadata`
  will fail validation if re-validated; regenerate them with `regis analyze`.

There is no automated migration: reports are generated output, not user config.
