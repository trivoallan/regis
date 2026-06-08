---
tags:
  - compatibility
  - rules
---

# platforms-count

Image should support multiple platforms.

| Provider | Level | Tags          |
| :------- | :---- | :------------ |
| oci      | Info  | compatibility |

## Parameters

| Name            | Default Value | Description |
| :-------------- | :------------ | :---------- |
| `min_platforms` | `2`           | n/a         |

## Messages

| Type     | Message                                                                                                          |
| :------- | :--------------------------------------------------------------------------------------------------------------- |
| **Pass** | Image supports ${results.oci.platforms.length} platforms.                                                        |
| **Fail** | Image only supports ${results.oci.platforms.length} platforms (min required: ${criterion.params.min_platforms}). |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: platforms-count
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
          "var": "results.oci.platforms"
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
      "var": "criterion.params.min_platforms"
    }
  ]
}
```
