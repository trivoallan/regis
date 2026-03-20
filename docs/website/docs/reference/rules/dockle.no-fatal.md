---
tags:
  - dockle
  - rules
---

# dockle.no-fatal

Fails if [dockle](/reference/analyzers/dockle) finds fatal issues.

| Provider                              | Level    | Tags     |
| :------------------------------------ | :------- | :------- |
| [dockle](/reference/analyzers/dockle) | Critical | Security |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `max_count` | `0`           |

## Messages

| Type     | Message                                                                                                    |
| :------- | :--------------------------------------------------------------------------------------------------------- |
| **Pass** | Image has no critical CVEs.                                                                                |
| **Fail** | Dockle found ${results.dockle.issues_by_level.FATAL} fatal issues (max allowed: ${rule.params.max_count}). |

## Playbook Example

```yaml
rules:
  dockle.no-fatal:
    enable: true
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.dockle.issues_by_level.FATAL"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
