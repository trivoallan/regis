# Refusal report: cut-point spike

Date: 2026-10-16. Change: `openspec/changes/refus-auto-explicatifs` (task 1, design D1/D2).

## Question

Can the HTML report show a refused rule's observed value and threshold without rewriting the JSON Logic evaluator? Design D2 avoids the cut (falling back to interpolated messages, with `report.json` unchanged) only if all three of these conditions hold:

1. D1 works: the observed value and the threshold can be read from `MissingDataTracker.accessed_keys` without touching more than one file under `core/domain/rules/` besides the tracker.
2. The pilot playbooks read their thresholds through `rule.params.*`/`criterion.params.*`, not as literals in a condition.
3. Moving `schemaVersion` from 5 to 6 is accepted as a pilot-required fix under the release freeze.

## Method

A throwaway script (not committed) re-ran each enabled rule's condition through `MissingDataTracker`, the way `evaluate_rules` does. It kept the deepest accessed keys and resolved them against the nested context:

- `results.*` and `request.*` give observed facts;
- `criterion.params.*` gives the threshold;
- a key that resolves to nothing, or to `None`, counts as missing.

Inputs: `tests/fixtures/report.v3.json` (analyzers `cve`, `oci`), the built-in default playbook, and the two pilot playbooks in `reference/playbooks/` (`admission`, `version`, revision `3b1fa08`).

## Results

### Condition 1: holds

Every access is recorded on the nested path (`criterion.params.max_count`, `results.cve.fixed_count`). No flat/nested duplicate showed up, because conditions use dotted `var` paths that the tracker walks level by level. Rules read their parameters through the `criterion` alias only.

Sample, version playbook:

| Rule | Status | Observed fact | Threshold | Missing |
|---|---|---|---|---|
| `cve-fixable` | failed | `results.cve.fixed_count = 5` | `max_count = 0` | — |
| `cve-critical` | passed | `results.cve.critical_count = 0` | `level = critical`, `max_count = 0` | — |
| `cve-high` | passed | `results.cve.high_count = 1` | `level = high`, `max_count = 10` | — |
| `no-root` | passed | `results.oci.platforms` (list of 1) | `forbidden_user = root` | — |
| `freshness` | incomplete | — | `max_days = 90` | `results.freshness` |
| `no-licence-toxique` | incomplete | — | `blocklist = [GPL-2.0-only, …]` | `results.sbom` |
| `no-secret`, `secrets-non-verifies` | incomplete | — | — | `results.secrets` |
| `bonnes-pratiques` | incomplete | — | `level = FATAL`, `max_count = 0` | `results.dockle` |

The implementation needs the rule entry in `core/domain/rules/evaluator.py` plus the tracker in `core/domain/playbook/context.py`, and nothing else under `core/domain/rules/`.

Two adjustments to D1:

- Facts are not only under `results.*`. `registry-domain-whitelist` reads `request.registry`, and `tag-blacklist` reads `request.tag`, so the fact filter must take `request.*` as well.
- Some facts are lists or objects (`results.oci.platforms`). Show them as-is or summarized; it is not a blocker.

### Condition 2: holds for 12 of 13 pilot rules

Every rule in both pilot playbooks is a catalogue criterion with `options` (no inline rule conditions), so their thresholds arrive as `params`. The one exception is `tag-blacklist` (`no-latest`, level critical), whose catalogue condition hard-codes the literal (`{"!=": [{"var": "request.tag"}, "latest"]}`, `core/domain/analyzers/oci.py:108`). Its threshold is therefore invisible to `accessed_keys`. Its fail message already names it: "Image is using the 'latest' tag."

Rules with no numeric threshold by nature (`has-sbom`, `verified-secrets`, `secret-scan`) show none; their description is the threshold.

### Condition 3: holds

The maintainer accepted the `schemaVersion` bump to 6 as a pilot-required fix under the freeze (2026-10-16).

## Branch

**No cut.**

- Read facts from `results.*` and `request.*`, and thresholds from `criterion.params.*`.
- For rules without params (`tag-blacklist`), the rule's fail message carries the threshold, and the five-field grid accepts that.
- Making `tag-blacklist` take a parameter is a catalogue change and stays out of scope.

Had condition 3 been refused, it would have been the cut: `report.json` gains only `missing_keys` (additive, no version bump), and the pilot playbooks' rule messages would have interpolated the fact and the threshold.

Decision on condition 3: **accepted** (Tristan Rivoallan, 2026-10-16). Branch taken: **no cut**. `schemaVersion` goes to 6.
