---
tags:
  - core
  - rules
---

# core.registry-domain-whitelist

Checks if requested image registry domain is in the domains list.

| Provider | Level    | Tags     |
| :------- | :------- | :------- |
| core     | critical | security |

## Parameters

| Name      | Default Value                                                 |
| :-------- | :------------------------------------------------------------ |
| `domains` | `['docker.io', 'registry-1.docker.io', 'quay.io', 'ghcr.io']` |

## Messages

| Type     | Message                                                                 |
| :------- | :---------------------------------------------------------------------- |
| **Pass** | Image registry domain '${request.registry}' is in the domains list.     |
| **Fail** | Image registry domain '${request.registry}' is not in the domains list. |

## Playbook Example

```yaml
rules:
  core.registry-domain-whitelist:
    params:
      domains: ["my-registry.com"]
```

## Condition

```json
{
  "in": [
    {
      "var": "request.registry"
    },
    {
      "var": "rule.params.domains"
    }
  ]
}
```
