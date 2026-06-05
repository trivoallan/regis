---
tags:
  - security
  - rules
---

# severity-count

Max allowed issues for a given severity level.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| dockle | Warning | security |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `level` | `FATAL` | n/a |
| `max_count` | `0` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | Dockle ${criterion.params.level} issues are within limits. |
| **Fail** | Dockle found ${results.dockle.issues_by_level.${criterion.params.level}} ${criterion.params.level} issues (max allowed: ${criterion.params.max_count}). |

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
          "var": "criterion.params.level"
        }
      ]
    },
    {
      "var": "criterion.params.max_count"
    }
  ]
}
```
