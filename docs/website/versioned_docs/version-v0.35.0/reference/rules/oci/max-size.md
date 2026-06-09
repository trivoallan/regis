---
tags:
  - hygiene
  - rules
---

# max-size

Image size is within limits.

| Provider | Level   | Tags    |
| :------- | :------ | :------ |
| oci      | Warning | hygiene |

## Parameters

| Name     | Default Value | Description |
| :------- | :------------ | :---------- |
| `max_mb` | `1000`        | n/a         |

## Messages

| Type     | Message                                                                                   |
| :------- | :---------------------------------------------------------------------------------------- |
| **Pass** | Image size is within limits (${results.oci.platforms.0.size} bytes).                      |
| **Fail** | Image size exceeds ${criterion.params.max_mb} MB (${results.oci.platforms.0.size} bytes). |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: max-size
    options:
      max_mb: 1000
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.oci.platforms.0.size"
    },
    {
      "*": [
        {
          "var": "criterion.params.max_mb"
        },
        1048576
      ]
    }
  ]
}
```
