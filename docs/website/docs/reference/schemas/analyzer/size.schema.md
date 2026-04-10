# size.output

**Title:** size.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Image size breakdown.

| Property                                             | Pattern | Type                    | Deprecated | Definition | Title/Description                                                 |
| ---------------------------------------------------- | ------- | ----------------------- | ---------- | ---------- | ----------------------------------------------------------------- |
| + [analyzer](#analyzer )                             | No      | const                   | No         | -          | Unique identifier for the Size analyzer.                          |
| + [repository](#repository )                         | No      | string                  | No         | -          | The image repository that was analyzed.                           |
| + [tag](#tag )                                       | No      | string                  | No         | -          | The image tag that was analyzed.                                  |
| + [multi_arch](#multi_arch )                         | No      | boolean                 | No         | -          | True if the image is a multi-architecture manifest list.          |
| + [total_compressed_bytes](#total_compressed_bytes ) | No      | integer                 | No         | -          | Total compressed size of the image in bytes.                      |
| + [total_compressed_human](#total_compressed_human ) | No      | string                  | No         | -          | Human-readable total compressed size (e.g., '10.5 MB').           |
| + [layer_count](#layer_count )                       | No      | integer                 | No         | -          | Total number of layers in the image.                              |
| + [config_size_bytes](#config_size_bytes )           | No      | integer                 | No         | -          | Size of the image configuration JSON in bytes.                    |
| + [layers](#layers )                                 | No      | array of object         | No         | -          | Detailed breakdown of each layer in the image.                    |
| + [platforms](#platforms )                           | No      | array of object or null | No         | -          | Size information for each platform variant in a multi-arch image. |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Size analyzer.

Specific value: `"size"`

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

## <a name="multi_arch"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `multi_arch`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if the image is a multi-architecture manifest list.

## <a name="total_compressed_bytes"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `total_compressed_bytes`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total compressed size of the image in bytes.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="total_compressed_human"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `total_compressed_human`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable total compressed size (e.g., '10.5 MB').

## <a name="layer_count"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `layer_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of layers in the image.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="config_size_bytes"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `config_size_bytes`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Size of the image configuration JSON in bytes.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="layers"></a>9. ![Required](https://img.shields.io/badge/Required-blue) Property `layers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Detailed breakdown of each layer in the image.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [layers items](#layers_items)   | -           |

### <a name="layers_items"></a>9.1. layers items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                  | Pattern | Type    | Deprecated | Definition | Title/Description                       |
| ----------------------------------------- | ------- | ------- | ---------- | ---------- | --------------------------------------- |
| + [index](#layers_items_index )           | No      | integer | No         | -          | Zero-indexed position of the layer.     |
| + [digest](#layers_items_digest )         | No      | string  | No         | -          | Content digest (SHA256) of the layer.   |
| + [size_bytes](#layers_items_size_bytes ) | No      | integer | No         | -          | Compressed size of this layer in bytes. |
| + [size_human](#layers_items_size_human ) | No      | string  | No         | -          | Human-readable size of this layer.      |

#### <a name="layers_items_index"></a>9.1.1. Property `index`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Zero-indexed position of the layer.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="layers_items_digest"></a>9.1.2. Property `digest`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Content digest (SHA256) of the layer.

#### <a name="layers_items_size_bytes"></a>9.1.3. Property `size_bytes`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Compressed size of this layer in bytes.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="layers_items_size_human"></a>9.1.4. Property `size_human`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable size of this layer.

## <a name="platforms"></a>10. ![Required](https://img.shields.io/badge/Required-blue) Property `platforms`

|          |                           |
| -------- | ------------------------- |
| **Type** | `array of object or null` |

**Description:** Size information for each platform variant in a multi-arch image.

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

### <a name="platforms_items"></a>10.1. platforms items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                                 | Pattern | Type    | Deprecated | Definition | Title/Description                        |
| -------------------------------------------------------- | ------- | ------- | ---------- | ---------- | ---------------------------------------- |
| + [platform](#platforms_items_platform )                 | No      | string  | No         | -          | Platform string (e.g., 'linux/amd64').   |
| + [compressed_bytes](#platforms_items_compressed_bytes ) | No      | integer | No         | -          | Total compressed size for this platform. |
| + [compressed_human](#platforms_items_compressed_human ) | No      | string  | No         | -          | Human-readable size for this platform.   |
| + [layer_count](#platforms_items_layer_count )           | No      | integer | No         | -          | Number of layers for this platform.      |

#### <a name="platforms_items_platform"></a>10.1.1. Property `platform`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Platform string (e.g., 'linux/amd64').

#### <a name="platforms_items_compressed_bytes"></a>10.1.2. Property `compressed_bytes`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total compressed size for this platform.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="platforms_items_compressed_human"></a>10.1.3. Property `compressed_human`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable size for this platform.

#### <a name="platforms_items_layer_count"></a>10.1.4. Property `layer_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Number of layers for this platform.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-10 at 12:50:08 +0000
