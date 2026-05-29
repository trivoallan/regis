---
tags:
  - compliance
  - rules
---

# has-sbom

Image must provide a Software Bill of Materials.

| Provider | Level   | Tags       |
| :------- | :------ | :--------- |
| sbom     | Warning | compliance |

## Messages

| Type     | Message                                             |
| :------- | :-------------------------------------------------- |
| **Pass** | SBOM is available for this image.                   |
| **Fail** | No SBOM could be generated or found for this image. |

## Playbook Example

```yaml
rules:
  - provider: sbom
    rule: has-sbom
```

## Condition

```json
{
  "==": [
    {
      "var": "results.sbom.has_sbom"
    },
    true
  ]
}
```
