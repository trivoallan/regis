---
tags:
  - dockle
  - rules
---

# dockle.max-warnings

Too many [dockle](/reference/analyzers/dockle) warnings found.

| Provider                              | Level   | Tags     |
| :------------------------------------ | :------ | :------- |
| [dockle](/reference/analyzers/dockle) | Warning | Security |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `max_count` | `5`           |

## Messages

| Type     | Message                                                                                               |
| :------- | :---------------------------------------------------------------------------------------------------- |
| **Pass** | Dockle warnings are within acceptable limits (${results.dockle.issues_by_level.WARN}).                |
| **Fail** | Dockle found ${results.dockle.issues_by_level.WARN} warnings (max allowed: ${rule.params.max_count}). |

## Playbook Example

```yaml
rules:
  dockle.max-warnings:
    params:
      max_count: 10
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.dockle.issues_by_level.WARN"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
