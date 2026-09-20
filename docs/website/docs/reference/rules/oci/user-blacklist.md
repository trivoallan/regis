---
tags:
  - security
  - rules
---

# user-blacklist

Image must not run as root.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| oci | Critical | security |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `forbidden_user` | `root` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | Image does not run as '${criterion.params.forbidden_user}'. |
| **Fail** | Image configured to run as '${criterion.params.forbidden_user}'. |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: user-blacklist
    options:
      forbidden_user: root
```

## Condition

```json
{
  "!=": [
    {
      "var": "results.oci.platforms.0.user"
    },
    {
      "var": "criterion.params.forbidden_user"
    }
  ]
}
```
