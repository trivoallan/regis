# signed-by

Image must carry a verified signature by a listed signer.

| Provider | Level | Tags |
| :--- | :--- | :--- |
| provenance | Critical | supply-chain, signature |

## Parameters

| Name | Default Value | Description |
| :--- | :--- | :--- |
| `signers` | `[]` | n/a |

## Messages

| Type | Message |
| :--- | :--- |
| **Pass** | Image is signed by an accepted signer. |
| **Fail** | No verified signature by an accepted signer (found: ${results.provenance.verified_signers}). |

## Playbook Example

```yaml
rules:
  - provider: provenance
    criterion: signed-by
    options:
      signers: []
```

## Condition

```json
{
  "if": [
    {
      "intersects": [
        {
          "var": "results.provenance.verified_signers"
        },
        {
          "var": "criterion.params.signers"
        }
      ]
    },
    true,
    {
      "and": [
        {
          "var": "results.provenance.signatures_complete"
        },
        false
      ]
    }
  ]
}
```
