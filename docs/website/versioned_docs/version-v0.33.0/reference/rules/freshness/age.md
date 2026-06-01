---
tags:
  - freshness
  - rules
---

# age

Image should be less than expected days old.

| Provider  | Level   | Tags      |
| :-------- | :------ | :-------- |
| freshness | Warning | freshness |

## Parameters

| Name       | Default Value | Description |
| :--------- | :------------ | :---------- |
| `max_days` | `30`          | n/a         |

## Messages

| Type     | Message                                                                                   |
| :------- | :---------------------------------------------------------------------------------------- |
| **Pass** | Image is less than ${rule.params.max_days} days old (${results.freshness.age_days} days). |
| **Fail** | Image is older than ${rule.params.max_days} days (${results.freshness.age_days} days).    |

## Playbook Example

```yaml
rules:
  - provider: freshness
    rule: age
    options:
      max_days: 30
```

## Condition

```json
{
  "<": [
    {
      "var": "results.freshness.age_days"
    },
    {
      "var": "rule.params.max_days"
    }
  ]
}
```
