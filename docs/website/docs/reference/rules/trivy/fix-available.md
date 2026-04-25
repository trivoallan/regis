---
tags:
  - security
  - rules
---

# fix-available

All vulnerabilities should be fixed if a patch exists.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| trivy | Warning | security |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `max_count` | `0` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | All vulnerabilities with available fixes have been patched. |
| **Fail** | Image has ${results.trivy.fixed_count} vulnerabilities with available fixes. |

## Playbook Example

```yaml
rules:
  - provider: trivy
    rule: fix-available
    options:
      max_count: 0
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
