---
tags:
  - freshness
  - rules
---

# freshness.age

Fails if the image is older than a specified number of days.

| Provider                                    | Level   | Tags      |
| :------------------------------------------ | :------ | :-------- |
| [freshness](/reference/analyzers/freshness) | Warning | Lifecycle |

## Parameters

| Name       | Default Value |
| :--------- | :------------ |
| `max_days` | `30`          |

## Messages

| Type     | Message                                                                                      |
| :------- | :------------------------------------------------------------------------------------------- |
| **Pass** | Image is ${results.freshness.age_days} days old (max allowed: ${rule.params.max_days}).      |
| **Fail** | Image is too old (${results.freshness.age_days} days). Max allowed: ${rule.params.max_days}. |

## Playbook Example

```yaml
rules:
  freshness.age:
    params:
      max_days: 60
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.freshness.age_days"
    },
    {
      "var": "rule.params.max_days"
    }
  ]
}
```
