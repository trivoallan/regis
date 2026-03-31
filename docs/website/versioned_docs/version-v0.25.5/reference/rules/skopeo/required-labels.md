---
tags:
  - metadata
  - rules
---

# required-labels

Image must have required OCI labels.

| Provider | Level   | Tags     |
| :------- | :------ | :------- |
| skopeo   | Warning | metadata |

## Parameters

| Name     | Default Value                         | Description |
| :------- | :------------------------------------ | :---------- |
| `labels` | `['org.opencontainers.image.source']` | n/a         |

## Messages

| Type     | Message                                                              |
| :------- | :------------------------------------------------------------------- |
| **Pass** | All required labels are present.                                     |
| **Fail** | Image is missing one or more required labels: ${rule.params.labels}. |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: required-labels
    options:
      labels:
        - org.opencontainers.image.source
```

## Condition

```json
{
  "contains_all": [
    {
      "keys": [
        {
          "var": "results.skopeo.platforms.0.labels"
        }
      ]
    },
    {
      "var": "rule.params.labels"
    }
  ]
}
```
