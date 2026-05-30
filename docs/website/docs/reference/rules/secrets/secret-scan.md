---
tags:
  - security
  - rules
---

# secret-scan

No secrets or credentials should be embedded in the image.

| Provider | Level    | Tags     |
| :------- | :------- | :------- |
| secrets  | Critical | security |

## Parameters

| Name        | Default Value | Description |
| :---------- | :------------ | :---------- |
| `max_count` | `0`           | n/a         |

## Messages

| Type     | Message                                                                    |
| :------- | :------------------------------------------------------------------------- |
| **Pass** | No secrets detected in the image.                                          |
| **Fail** | TruffleHog detected ${results.secrets.secrets_count} secrets in the image. |

## Playbook Example

```yaml
rules:
  - provider: secrets
    rule: secret-scan
    options:
      max_count: 0
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.secrets.secrets_count"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
