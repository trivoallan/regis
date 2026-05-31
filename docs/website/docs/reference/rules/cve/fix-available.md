---
tags:
  - security
  - rules
---

# fix-available

All vulnerabilities should be fixed if a patch exists.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| cve | Warning | security |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `max_count` | `0` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | All vulnerabilities with available fixes have been patched. |
| **Fail** | Image has ${results.cve.fixed_count} vulnerabilities with available fixes. |

## Playbook Example

```yaml
rules:
  - provider: cve
    rule: fix-available
    options:
      max_count: 0
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.cve.fixed_count"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
