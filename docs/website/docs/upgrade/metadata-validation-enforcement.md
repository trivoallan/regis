---
sidebar_position: 6
---

# Metadata validation becomes a real checkpoint

**Behaviour change.** A playbook bundle's `meta.schema.json` is now actually read and
enforced. Until this release it was read on no execution path: the `metadata` analyzer
ran with an empty input, so every report claimed `results.metadata.valid: true`
regardless of what `--meta` carried, and a missing required field went unnoticed.

## What changed

- The `--meta` values now reach the `metadata` analyzer on the normal `analyze` path.
- Schemas in force stack by JSON Schema `allOf`, in order: the well-known schema, each
  `--playbook` bundle's `meta.schema.json`, then each `--meta-schema` path. A source can
  only add constraints, never relax another's.
- New `--meta-schema PATH` option (repeatable, local paths, JSON) for a schema outside
  any bundle.
- New **exit code 3**: the metadata violates a schema the caller opted into. The report
  is written first, and the code is independent of `--fail`.
- `results.metadata.schema_sources` records which schemas were in force.
- A schema that cannot be read or parsed now aborts with exit 1 instead of being skipped
  with a log warning.

## Who is affected

**You ship a bundle with a `meta.schema.json`.** Its constraints now bite. A run that
used to exit 0 with an unsatisfied `required` field now exits 3. Either supply the
fields, or remove the constraint from the schema if it was aspirational:

```bash
regis analyze myimage:latest -p ./my-bundle/ -m PROJECT_ID=PROJ-42
# exit 3 if the schema requires a field you did not pass
```

**You consume a bundle you do not own.** The party that declares the required field and the
party whose pipeline fails need not be the same. `--meta-advisory` (or
`REGIS_META_ADVISORY=1`) suspends the sanction without hiding the finding — exit 0, the report
still records what is missing, and `results.metadata.enforcement` becomes `"advisory"` so
whoever reads the report sees that a derogation was used:

```bash
regis analyze myimage:latest -p ./their-bundle/ --meta-advisory -m PROJECT_ID=PROJ-42
# exit 0; jq '.results.metadata.enforcement' → "advisory"
```

Use it to cross the migration, then drop it. A consumer that wants the guarantee can reject a
report carrying the derogation:

```bash
jq -e '.results.metadata.enforcement == "enforcing"' report.json
```

**Your bundle's `meta.schema.json` is malformed.** It used to be silently ignored; it now
fails the run with exit 1 and a message naming the file.

**You pass `--meta` with no bundle or `--meta-schema` schema.** Nothing changes. Only the
well-known schema applies, it declares no `required` field, and a violation of it (an
unknown `ci.platform`, a malformed `ci.job.url`) is recorded in the report and warned
about on stderr without changing the exit code.

## Adjusting a CI pipeline

A caller that only tests `exit_code != 0` needs no change. One that distinguishes
outcomes should add the new code:

```bash
regis analyze "$IMAGE" -p ./regime/ --fail -m SAISINE_URL="$SAISINE_URL"
case $? in
  0) echo "admitted" ;;
  1) echo "refused by the rules" ;;
  2) echo "bad invocation (regis usage)" ;;
  3) echo "malformed call: metadata missing or invalid" ;;
esac
```

A caller that must not accept a derogation checks the report rather than the exit code:

```bash
jq -e '.results.metadata.enforcement == "enforcing"' report.json
```

## Report compatibility

`schema_sources` is additive inside the existing `results.metadata` object, so
`REPORT_SCHEMA_VERSION` is unchanged and stored reports stay readable by `regis evaluate`
and `--rerun`. A report produced before this release simply has no `schema_sources` key.

`regis evaluate` is unaffected: it replays `results.metadata` verbatim and never exits 3.
