---
tags:
  - sbom
  - rules
---

# sbom.has-sbom

Ensures the image provides a Software Bill of Materials (SBOM).

| Provider                          | Level   | Tags       |
| :-------------------------------- | :------ | :--------- |
| [sbom](/reference/analyzers/sbom) | Warning | Compliance |

## Parameters

This rule has no parameters.

## Messages

| Type     | Message                                             |
| :------- | :-------------------------------------------------- |
| **Pass** | SBOM is available for this image.                   |
| **Fail** | No SBOM could be generated or found for this image. |

## Playbook Example

```yaml
rules:
  sbom.has-sbom:
    enable: true
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
