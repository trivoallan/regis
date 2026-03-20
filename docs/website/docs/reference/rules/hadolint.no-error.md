---
tags:
  - hadolint
  - rules
---

# hadolint.no-error

Fails if [hadolint](/reference/analyzers/hadolint) finds any 'error' level violations in the pseudo-Dockerfile.

| Provider                                  | Level    | Tags           |
| :---------------------------------------- | :------- | :------------- |
| [hadolint](/reference/analyzers/hadolint) | Critical | Best Practices |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `max_count` | `0`           |

## Messages

| Type     | Message                                                          |
| :------- | :--------------------------------------------------------------- |
| **Pass** | No hadolint errors detected.                                     |
| **Fail** | Hadolint found ${results.hadolint.issues_by_level.error} errors. |

## Playbook Example

```yaml
rules:
  hadolint.no-error:
    enable: true
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.hadolint.issues_by_level.error"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
