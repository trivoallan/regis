---
tags:
  - skopeo
  - rules
---

# skopeo.no-root

Checks if the image is configured to run as a non-root user.

| Provider                              | Level    | Tags     |
| :------------------------------------ | :------- | :------- |
| [skopeo](/reference/analyzers/skopeo) | Critical | Security |

## Parameters

| Name             | Default Value |
| :--------------- | :------------ |
| `forbidden_user` | `"root"`      |

## Messages

| Type     | Message                                                     |
| :------- | :---------------------------------------------------------- |
| **Pass** | Image does not run as '${rule.params.forbidden_user}'.      |
| **Fail** | Image configured to run as '${rule.params.forbidden_user}'. |

## Playbook Example

```yaml
rules:
  skopeo.no-root:
    params:
      forbidden_user: "0"
```

## Condition

```json
{
  "!=": [
    {
      "var": "results.skopeo.platforms.0.user"
    },
    {
      "var": "rule.params.forbidden_user"
    }
  ]
}
```
