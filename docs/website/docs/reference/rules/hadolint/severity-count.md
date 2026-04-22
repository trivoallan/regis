---
tags:
  - best-practices
  - rules
---

# severity-count

Max allowed violations for a given severity level.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| hadolint | Warning | best-practices |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `level` | `error` | n/a |
| `max_count` | `0` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | Hadolint ${rule.params.level} issues are within limits. |
| **Fail** | Hadolint found ${results.hadolint.issues_by_level.${rule.params.level}} ${rule.params.level} issues (max allowed: ${rule.params.max_count}). |

## Playbook Example

```yaml
rules:
  - provider: hadolint
    rule: severity-count
    options:
      level: error
      max_count: 0
```

## Condition

```json
{
  "<=": [
    {
      "get": [
        {
          "var": "results.hadolint.issues_by_level"
        },
        {
          "var": "rule.params.level"
        }
      ]
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
