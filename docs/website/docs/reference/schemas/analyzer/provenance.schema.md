# provenance.output

**Title:** provenance.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Build provenance and supply-chain attestation information.

| Property                                         | Pattern | Type            | Deprecated | Definition | Title/Description                                                            |
| ------------------------------------------------ | ------- | --------------- | ---------- | ---------- | ---------------------------------------------------------------------------- |
| + [analyzer](#analyzer )                         | No      | const           | No         | -          | Unique identifier for the Provenance analyzer.                               |
| + [repository](#repository )                     | No      | string          | No         | -          | The image repository that was analyzed.                                      |
| + [tag](#tag )                                   | No      | string          | No         | -          | The image tag that was analyzed.                                             |
| + [has_provenance](#has_provenance )             | No      | boolean         | No         | -          | True if SLSA provenance or build attestations were found.                    |
| + [has_cosign_signature](#has_cosign_signature ) | No      | boolean         | No         | -          | True if a Cosign signature was found.                                        |
| + [source_tracked](#source_tracked )             | No      | boolean         | No         | -          | True if the source repository URL is tracked in metadata.                    |
| + [indicators_count](#indicators_count )         | No      | integer         | No         | -          | Total number of supply-chain indicators found.                               |
| + [indicators](#indicators )                     | No      | array of object | No         | -          | List of specific supply-chain evidence found (e.g., OCI labels, signatures). |

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

**Description:** True if a Cosign signature was found.

## <a name="source_tracked"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `source_tracked`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if the source repository URL is tracked in metadata.

## <a name="indicators_count"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `indicators_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of supply-chain indicators found.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="indicators"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `indicators`

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

### <a name="indicators_items"></a>8.1. indicators items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                            | Pattern | Type   | Deprecated | Definition | Title/Description                                  |
| ----------------------------------- | ------- | ------ | ---------- | ---------- | -------------------------------------------------- |
| + [type](#indicators_items_type )   | No      | string | No         | -          | Type of indicator (label, signature, attestation). |
| + [key](#indicators_items_key )     | No      | string | No         | -          | The specific metadata key or ID.                   |
| + [value](#indicators_items_value ) | No      | string | No         | -          | The value of the indicator.                        |

#### <a name="indicators_items_type"></a>8.1.1. Property `type`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Type of indicator (label, signature, attestation).

#### <a name="indicators_items_key"></a>8.1.2. Property `key`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The specific metadata key or ID.

#### <a name="indicators_items_value"></a>8.1.3. Property `value`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The value of the indicator.

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-10 at 07:32:03 +0000
