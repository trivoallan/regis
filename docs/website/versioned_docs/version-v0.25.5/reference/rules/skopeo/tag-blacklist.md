---
tags:
  - lifecycle
  - rules
---

# tag-blacklist

Image tag should not be 'latest'.

| Provider | Level   | Tags      |
| :------- | :------ | :-------- |
| skopeo   | Warning | lifecycle |

## Messages

| Type     | Message                                                              |
| :------- | :------------------------------------------------------------------- |
| **Pass** | Image tag is not 'latest'.                                           |
| **Fail** | Image is using the 'latest' tag. Use immutable version tags instead. |

## Playbook Example

```yaml
rules:
  - provider: skopeo
    rule: tag-blacklist
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
