---
tags:
  - skopeo
  - rules
---

# skopeo.max-size

Checks if the image size is within the allowed limit.

| Provider                              | Level   | Tags    |
| :------------------------------------ | :------ | :------ |
| [skopeo](/reference/analyzers/skopeo) | Warning | Hygiene |

## Parameters

| Name     | Default Value |
| :------- | :------------ |
| `max_mb` | `1000`        |

## Messages

| Type     | Message                                                                                 |
| :------- | :-------------------------------------------------------------------------------------- |
| **Pass** | Image size is within limits (${results.skopeo.platforms.0.size} bytes).                 |
| **Fail** | Image size exceeds ${rule.params.max_mb} MB (${results.skopeo.platforms.0.size} bytes). |

## Playbook Example

```yaml
rules:
  skopeo.max-size:
    params:
      max_mb: 500
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.skopeo.platforms.0.size"
    },
    {
      "*": [
        {
          "var": "rule.params.max_mb"
        },
        1048576
      ]
    }
  ]
}
```
