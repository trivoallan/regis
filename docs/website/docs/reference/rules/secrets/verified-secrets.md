---
tags:
  - security
  - rules
---

# verified-secrets

No verified, active credentials should be embedded in the image.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| secrets | Critical | security |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | No verified secrets detected in the image. |
| **Fail** | TruffleHog verified ${results.secrets.verified_count} active credential(s) in the image. |

## Playbook Example

```yaml
rules:
  - provider: secrets
    criterion: verified-secrets
```

## Condition

```json
{
  "==": [
    {
      "var": "results.secrets.verified_count"
    },
    0
  ]
}
```
