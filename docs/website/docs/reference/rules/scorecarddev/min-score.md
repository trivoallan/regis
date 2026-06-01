---
tags:
  - security
  - rules
---

# min-score

OpenSSF Scorecard score is above the threshold.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| scorecarddev | Warning | security |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `min_score` | `5.0` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | Scorecard score is ${results.scorecarddev.score} (min required: ${rule.params.min_score}). |
| **Fail** | Scorecard score is too low: ${results.scorecarddev.score} (min required: ${rule.params.min_score}). |

## Playbook Example

```yaml
rules:
  - provider: scorecarddev
    rule: min-score
    options:
      min_score: 5.0
```

## Condition

```json
{
  ">=": [
    {
      "var": "results.scorecarddev.score"
    },
    {
      "var": "rule.params.min_score"
    }
  ]
}
```
