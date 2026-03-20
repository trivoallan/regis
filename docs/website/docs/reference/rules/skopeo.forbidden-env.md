---
tags:
  - skopeo
  - rules
---

# skopeo.forbidden-env

Checks if forbidden environment variables are present in the image config.

| Provider                              | Level    | Tags     |
| :------------------------------------ | :------- | :------- |
| [skopeo](/reference/analyzers/skopeo) | Critical | Security |

## Parameters

| Name   | Default Value             |
| :----- | :------------------------ |
| `keys` | `["DEBUG", "SECRET_KEY"]` |

## Messages

| Type     | Message                                                     |
| :------- | :---------------------------------------------------------- |
| **Pass** | No forbidden environment variables found.                   |
| **Fail** | Image contains one or more forbidden environment variables. |

## Playbook Example

```yaml
rules:
  skopeo.forbidden-env:
    params:
      keys: ["PASSWORD", "TOKEN"]
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
