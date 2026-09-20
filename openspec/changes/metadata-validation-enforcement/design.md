## Context

See proposal.md. Verified on `7aed616`:

- `metadata` is an entry point (`pyproject.toml`), `discover_analyzers()` filters nothing, and
  `analyze.py` does `selected = dict(all_analyzers)` — so `MetadataAnalyzer()` runs on every
  analysis with an empty dict and emits `{"valid": true}`.
- `--meta` values land in `envelope["metadata"]` only (`request.metadata` was removed by the
  meta-rules-UX change; `REPORT_SCHEMA_VERSION` is 5).
- `bundle_meta_schema_path()` has no caller outside `tests/test_playbook_loader.py`.
- `metadata.*` is **already** a first-class rule namespace: `_build_context` flattens it,
  `_is_optional_namespace` exempts it from `incomplete`, and `is_set` / `is_url` / `matches` etc.
  exist for it. Nothing to build there.

## Goals / Non-Goals

**Goals:**

- The seal in `results.metadata` reflects the metadata actually supplied.
- A declared-but-missing field has a consequence readable without parsing JSON.
- Existing callers with no schema source keep their exact current behaviour.

**Non-Goals:**

- Exposing `metadata.*` to playbook rules — already shipped.
- URL-sourced schemas. Paths only; a governance gate should not depend on a remote host.
- Enforcing exit 3 in `regis evaluate`. It is a dry-run replay over a stored report, not a
  checkpoint; making it fail would turn every replay of an old report into an error.
- A per-source `sha256` in `schema_sources`. Worth adding when an audit must prove _which_ schema
  sealed a given report; with local paths versioned alongside the caller, the path is enough.

## Decisions

- **Result stays in `results.metadata`.** It is where `--rerun metadata` already writes, `results`
  is `additionalProperties: {type: object}`, and rules already reach it. No new top-level key, no
  `REPORT_SCHEMA_VERSION` bump, no downstream break. The key already exists in today's reports —
  it just stops lying. Alternative (a new top-level `metadata_validation`) would need a schema
  change and a version bump for no gain.
- **The metadata analyzer leaves the thread pool.** It is a pure function of user input — no
  image, no inspector, no tools — and `AnalyzeImage.run` instantiates analyzers as `cls()`, which
  cannot carry constructor arguments. `run_and_evaluate` therefore removes `metadata` from the
  looped selection and calls `MetadataAnalyzer(metadata=…, meta_schema_paths=…).analyze()`
  directly, merging the result into `reports` and emitting its `on_progress` tick so the CLI
  output is unchanged. This also makes an unreadable schema a **hard** failure: inside the loop
  every exception becomes an error stub by design, so the run would have continued at exit 0.
  Alternatives rejected: a pre-bound `functools.partial` in `selected` (keeps the analyzer in the
  pool, so the error stays swallowed), and carrying metadata on `AnalysisContext` (puts user
  input on an image-centric object for one consumer).
- **A metadata-only selection still produces a report.** `-a metadata` leaves the looped
  selection empty, so the "All analyzers failed" guard is checked _after_ the metadata result is
  merged in.
- **`meta_schema_paths: Sequence[Path]`, not a single path.** Several `--playbook` bundles plus
  several `--meta-schema` can each contribute; a field required by any regime is required. Union
  by `allOf` is the only semantics that prevents a caller from weakening a playbook's regime by
  passing a permissive schema of their own.
- **Strictness is triggered by the _provenance_ of the constraint**, not by `--fail`. With at
  least one source beyond the well-known schema, any violation exits 3. With none, the violation
  is recorded and warned about, and the exit code is unchanged. Rationale: the governance
  guarantee comes from the playbook (or an explicit `--meta-schema`), which is an opt-in; the
  well-known schema declares no `required` and has never had teeth, so giving it teeth
  retroactively would break a caller passing e.g. `-m ci.platform=jenkins` for no governance gain
  — which the compatibility constraint forbids.
- **Exit 3 is unconditional, not gated on `--fail`.** `--fail` governs the verdict on the image; a
  malformed invocation is not a verdict. This is exactly what makes the two distinguishable
  without reading the report.
- **Exit 1, not a fourth code, for an unreadable schema.** That is regis failing to do its job,
  not a malformed call, so it goes through `ClickException`. Do not multiply codes.
- **Stop swallowing a broken schema.** `_build_combined_schema` currently logs a warning and
  continues without the schema — the silent disarming this whole change removes.
- **JSON only for `--meta-schema`**, matching the bundle's `meta.schema.json`. One form to
  document, and the analyzer already does `json.loads(path.read_text())`.
- **`click.Path(exists=True, dir_okay=False)`** for `--meta-schema`: a missing file is Click's own
  usage error (exit 2), no bespoke handling.

