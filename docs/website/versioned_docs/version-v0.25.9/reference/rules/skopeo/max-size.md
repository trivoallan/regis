---
tags:
  - hygiene
  - rules
---

# max-size

Image size is within limits.

| Provider | Level   | Tags    |
| :------- | :------ | :------ |
| skopeo   | Warning | hygiene |

## Parameters

| Name     | Default Value | Description |
| :------- | :------------ | :---------- |
| `max_mb` | `1000`        | n/a         |

## Messages

| Type     | Message                                                                                 |
| :------- | :-------------------------------------------------------------------------------------- |
| **Pass** | Image size is within limits (${results.skopeo.platforms.0.size} bytes).                 |
| **Fail** | Image size exceeds ${rule.params.max_mb} MB (${results.skopeo.platforms.0.size} bytes). |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: max-size
    options:
      max_mb: 1000
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
