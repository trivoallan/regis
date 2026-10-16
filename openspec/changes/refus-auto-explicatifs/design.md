# Design

## Context

See proposal.md for the motivation. Current state, from reading the code:

- The rule entry (`core/domain/rules/evaluator.py`, built around lines 407-435) carries `slug`, `description`, `level`, `tags`, `passed`, `status`, `message` and `analyzers`. It has no field for the observed value or the threshold. The thresholds stay in `rule["params"]` and reach the output only if the `message` template interpolates them.
- `MissingDataTracker` (`core/domain/playbook/context.py`, around lines 91-150) records `accessed_keys` and a single boolean `missing_accessed`. It counts a `KeyError`, a `None` value or a failed `in` check as missing. `playbook/conditions.py` is a second user (tiers and badges).
- Contexts are both flattened and nested. A key access can therefore be recorded either as a flat dotted key or as a nested path. Thresholds appear as `rule.params.*` or `criterion.params.*` (two aliases).
- `adapters/driven/report/html.py` (`_build_context`, around lines 75-82) keeps only `slug`, `level` and `message` for failures and incompletes, and drops `analyzers`.
- `report.html.j2` reads `pb.name` and `pb.verdict` in the playbooks table (lines 209-226), but the evaluator emits `playbook_name`, `playbook_version`, `tier` and `score`. `utils/report.py:240-246` has the same mismatch and also counts `r.get("result") is False`, a field that does not exist (the real one is `passed`).
- `REPORT_SCHEMA_VERSION` is the integer `5` (`core/model/report.py:8`), and `report.schema.json` types it as an integer.

## Goals / Non-Goals

**Goals:**
- Expose what the HTML needs (missing keys always; observed value and threshold when the spike allows it) on the rule entry, so that rendering stays a pure view of `report.json`.
- Keep `uske classify` unaffected: new fields only, no renamed or removed ones.

**Non-Goals:**
- Rewriting the JSON Logic evaluator to trace values through operators.
- Changing the SARIF or Markdown renderers beyond the `utils/report.py` key fix.
- A new report layout. v1 extends the existing triage table (PRD UX option A).

## Decisions

**D1. Read the observed value and the threshold from `accessed_keys`, not from the evaluator.** After the condition runs, keep the deepest accessed keys and resolve them against the nested context. Keys under `results.*` and `request.*` give the observed values; keys under `rule.params.*` and `criterion.params.*` give the threshold, de-duplicated across the two aliases. The spike (`docs/superpowers/specs/2026-10-16-refusal-report-cut-point.md`) found accesses recorded on the nested path only, and found `request.*` facts on `registry-domain-whitelist` and `tag-blacklist`. *Alternative:* instrument each JSON Logic operator to record its operands. This would be exact, but it rewrites the evaluator, so it falls past the cut point.

**D2. Cut point, decided by a spike capped at half a day before 2026-10-25.** There is no cut only if all three hold: D1 works without touching more than one file under `core/domain/rules/` besides the tracker; the pilot playbook reads its thresholds via `rule.params.*` rather than literals in the condition; and the bump to `schemaVersion` 6 is accepted as a pilot-required fix under the freeze. Otherwise it is the cut: `report.json` gains only `missing_keys`, and the pilot playbook's rule `message` templates interpolate the fact and the threshold. The spike writes a dated note in `docs/` that names the branch taken.

**D3. `missing_keys` is a list kept by the tracker next to `missing_accessed`.** The boolean stays, so `conditions.py` is untouched. The list is copied onto the rule entry and is empty unless the status is `incomplete`. It is additive and needs no `schemaVersion` bump on its own. *Alternative:* derive the missing keys from `analyzers`. That is too coarse, because one analyzer can provide some keys and lack others.

**D4. `schemaVersion` 5 → 6 only when there is no cut.** The version is an integer, so a minor bump does not exist. A new observed/threshold field changes the rule contract that consumers may parse, so it gets a version. `missing_keys` alone does not.

**D5. Fix the playbooks table by reading the emitted keys** (`playbook_name`, `playbook_version`, `tier`), and fix `utils/report.py` to count `passed is False`. *Alternative:* add `name`/`verdict` aliases to the evaluator output. That would add two redundant fields to the contract to work around a template bug.

## Risks / Trade-offs

- [The flat and nested access paths record the same key twice] → Normalize to the dotted form and de-duplicate before resolving.
- [`accessed_keys` includes keys the condition read but that did not decide the outcome, for example the branches of an `or`] → Show all accessed `results.*` and `request.*` values. Over-reporting a fact is acceptable to the operator; hiding the deciding one is not.
- [Hard-coded thresholds in a condition do not appear in `accessed_keys`] → The spike checks the pilot playbook. If it has hard-coded thresholds, it takes the cut and the message route.
- [Patching the version pinned by the pilot (0.38.1-full vs 0.39.1-full, roadmap item 3)] → Branch from the pinned version once item 3 decides; the change does not depend on #870.

## Migration Plan

Release a regis patch, pin it by digest in `uske/deploy`, and rerun `uske/tests/test_orchestrator.py` before re-pinning. To roll back, re-pin the previous digest. Report consumers need no migration because the fields are additive.
