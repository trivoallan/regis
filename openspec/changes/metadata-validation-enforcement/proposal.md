## Why

`docs/website/docs/concepts/playbooks.md` § Metadata promises that a bundle can ship a
`meta.schema.json` declaring `required` fields, and that "Missing required fields cause the
`metadata` analyzer to report a validation failure". The code does not do this.

`metadata` is a registered entry-point analyzer, so it runs on every `regis analyze` — but the
generic analyzer loop instantiates it as `cls()`, with no arguments. It therefore validates the
**empty dict** and writes `results.metadata.valid: true` into every report, while the real
`--meta` values travel separately into the top-level `metadata` envelope and never meet the
validator. `bundle_meta_schema_path()` exists in the playbook loader but has no production
caller, so a bundle's `meta.schema.json` is read on no execution path.

The net effect is worse than a missing check: the report carries a green seal it never earned.
A caller can declare a required field, omit it, and the analysis exits 0 with
`metadata.valid: true`.

A downstream image-admission orchestrator is about to rely on this for a governance guarantee —
no refusal may be pronounced without an address to contest it (`SAISINE_URL`) — so the absence of
a declared field must have a consequence the caller can act on without parsing JSON.

## What Changes

- The normal `analyze` path hands the `--meta` values **and** the effective metadata schemas to
  `MetadataAnalyzer`, so `results.metadata` reflects the real input.
- Schema sources stack by `allOf`, in order: the well-known schema, each `--playbook` bundle's
  `meta.schema.json`, then each `--meta-schema` path. Union only — a caller can add requirements,
  never weaken a playbook's regime.
- New repeatable `--meta-schema PATH` option on `analyze` (normal and `--rerun metadata`), for a
  JSON Schema outside any bundle. Local paths only.
- New exit code **3** — the call was malformed — raised when metadata violates a schema, and only
  when a source beyond the well-known schema is in play. Distinct from exit 1 (the image was
  refused by the rules) and exit 2 (Click usage error). The report is written before the exit.
- An unreadable schema is a hard error (exit 1) instead of a `logger.warning` that continues
  without it. A broken regime is not an absent regime.
- `results.metadata.schema_sources` lists the schemas actually loaded, so "no schema was in
  force" is scriptable and not merely a line on stderr.
- A `--meta` with no loadable schema (every `--playbook` is a file or a URL) warns explicitly on
  stderr.
- Documentation is corrected to match the code, and gains the two complementary mechanisms
  (schema `required` vs a playbook rule over `metadata.*`) and the exit codes.

## Capabilities

### New Capabilities

- `metadata-validation`: how regis validates user-supplied `--meta` values against the
  well-known schema, playbook bundle schemas and explicit `--meta-schema` paths, what it records
  in the report, and how it signals a malformed call.

### Modified Capabilities

## Impact

- `regis/core/domain/analyzers/metadata.py`, `regis/core/application/analyze_image.py`,
  `regis/adapters/driving/cli/commands/analyze.py`.
- Report output gains `results.metadata.schema_sources` (additive, inside an existing object;
  `results` is `additionalProperties: {type: object}`). **No `REPORT_SCHEMA_VERSION` bump**, so
  stored reports stay readable and `regis evaluate` / `--rerun` keep replaying them.
- Behaviour change for callers whose bundle already ships a `meta.schema.json`: violations that
  were silently ignored now exit 3. This is the documented promise being honoured; an
  `upgrade/` note records it.
- No change for a caller passing `--meta` with no schema source beyond the well-known one:
  same exit codes as today.
- `regis evaluate` is unchanged — it replays `results.metadata` verbatim and does not re-run the
  analyzer.
