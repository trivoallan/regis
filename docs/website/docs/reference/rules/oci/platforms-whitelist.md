---
tags:
  - compatibility
  - rules
---

# platforms-whitelist

Image must only support allowed platforms.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| oci | Warning | compatibility |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `platforms` | `['linux/amd64', 'linux/arm64']` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | All supported platforms are allowed. |
| **Fail** | Image supports disallowed platforms: ${results.oci.platforms_supported} (allowed: ${criterion.params.platforms}). |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: platforms-whitelist
    options:
      platforms:
      - linux/amd64
      - linux/arm64
```

## Condition

```json
{
  "subset": [
    {
      "var": "results.oci.platforms_supported"
    },
    {
      "var": "criterion.params.platforms"
    }
  ]
}
```
