---
tags:
  - hadolint
  - rules
---

# hadolint.max-warnings

Limits the number of 'warning' level violations found by [hadolint](/reference/analyzers/hadolint).

| Provider                                  | Level   | Tags           |
| :---------------------------------------- | :------ | :------------- |
| [hadolint](/reference/analyzers/hadolint) | Warning | Best Practices |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `max_count` | `5`           |

## Messages

| Type     | Message                                                                                                 |
| :------- | :------------------------------------------------------------------------------------------------------ |
| **Pass** | Hadolint warnings are within limits.                                                                    |
| **Fail** | Too many hadolint warnings: ${results.hadolint.issues_by_level.warning} (max ${rule.params.max_count}). |

## Playbook Example

```yaml
rules:
  hadolint.max-warnings:
    params:
      max_count: 10
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.hadolint.issues_by_level.warning"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
