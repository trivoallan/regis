## Why

In the SNCF admission pilot, the platform operator must answer a contested refusal within the hour from `report.html` alone. Their first question is "which rule?". Today the report shows the failing rule's slug and message, but not the threshold, the image fact or the `ruleset_hash`. The playbook name renders as "—", and an `incomplete` rule reuses the failure message without saying what data was missing. Every contested refusal goes back to the maintainer. Pilot delivery is 2026-11-22 (PRD: `.nanopm/wiki/docs/prds/refus-auto-explicatifs.md`).

## What Changes

- The HTML report shows five fields for every `failed` rule: the rule (slug and description), the image fact (observed value), the threshold (the rule's parameters), the playbook (name and version), and the `ruleset_hash`.
- An `incomplete` rule gets its own label, distinct from failure, and names the missing analyzer or data keys instead of repeating the failure message.
- The "Playbook results" table shows the real playbook name and its result (tier), never "—". The Markdown/utils summary gets the same key fix.
- Each rule entry in the playbook result gains `missing_keys` (additive).
- **Conditional, decided by a half-day spike before 2026-10-25 (cut point):** each rule entry also gains the observed value and the threshold, read from the keys the condition accessed, and `schemaVersion` goes from 5 to 6. If the spike fails, `report.json` keeps its current rule fields plus `missing_keys`. The observed value and threshold are then interpolated into the `message` templates of the pilot playbook's rules.
- Capped at M (5 engineer-days). Out of scope: rewriting the JSON Logic evaluator, SARIF/Markdown propagation of the new fields, a dedicated "why this refusal" panel, and the #870 fix.

## Capabilities

### New Capabilities

- `refusal-report`: what the HTML report must show so a reader can explain a refused or incomplete verdict without the maintainer, and which per-rule fields the playbook result carries to support it.

### Modified Capabilities

## Impact

- `regis/core/domain/playbook/context.py` (missing-data tracking), `regis/core/domain/rules/evaluator.py` (rule entry), `regis/core/domain/playbook/verdict.py`, `regis/adapters/driven/report/html.py`, `regis/templates/html/report.html.j2`, `regis/utils/report.py`, `regis/schemas/playbook/result.schema.json`.
- If there is no cut: `regis/core/model/report.py` (`REPORT_SCHEMA_VERSION` 5 → 6), `report.schema.json`, `tests/test_report_schema_version.py`. Downstream, `uske classify` reads only `playbooks[0].rules[].status/level/slug`, so the new fields are additive-safe; rerun `uske/tests/test_orchestrator.py`.
- If there is a cut: the pilot playbook's rule messages (outside this repo).
- Release: a patch pinnable by digest in `uske/deploy`, within the regis/knock release freeze (pilot-required fixes only).
