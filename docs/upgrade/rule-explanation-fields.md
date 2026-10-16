# Rule explanation fields: `schemaVersion` 6

Starting with report `schemaVersion: 6`, each rule entry in a playbook result
says what its condition read. A reader can explain a failed or incomplete rule
from the report alone, without re-running the analysis.

## What changed

Every item of `playbooks[].rules[]` gains three fields:

| Field | Type | Content |
|---|---|---|
| `observed` | object | The image facts the condition read, keyed by dotted path (`results.cve.fixed_count`, `request.tag`). Lists over 10 items, lists of objects, and objects are summarized as `"<list of N>"` or `"<object with N keys>"`. |
| `threshold` | object | The rule parameters the condition read, keyed by parameter name (`max_count`, `max_days`). It is empty when the criterion's condition hard-codes its threshold (for example `tag-blacklist`); the rule's message then names it. |
| `missing_keys` | array of strings | The data keys the condition needed but could not read (`results.sbom`). It is empty unless `status` is `incomplete`. |

The HTML report shows these fields for each failed or incomplete rule, together
with the playbook's name, its version and its `ruleset_hash`.

## Action required

None. The fields are additive: `slug`, `status`, `level`, `passed` and
`message` are unchanged. Consumers that want the new fields should gate on
`schemaVersion >= 6`.
