---
tags:
  - security
  - rules
---

# env-blacklist

Image must not contain forbidden environment variables.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| oci | Critical | security |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `keys` | `['DEBUG', 'SECRET_KEY']` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | No forbidden environment variables found. |
| **Fail** | Image contains one or more forbidden environment variables. |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: env-blacklist
    options:
      keys:
      - DEBUG
      - SECRET_KEY
```

## Condition

```json
{
  "!": {
    "env_contains": [
      {
        "var": "results.oci.platforms.0.env"
      },
      {
        "var": "criterion.params.keys"
      }
    ]
  }
}
```
