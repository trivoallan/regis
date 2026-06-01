---
tags:
  - security
  - rules
---

# exposed-ports-whitelist

Image exposes permitted ports.

| Provider | Level   | Tags     |
| :------- | :------ | :------- |
| oci      | Warning | security |

## Parameters

| Name            | Default Value   | Description |
| :-------------- | :-------------- | :---------- |
| `allowed_ports` | `['80', '443']` | n/a         |

## Messages

| Type     | Message                                                                     |
| :------- | :-------------------------------------------------------------------------- |
| **Pass** | All exposed ports are allowed.                                              |
| **Fail** | Image exposes unauthorized ports: ${results.oci.platforms.0.exposed_ports}. |

## Playbook Example

```yaml
rules:
  - provider: oci
    rule: exposed-ports-whitelist
    options:
      allowed_ports:
        - "80"
        - "443"
```

## Condition

```json
{
  "subset": [
    {
      "var": "results.oci.platforms.0.exposed_ports"
    },
    {
      "var": "rule.params.allowed_ports"
    }
  ]
}
```
