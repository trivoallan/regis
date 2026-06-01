---
tags:
  - security
  - rules
---

# severity-count

Max allowed issues for a given severity level.

| Provider | Level   | Tags     |
| :------- | :------ | :------- |
| dockle   | Warning | security |

## Parameters

| Name        | Default Value | Description |
| :---------- | :------------ | :---------- |
| `level`     | `FATAL`       | n/a         |
| `max_count` | `0`           | n/a         |

## Messages

| Type     | Message                                                                                                                                  |
| :------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| **Pass** | Dockle ${rule.params.level} issues are within limits.                                                                                    |
| **Fail** | Dockle found ${results.dockle.issues_by_level.${rule.params.level}} ${rule.params.level} issues (max allowed: ${rule.params.max_count}). |

## Playbook Example

```yaml
rules:
  - provider: dockle
    rule: severity-count
    options:
      level: FATAL
      max_count: 0
```

## Condition

```json
{
  "<=": [
    {
      "get": [
        {
          "var": "results.dockle.issues_by_level"
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
