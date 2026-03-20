---
tags:
  - scorecard
  - rules
---

# scorecard.min-score

Ensures the OpenSSF Scorecard score for the source repository is above a certain threshold.

| Provider                                          | Level   | Tags     |
| :------------------------------------------------ | :------ | :------- |
| [scorecarddev](/reference/analyzers/scorecarddev) | Warning | Security |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `min_score` | `5.0`         |

## Messages

| Type     | Message                                                                                             |
| :------- | :-------------------------------------------------------------------------------------------------- |
| **Pass** | Scorecard score is ${results.scorecarddev.score} (min required: ${rule.params.min_score}).          |
| **Fail** | Scorecard score is too low: ${results.scorecarddev.score} (min required: ${rule.params.min_score}). |

## Playbook Example

```yaml
rules:
  scorecard.min-score:
    params:
      min_score: 7.0
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
