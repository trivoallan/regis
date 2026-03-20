---
tags:
  - skopeo
  - rules
---

# skopeo.multi-arch

Checks if the image supports multiple architectures.

| Provider                              | Level | Tags          |
| :------------------------------------ | :---- | :------------ |
| [skopeo](/reference/analyzers/skopeo) | Info  | Compatibility |

## Parameters

| Name            | Default Value |
| :-------------- | :------------ |
| `min_platforms` | `2`           |

## Messages

| Type     | Message                                                                                                        |
| :------- | :------------------------------------------------------------------------------------------------------------- |
| **Pass** | Image supports ${results.skopeo.platforms.length} platforms.                                                   |
| **Fail** | Image only supports ${results.skopeo.platforms.length} platforms (min required: ${rule.params.min_platforms}). |

## Playbook Example

```yaml
rules:
  skopeo.multi-arch:
    params:
      min_platforms: 3
```

## Condition

```json
{
  ">=": [
    {
      "reduce": [
        {
          "var": "results.skopeo.platforms"
        },
        {
          "+": [
            1,
            {
              "var": "accumulator"
            }
          ]
        },
        0
      ]
    },
    {
      "var": "rule.params.min_platforms"
    }
  ]
}
```
