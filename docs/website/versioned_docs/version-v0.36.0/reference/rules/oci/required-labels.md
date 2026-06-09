---
tags:
  - metadata
  - rules
---

# required-labels

Image must have required OCI labels.

| Provider | Level   | Tags     |
| :------- | :------ | :------- |
| oci      | Warning | metadata |

## Parameters

| Name     | Default Value                         | Description |
| :------- | :------------------------------------ | :---------- |
| `labels` | `['org.opencontainers.image.source']` | n/a         |

## Messages

| Type     | Message                                                                   |
| :------- | :------------------------------------------------------------------------ |
| **Pass** | All required labels are present.                                          |
| **Fail** | Image is missing one or more required labels: ${criterion.params.labels}. |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: required-labels
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
          "var": "results.oci.platforms.0.labels"
        }
      ]
    },
    {
      "var": "criterion.params.labels"
    }
  ]
}
```
