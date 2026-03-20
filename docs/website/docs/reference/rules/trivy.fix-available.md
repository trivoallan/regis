---
tags:
  - trivy
  - rules
---

# trivy.fix-available

Fails if vulnerabilities with available fixes are found.

| Provider                            | Level   | Tags     |
| :---------------------------------- | :------ | :------- |
| [trivy](/reference/analyzers/trivy) | Warning | Security |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `max_count` | `0`           |

## Messages

| Type     | Message                                                                      |
| :------- | :--------------------------------------------------------------------------- |
| **Pass** | All vulnerabilities with available fixes have been patched.                  |
| **Fail** | Image has ${results.trivy.fixed_count} vulnerabilities with available fixes. |

## Playbook Example

```yaml
rules:
  trivy.fix-available:
    params:
      max_count: 5
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.trivy.fixed_count"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
