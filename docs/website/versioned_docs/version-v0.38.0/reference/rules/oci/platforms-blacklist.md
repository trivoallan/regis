---
tags:
  - compatibility
  - rules
---

# platforms-blacklist

Image must not support forbidden platforms.

| Provider | Level   | Tags          |
| :------- | :------ | :------------ |
| oci      | Warning | compatibility |

## Parameters

| Name        | Default Value       | Description |
| :---------- | :------------------ | :---------- |
| `platforms` | `['windows/amd64']` | n/a         |

## Messages

| Type     | Message                                                                                                            |
| :------- | :----------------------------------------------------------------------------------------------------------------- |
| **Pass** | Image supports no forbidden platforms.                                                                             |
| **Fail** | Image supports forbidden platforms: ${results.oci.platforms_supported} (forbidden: ${criterion.params.platforms}). |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: platforms-blacklist
    options:
      platforms:
        - windows/amd64
```

## Condition

```json
{
  "!": {
    "intersects": [
      {
        "var": "results.oci.platforms_supported"
      },
      {
        "var": "criterion.params.platforms"
      }
    ]
  }
}
```
