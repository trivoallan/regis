---
tags:
  - security
  - rules
---

# env-blacklist

Image must not contain forbidden environment variables.

| Provider | Level    | Tags     |
| :------- | :------- | :------- |
| skopeo   | Critical | security |

## Parameters

| Name   | Default Value             | Description |
| :----- | :------------------------ | :---------- |
| `keys` | `['DEBUG', 'SECRET_KEY']` | n/a         |

## Messages

| Type     | Message                                                     |
| :------- | :---------------------------------------------------------- |
| **Pass** | No forbidden environment variables found.                   |
| **Fail** | Image contains one or more forbidden environment variables. |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: env-blacklist
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
        "var": "results.skopeo.platforms.0.env"
      },
      {
        "var": "rule.params.keys"
      }
    ]
  }
}
```
