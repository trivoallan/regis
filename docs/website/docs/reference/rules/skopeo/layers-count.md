---
tags:
  - performance
  - rules
---

# layers-count

Image has an acceptable number of layers.

| Provider | Level   | Tags        |
| :------- | :------ | :---------- |
| skopeo   | Warning | performance |

## Parameters

| Name         | Default Value | Description |
| :----------- | :------------ | :---------- |
| `max_layers` | `30`          | n/a         |

## Messages

| Type     | Message                                                                                                         |
| :------- | :-------------------------------------------------------------------------------------------------------------- |
| **Pass** | Image has ${results.skopeo.platforms.0.layers_count} layers.                                                    |
| **Fail** | Image has too many layers (${results.skopeo.platforms.0.layers_count}). Max allowed: ${rule.params.max_layers}. |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: layers-count
    options:
      max_layers: 30
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
