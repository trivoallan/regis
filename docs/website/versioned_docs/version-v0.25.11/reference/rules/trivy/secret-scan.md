---
tags:
  - security
  - rules
---

# secret-scan

No secrets or credentials should be embedded in the image.

| Provider | Level    | Tags     |
| :------- | :------- | :------- |
| trivy    | Critical | security |

## Parameters

| Name        | Default Value | Description |
| :---------- | :------------ | :---------- |
| `max_count` | `0`           | n/a         |

## Messages

| Type     | Message                                                                            |
| :------- | :--------------------------------------------------------------------------------- |
| **Pass** | No secrets detected in the image.                                                  |
| **Fail** | Trivy detected ${results.trivy.secrets_count} secrets or credentials in the image. |

## Playbook Example

```yaml
rules:
  - provider: trivy
    rule: secret-scan
    options:
      max_count: 0
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.trivy.secrets_count"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
