---
tags:
  - security
  - rules
---

# registry-domain-whitelist

Checks if requested image registry domain is in the domains list.

| Provider | Level    | Tags     |
| :------- | :------- | :------- |
| core     | Critical | security |

## Parameters

| Name      | Default Value                                                 | Description |
| :-------- | :------------------------------------------------------------ | :---------- |
| `domains` | `['docker.io', 'registry-1.docker.io', 'quay.io', 'ghcr.io']` | n/a         |

## Messages

| Type     | Message                                                                 |
| :------- | :---------------------------------------------------------------------- |
| **Pass** | Image registry domain '${request.registry}' is in the domains list.     |
| **Fail** | Image registry domain '${request.registry}' is not in the domains list. |

## Playbook Example

```yaml
rules:
  - provider: core
    rule: registry-domain-whitelist
    options:
      domains:
        - docker.io
        - registry-1.docker.io
        - quay.io
        - ghcr.io
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
