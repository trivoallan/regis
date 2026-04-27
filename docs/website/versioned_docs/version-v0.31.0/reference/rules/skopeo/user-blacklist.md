---
tags:
  - security
  - rules
---

# user-blacklist

Image must not run as root.

| Provider | Level    | Tags     |
| :------- | :------- | :------- |
| skopeo   | Critical | security |

## Parameters

| Name             | Default Value | Description |
| :--------------- | :------------ | :---------- |
| `forbidden_user` | `root`        | n/a         |

## Messages

| Type     | Message                                                     |
| :------- | :---------------------------------------------------------- |
| **Pass** | Image does not run as '${rule.params.forbidden_user}'.      |
| **Fail** | Image configured to run as '${rule.params.forbidden_user}'. |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: user-blacklist
    options:
      forbidden_user: root
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
