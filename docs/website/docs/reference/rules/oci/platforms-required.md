---
tags:
  - compatibility
  - rules
---

# platforms-required

Image must support a required set of platforms.

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
| **Pass** | Image supports all required platforms. |
| **Fail** | Image is missing required platforms (supported: ${results.oci.platforms_supported}; required: ${criterion.params.platforms}). |

## Playbook Example

```yaml
rules:
  - provider: oci
    criterion: platforms-required
    options:
      platforms:
      - linux/amd64
      - linux/arm64
```

## Condition

```json
{
  "contains_all": [
    {
      "var": "results.oci.platforms_supported"
    },
    {
      "var": "criterion.params.platforms"
    }
  ]
}
```
