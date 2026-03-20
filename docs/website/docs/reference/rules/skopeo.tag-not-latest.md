---
tags:
  - skopeo
  - rules
---

# skopeo.tag-not-latest

Ensures the image tag is not `latest`.

| Provider                              | Level   | Tags      |
| :------------------------------------ | :------ | :-------- |
| [skopeo](/reference/analyzers/skopeo) | Warning | Lifecycle |

## Parameters

This rule has no parameters.

## Messages

| Type     | Message                                                              |
| :------- | :------------------------------------------------------------------- |
| **Pass** | Image tag is not 'latest'.                                           |
| **Fail** | Image is using the 'latest' tag. Use immutable version tags instead. |

## Playbook Example

```yaml
rules:
  skopeo.tag-not-latest:
    enable: true
```

## Condition

```json
{
  "!=": [
    {
      "var": "request.tag"
    },
    "latest"
  ]
}
```
