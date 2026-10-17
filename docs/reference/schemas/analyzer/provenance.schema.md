# provenance.output

**Title:** provenance.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Build provenance and supply-chain attestation information.

| Property                                         | Pattern | Type            | Deprecated | Definition | Title/Description                                                                                                                                                                            |
| ------------------------------------------------ | ------- | --------------- | ---------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| + [analyzer](#analyzer )                         | No      | const           | No         | -          | Unique identifier for the Provenance analyzer.                                                                                                                                               |
| + [repository](#repository )                     | No      | string          | No         | -          | The image repository that was analyzed.                                                                                                                                                      |
| + [tag](#tag )                                   | No      | string          | No         | -          | The image tag that was analyzed.                                                                                                                                                             |
| + [has_provenance](#has_provenance )             | No      | boolean         | No         | -          | True if SLSA provenance or build attestations were found.                                                                                                                                    |
| + [has_cosign_signature](#has_cosign_signature ) | No      | boolean         | No         | -          | True if at least one cosign signature (legacy tag or Sigstore bundle referrer) was discovered on the digest the reference resolves to. Discovery alone, not proof: see \`verified_signers\`. |
| - [signatures](#signatures )                     | No      | array of object | No         | -          | Signatures discovered on the subject digest.                                                                                                                                                 |
| - [verified_signers](#verified_signers )         | No      | array of object | No         | -          | Distinct signers of verified signatures, matched by the \`signed-by\` criterion.                                                                                                             |
| - [signatures_complete](#signatures_complete )   | No      | boolean or null | No         | -          | True when every lookup and verification ran; null when one could not (see \`signature_gaps\`).                                                                                               |
| - [signature_gaps](#signature_gaps )             | No      | array of string | No         | -          | Lookups or verifications that could not run (registry error, cosign missing, trust root unreachable).                                                                                        |
| + [source_tracked](#source_tracked )             | No      | boolean         | No         | -          | True if the source repository URL is tracked in metadata.                                                                                                                                    |
| + [indicators_count](#indicators_count )         | No      | integer         | No         | -          | Total number of supply-chain indicators found.                                                                                                                                               |
| + [indicators](#indicators )                     | No      | array of object | No         | -          | List of specific supply-chain evidence found (e.g., OCI labels, signatures).                                                                                                                 |
| - [source](#source )                             | No      | object          | No         | -          | -                                                                                                                                                                                            |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Provenance analyzer.

Specific value: `"provenance"`

## <a name="repository"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The image repository that was analyzed.

## <a name="tag"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `tag`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The image tag that was analyzed.

## <a name="has_provenance"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `has_provenance`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if SLSA provenance or build attestations were found.

## <a name="has_cosign_signature"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `has_cosign_signature`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if at least one cosign signature (legacy tag or Sigstore bundle referrer) was discovered on the digest the reference resolves to. Discovery alone, not proof: see `verified_signers`.

## <a name="signatures"></a>6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `signatures`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Signatures discovered on the subject digest.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be       | Description |
| ------------------------------------- | ----------- |
| [signatures items](#signatures_items) | -           |

### <a name="signatures_items"></a>6.1. signatures items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                  | Pattern | Type             | Deprecated | Definition | Title/Description                                                                |
| ----------------------------------------- | ------- | ---------------- | ---------- | ---------- | -------------------------------------------------------------------------------- |
| + [format](#signatures_items_format )     | No      | enum (of string) | No         | -          | cosign v2 \`.sig\` tag layer, or cosign v3 Sigstore bundle referrer.             |
| + [location](#signatures_items_location ) | No      | string           | No         | -          | The \`sha256-<hex>.sig\` tag, or the referrer manifest digest.                   |
| + [verified](#signatures_items_verified ) | No      | boolean          | No         | -          | True when cosign confirmed this signature for the signer its certificate claims. |
| - [identity](#signatures_items_identity ) | No      | string           | No         | -          | Certificate identity (SAN). Present only when verified.                          |
| - [issuer](#signatures_items_issuer )     | No      | string           | No         | -          | OIDC issuer of the certificate. Present only when verified.                      |

#### <a name="signatures_items_format"></a>6.1.1. Property `format`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** cosign v2 `.sig` tag layer, or cosign v3 Sigstore bundle referrer.

Must be one of:
* "legacy-tag"
* "sigstore-bundle"

#### <a name="signatures_items_location"></a>6.1.2. Property `location`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The `sha256-<hex>.sig` tag, or the referrer manifest digest.

#### <a name="signatures_items_verified"></a>6.1.3. Property `verified`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True when cosign confirmed this signature for the signer its certificate claims.

#### <a name="signatures_items_identity"></a>6.1.4. Property `identity`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Certificate identity (SAN). Present only when verified.

#### <a name="signatures_items_issuer"></a>6.1.5. Property `issuer`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** OIDC issuer of the certificate. Present only when verified.

## <a name="verified_signers"></a>7. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `verified_signers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Distinct signers of verified signatures, matched by the `signed-by` criterion.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                   | Description |
| ------------------------------------------------- | ----------- |
| [verified_signers items](#verified_signers_items) | -           |

### <a name="verified_signers_items"></a>7.1. verified_signers items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                        | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| + [identity](#verified_signers_items_identity ) | No      | string | No         | -          | -                 |
| + [issuer](#verified_signers_items_issuer )     | No      | string | No         | -          | -                 |

#### <a name="verified_signers_items_identity"></a>7.1.1. Property `identity`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="verified_signers_items_issuer"></a>7.1.2. Property `issuer`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="signatures_complete"></a>8. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `signatures_complete`

|          |                   |
| -------- | ----------------- |
| **Type** | `boolean or null` |

**Description:** True when every lookup and verification ran; null when one could not (see `signature_gaps`).

## <a name="signature_gaps"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `signature_gaps`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Lookups or verifications that could not run (registry error, cosign missing, trust root unreachable).

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be               | Description |
| --------------------------------------------- | ----------- |
| [signature_gaps items](#signature_gaps_items) | -           |

### <a name="signature_gaps_items"></a>9.1. signature_gaps items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="source_tracked"></a>10. ![Required](https://img.shields.io/badge/Required-blue) Property `source_tracked`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if the source repository URL is tracked in metadata.

## <a name="indicators_count"></a>11. ![Required](https://img.shields.io/badge/Required-blue) Property `indicators_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of supply-chain indicators found.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="indicators"></a>12. ![Required](https://img.shields.io/badge/Required-blue) Property `indicators`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of specific supply-chain evidence found (e.g., OCI labels, signatures).

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be       | Description |
| ------------------------------------- | ----------- |
| [indicators items](#indicators_items) | -           |

### <a name="indicators_items"></a>12.1. indicators items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                            | Pattern | Type   | Deprecated | Definition | Title/Description                                  |
| ----------------------------------- | ------- | ------ | ---------- | ---------- | -------------------------------------------------- |
| + [type](#indicators_items_type )   | No      | string | No         | -          | Type of indicator (label, signature, attestation). |
| + [key](#indicators_items_key )     | No      | string | No         | -          | The specific metadata key or ID.                   |
| + [value](#indicators_items_value ) | No      | string | No         | -          | The value of the indicator.                        |

#### <a name="indicators_items_type"></a>12.1.1. Property `type`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Type of indicator (label, signature, attestation).

#### <a name="indicators_items_key"></a>12.1.2. Property `key`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The specific metadata key or ID.

#### <a name="indicators_items_value"></a>12.1.3. Property `value`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The value of the indicator.

## <a name="source"></a>13. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `source`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                            | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [fetched_at](#source_fetched_at ) | No      | string | No         | -          | -                 |
| - [built_at](#source_built_at )     | No      | string | No         | -          | -                 |
| - [version](#source_version )       | No      | string | No         | -          | -                 |
| - [checksum](#source_checksum )     | No      | string | No         | -          | -                 |

### <a name="source_fetched_at"></a>13.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `fetched_at`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

### <a name="source_built_at"></a>13.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `built_at`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

### <a name="source_version"></a>13.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="source_checksum"></a>13.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checksum`

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans)
