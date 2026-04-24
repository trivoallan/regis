---
tags:
  - compatibility
  - rules
---

# platforms-count

Image should support multiple platforms.

| Provider | Level | Tags          |
| :------- | :---- | :------------ |
| skopeo   | Info  | compatibility |

## Parameters

| Name            | Default Value | Description |
| :-------------- | :------------ | :---------- |
| `min_platforms` | `2`           | n/a         |

## Messages

| Type     | Message                                                                                                        |
| :------- | :------------------------------------------------------------------------------------------------------------- |
| **Pass** | Image supports ${results.skopeo.platforms.length} platforms.                                                   |
| **Fail** | Image only supports ${results.skopeo.platforms.length} platforms (min required: ${rule.params.min_platforms}). |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: platforms-count
    options:
      min_platforms: 2
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
