---
tags:
  - compliance
  - licensing
  - rules
---

# license-blocklist

Image must not include components with licenses from the configured blocklist.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| sbom | Critical | compliance, licensing |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `blocklist` | `[]` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | No blocked licenses detected across ${results.sbom.total_components} components. |
| **Fail** | Blocked license(s) detected: ${results.sbom.copyleft_licenses} |

## Playbook Example

```yaml
rules:
  - provider: sbom
    rule: license-blocklist
    options:
      blocklist: []
```

## Condition

```json
{
  "!": [
    {
      "intersects": [
        {
          "var": "results.sbom.licenses"
        },
        {
          "var": "rule.params.blocklist"
        }
      ]
    }
  ]
}
```
