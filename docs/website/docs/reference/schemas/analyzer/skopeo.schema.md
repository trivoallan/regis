# skopeo.output

**Title:** skopeo.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                     | Pattern | Type            | Deprecated | Definition | Title/Description                                 |
| ---------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------- |
| + [analyzer](#analyzer )     | No      | const           | No         | -          | Unique identifier for the Skopeo analyzer.        |
| + [repository](#repository ) | No      | string          | No         | -          | The image repository that was analyzed.           |
| + [tag](#tag )               | No      | string          | No         | -          | The image tag that was analyzed.                  |
| - [inspect](#inspect )       | No      | object          | No         | -          | Raw output from primary skopeo inspect            |
| + [platforms](#platforms )   | No      | array of object | No         | -          | List of platform variants available for this tag. |
| - [tags](#tags )             | No      | array of string | No         | -          | List of tags associated with the repository.      |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Skopeo analyzer.

Specific value: `"skopeo"`

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

## <a name="inspect"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `inspect`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Raw output from primary skopeo inspect

## <a name="platforms"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `platforms`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of platform variants available for this tag.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be     | Description |
| ----------------------------------- | ----------- |
| [platforms items](#platforms_items) | -           |

### <a name="platforms_items"></a>5.1. platforms items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                         | Pattern | Type           | Deprecated | Definition | Title/Description                          |
| ------------------------------------------------ | ------- | -------------- | ---------- | ---------- | ------------------------------------------ |
| + [architecture](#platforms_items_architecture ) | No      | string         | No         | -          | Processor architecture (e.g., 'amd64').    |
| + [os](#platforms_items_os )                     | No      | string         | No         | -          | Operating system (e.g., 'linux').          |
| - [variant](#platforms_items_variant )           | No      | string or null | No         | -          | Architecture variant (e.g., 'v7').         |
| - [digest](#platforms_items_digest )             | No      | string         | No         | -          | Manifest digest for this specific variant. |
| - [created](#platforms_items_created )           | No      | string or null | No         | -          | ISO timestamp of variant creation.         |
| - [labels](#platforms_items_labels )             | No      | object         | No         | -          | OCI labels associated with this variant.   |
| - [layers_count](#platforms_items_layers_count ) | No      | integer        | No         | -          | Number of layers in this variant.          |
| - [user](#platforms_items_user )                 | No      | string or null | No         | -          | Default user from image configuration.     |

#### <a name="platforms_items_architecture"></a>5.1.1. Property `architecture`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Processor architecture (e.g., 'amd64').

#### <a name="platforms_items_os"></a>5.1.2. Property `os`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Operating system (e.g., 'linux').

#### <a name="platforms_items_variant"></a>5.1.3. Property `variant`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Architecture variant (e.g., 'v7').

#### <a name="platforms_items_digest"></a>5.1.4. Property `digest`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Manifest digest for this specific variant.

#### <a name="platforms_items_created"></a>5.1.5. Property `created`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** ISO timestamp of variant creation.

#### <a name="platforms_items_labels"></a>5.1.6. Property `labels`

|                           |                                                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                            |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#platforms_items_labels_additionalProperties) |

**Description:** OCI labels associated with this variant.

| Property                                            | Pattern | Type   | Deprecated | Definition | Title/Description |
| --------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#platforms_items_labels_additionalProperties ) | No      | string | No         | -          | -                 |

##### <a name="platforms_items_labels_additionalProperties"></a>5.1.6.1. Property `additionalProperties`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="platforms_items_layers_count"></a>5.1.7. Property `layers_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Number of layers in this variant.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="platforms_items_user"></a>5.1.8. Property `user`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Default user from image configuration.

## <a name="tags"></a>6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of tags associated with the repository.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [tags items](#tags_items)       | -           |

### <a name="tags_items"></a>6.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-25 at 15:13:55 +0000