## Risks / Trade-offs

- [A bundle already shipping an inert `meta.schema.json` starts exiting 3] → this is the
  documented promise being honoured, recorded in an `upgrade/` note, and a caller who does not
  control the bundle has `--meta-advisory` as a traceable derogation. The earlier justification
  ("the bundle schema is the caller's own opt-in") was wrong whenever the schema's author and the
  caller are different people; see § Regulation analysis.
- [Exit 3 is a new code downstream must learn] → documented in `reference/cli.md`; a caller that
  only checks `!= 0` is unaffected.
- [The metadata tick no longer comes from the draining thread] → it is emitted synchronously
  after the pool has joined, so ordering is stable and nothing interleaves.
- [Two mechanisms for "require a metadata field" (schema vs rule) could confuse] → documented as a
  table with distinct exit codes and distinct report surfaces; the recommendation for a hard gate
  is to use both.

## Regulation analysis

<!-- incongru-voix: lessig — exit 3 imposed on a bundle's consumers, regulated by
     architecture — recours: none in the tool. Reviewer position: reformist, i.e. the
     answer below is "add a procedure", which is always the cheapest available exit.
     Whether this checkpoint deserved to exist is a different question, not asked here. -->

Three constraints are enacted here, and they do not weigh the same. Law regulates _after_
(a fact, a defence, an exception, a pardon); architecture regulates _before_ (no notice, no
mitigating circumstance, no appeal). This change regulates by architecture.

### C1 — An existing bundle whose `meta.schema.json` was inert now fails its consumers

```text
CONTRAINTE : the analysis becomes impossible to pass, for a caller who changed
             no line of their own configuration

  loi           The published docs already promised this behaviour. Rare case: the
                text said yes while the architecture said no. Aligning follows the
                published text — which does not waive the notice owed.
  norme         SemVer on 0.y permits a break in a minor, and an upgrade note exists.
                The norm is satisfied formally.
  prix          Repair is cheap (supply the field, or drop the `required`). But the
                price is not in the repair; it is in the discovery — a red pipeline.
  architecture  Total. `sys.exit(3)`, checked before every other outcome, no derogation.

  RECOURS       None in the tool. Dropping `required` from one's own schema is
                self-derogation, not recourse, and it presumes owning the bundle.
```

**This invalidates one of the decisions above.** "The bundle schema is the caller's opt-in"
holds only if the party shipping the schema and the party paying the exit code are the same.
In the target deployment they are not: a governance team authors the regime, an admission
orchestrator absorbs the exit code. A third party's consent was recorded as the caller's.

### C2 — An unreadable schema aborts the run (exit 1)

```text
  loi  none.  norme  fail-closed, well established.  prix  fixing JSON: low.
  architecture  total.
  RECOURS  none in the tool — but whoever is constrained owns the broken file, the
           message names it, and the failure is local and legible.
```

Legitimate: the constrained third party is oneself. Nothing to answer for.

### C3 — Declining `--no-fail-on-meta`

A deliberate refusal of a derogation route, justified by "not until someone is actually
broken". The broken party learns of it through a red pipeline. That charges the cost of our
own simplicity to someone else's price column.

### Would this have been voted, had it been presented as a rule?

_"From the next minor, any bundle declaring a required field fails its consumers' pipelines,
with no prior notice and no possible derogation."_ Put that way it passes — but with notice
and with a procedure. Those are what is missing. Worth stating plainly rather than as a
witticism: the field at stake is `SAISINE_URL`, an address at which to contest a refusal.
This change requires that nothing be refused without one, and imposes itself without one.

### Resolution — a derogation with a visible record (implemented)

Not a flag that removes the constraint: a procedure whose **use is visible**.
`--meta-advisory` (or `REGIS_META_ADVISORY=1`) keeps validation and the report intact
(`valid: false`, `metadata_validation`, `schema_sources`) and returns exit 0, writing
`enforcement: "advisory"` into `results.metadata`. A downstream orchestrator then sees that a
derogation was used and **can reject it**. The sanction is suspended; the finding never is.

Three properties make this a procedure rather than a hole:

- **The record is in the artefact, not only in the invocation.** `enforcement` is written by the
  analyzer into the report, so a consumer reading a stored report sees the derogation without
  knowing how the command was typed.
- **The notice is never silenced.** The advisory warning bypasses `--quiet`, unlike the rest of
  the informational output. A derogation the operator asked for is exactly what a later reader
  needs to see.
- **It is read back from the report, not from the flag.** `_exit_if_metadata_invalid` consults
  `results.metadata.enforcement`, so the normal and `--rerun` paths share one rule and the written
  artefact is the single source of truth for what was enforced.

Scope: the derogation covers the metadata contract only. A rule breach with `--fail` still exits
1 — it never masks the verdict on the image.
