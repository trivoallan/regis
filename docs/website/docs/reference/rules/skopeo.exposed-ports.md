---
tags:
  - skopeo
  - rules
---

# skopeo.exposed-ports

Checks if exposed ports are allowed.

| Provider                              | Level   | Tags     |
| :------------------------------------ | :------ | :------- |
| [skopeo](/reference/analyzers/skopeo) | Warning | Security |

## Parameters

| Name            | Default Value   |
| :-------------- | :-------------- |
| `allowed_ports` | `["80", "443"]` |

## Messages

| Type     | Message                                                                        |
| :------- | :----------------------------------------------------------------------------- |
| **Pass** | All exposed ports are allowed.                                                 |
| **Fail** | Image exposes unauthorized ports: ${results.skopeo.platforms.0.exposed_ports}. |

## Playbook Example

```yaml
rules:
  skopeo.exposed-ports:
    params:
      allowed_ports: ["80", "443", "8080"]
```

## Condition

```json
{
  "subset": [
    {
      "var": "results.skopeo.platforms.0.exposed_ports"
    },
    {
      "var": "rule.params.allowed_ports"
    }
  ]
}
```
