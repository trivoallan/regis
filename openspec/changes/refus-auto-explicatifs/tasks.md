# Tasks

Build plan: Wave 0 is T1 and T2 in parallel. Wave 1 is T3 (after T1). Wave 2 is T4 (after T2 and T3) and T5 (after T1 and T3) in parallel. Wave 3 is T6. T2 and T4 both edit `report.html.j2` (different sections), so merge T2 first. Critical path: T1 → T3 → T4 → T6. Cap: 5 engineer-days.

## 1. Cut-point spike (T1, S, Wave 0)

- [x] 1.1 Prototype D1 on one pilot rule (resolve `accessed_keys` to observed values under `results.*` and `request.*` and thresholds under `rule.params.*`/`criterion.params.*`), timeboxed to half a day; verify by printing the resolved fact and threshold for a failed and an incomplete rule
- [x] 1.2 Check whether the pilot playbook reads its thresholds via `rule.params.*` or hard-codes them in conditions; verify by listing each rule and its threshold source in the note
- [x] 1.3 Write a dated note in `docs/` that records the three D2 conditions and the branch taken (no cut, or cut); verify that the note exists and names the branch

## 2. Playbook results table (T2, S, Wave 0)

- [x] 2.1 Make `report.html.j2` read `playbook_name`, `playbook_version` and `tier` in the playbooks table (lines 209-226), and count failures as not passed and not incomplete; verify with a new `tests/report/test_html_playbooks.py` asserting the name and the tier appear and no "—" is rendered for a named playbook
- [x] 2.2 Fix `regis/utils/report.py:240-246` to read `playbook_name`/`tier` and count failures that are not incomplete; verify with a unit test on the summary output (landed upstream in #880)

## 3. Per-rule fields (T3, L, Wave 1, after T1)

- [x] 3.1 Add a `missing_keys` list to `MissingDataTracker`, filled wherever `missing_accessed` is set, leaving the boolean and `conditions.py` unchanged; verify with tracker unit tests covering KeyError, None and `in`
- [x] 3.2 Copy `missing_keys` onto the rule entry in `rules/evaluator.py` (empty unless the status is `incomplete`), and add it to `result.schema.json`; verify with an evaluator test on an incomplete rule and a schema validation test
- [x] 3.3 If T1 found no cut: add the observed values and threshold to the rule entry per D1 (normalized, de-duplicated keys) and to `result.schema.json`; verify with evaluator tests on a numeric-threshold rule and on the flat/nested alias case
- [x] 3.4 Carry `description`, `analyzers`, `missing_keys` (and the observed/threshold fields if present) through `RuleLine`/`_line` in `verdict.py` and `_build_context` in `html.py`, along with the playbook name, version and `ruleset_hash`; verify with an extension of `tests/report/test_html_context.py`

## 4. Triage table rendering (T4, M, Wave 2, after T2 and T3)

- [ ] 4.1 Render the five fields for each failed rule in the triage table of `report.html.j2` (lines 181-199), with the incomplete rows using a distinct label and listing `missing_keys`; verify by rendering a sample report
- [ ] 4.2 Add `tests/report/test_html_refusal.py`, which fails if any of the five fields is missing from the HTML of a failed rule or if an incomplete rule lacks its label or its missing keys; verify that `make test` passes with the per-file coverage at or above 90%

## 5. Contract or message route (T5, S, Wave 2, after T1 and T3)

- [ ] 5.1 No cut: bump `REPORT_SCHEMA_VERSION` to 6 in `core/model/report.py` and `report.schema.json`, and update `tests/test_report_schema_version.py`; verify that `make test` passes and that `uske/tests/test_orchestrator.py` passes against a report produced by the branch
- [ ] 5.2 Cut: interpolate the observed fact and threshold into the `message` templates of the pilot playbook's rules; verify by analyzing a known-refused image and checking that the rendered message contains both

## 6. Pilot audit (T6, S, Wave 3, after T4 and T5)

- [ ] 6.1 Run `make lint`, `make test` and `make image`, then release the patch and pin it by digest in `uske/deploy`; verify that the pilot `CronWorkflow` runs with the new digest
- [ ] 6.2 Audit every refusal `report.html` logged during the pilot (`policies/**/*.journal.jsonl`) against the five-field grid, and write a dated conformity note in `docs/`; verify that the note reports a conformity rate (target 100% by 2026-11-22)
