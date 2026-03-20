---
tags:
  - trivy
  - rules
---

# trivy.secret-scan

Fails if secrets or credentials are found in the image.

| Provider                            | Level    | Tags     |
| :---------------------------------- | :------- | :------- |
| [trivy](/reference/analyzers/trivy) | Critical | Security |

## Parameters

| Name        | Default Value |
| :---------- | :------------ |
| `max_count` | `0`           |

## Messages

| Type     | Message                                                                            |
| :------- | :--------------------------------------------------------------------------------- |
| **Pass** | No secrets detected in the image.                                                  |
| **Fail** | Trivy detected ${results.trivy.secrets_count} secrets or credentials in the image. |

## Playbook Example

```yaml
rules:
  trivy.secret-scan:
    enable: true
```

## Condition

```json
{
  "<=": [
    {
      "var": "results.trivy.secrets_count"
    },
    {
      "var": "rule.params.max_count"
    }
  ]
}
```
