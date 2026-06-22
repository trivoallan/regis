---
tags:
  - security
  - rules
---

# secret-scan

No secrets or credentials should be embedded in the image.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| secrets | Warning | security |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | No secrets detected in the image. |
| **Fail** | TruffleHog detected ${results.secrets.secrets_count} secret(s) in the image. |

## Playbook Example

```yaml
rules:
  - provider: secrets
    criterion: secret-scan
```

## Condition

```json
{
  "==": [
    {
      "var": "results.secrets.secrets_count"
    },
    0
  ]
}
```
