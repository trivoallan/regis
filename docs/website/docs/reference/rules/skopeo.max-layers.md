---
tags:
  - skopeo
  - rules
---

# skopeo.max-layers

Checks if the number of image layers is below the limit.

| Provider                              | Level   | Tags        |
| :------------------------------------ | :------ | :---------- |
| [skopeo](/reference/analyzers/skopeo) | Warning | Performance |

## Parameters

| Name         | Default Value |
| :----------- | :------------ |
| `max_layers` | `30`          |

## Messages

| Type     | Message                                                                                                         |
| :------- | :-------------------------------------------------------------------------------------------------------------- |
| **Pass** | Image has ${results.skopeo.platforms.0.layers_count} layers.                                                    |
| **Fail** | Image has too many layers (${results.skopeo.platforms.0.layers_count}). Max allowed: ${rule.params.max_layers}. |

## Playbook Example

```yaml
rules:
  skopeo.max-layers:
    params:
      max_layers: 20
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.skopeo.platforms.0.layers_count"
    },
    {
      "var": "rule.params.max_layers"
    }
  ]
}
```
