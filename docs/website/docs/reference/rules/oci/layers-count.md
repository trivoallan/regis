---
tags:
  - performance
  - rules
---

# layers-count

Image has an acceptable number of layers.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| oci | Warning | performance |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `max_layers` | `30` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | Image has ${results.oci.platforms.0.layers_count} layers. |
| **Fail** | Image has too many layers (${results.oci.platforms.0.layers_count}). Max allowed: ${criterion.params.max_layers}. |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: layers-count
    options:
      max_layers: 30
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.oci.platforms.0.layers_count"
    },
    {
      "var": "criterion.params.max_layers"
    }
  ]
}
```
