# popularity.output

**Title:** popularity.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Docker Hub popularity statistics.

| Property                               | Pattern | Type            | Deprecated | Definition | Title/Description                                    |
| -------------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------------------------- |
| + [analyzer](#analyzer )               | No      | const           | No         | -          | Unique identifier for the Popularity analyzer.       |
| + [repository](#repository )           | No      | string          | No         | -          | The image repository that was analyzed.              |
| + [available](#available )             | No      | boolean         | No         | -          | True if the repository was found on Docker Hub.      |
| + [pull_count](#pull_count )           | No      | integer or null | No         | -          | Total number of pulls for this repository.           |
| + [star_count](#star_count )           | No      | integer or null | No         | -          | Number of stars for this repository on Docker Hub.   |
| + [description](#description )         | No      | string or null  | No         | -          | Short description of the repository from Docker Hub. |
| + [date_registered](#date_registered ) | No      | string or null  | No         | -          | ISO timestamp of when the repository was created.    |
| + [is_official](#is_official )         | No      | boolean         | No         | -          | True if this is an official Docker Hub repository.   |
| - [source](#source )                   | No      | object          | No         | -          | -                                                    |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Popularity analyzer.

Specific value: `"popularity"`

## <a name="repository"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The image repository that was analyzed.

## <a name="available"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `available`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if the repository was found on Docker Hub.

## <a name="pull_count"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `pull_count`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Total number of pulls for this repository.

## <a name="star_count"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `star_count`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Number of stars for this repository on Docker Hub.

## <a name="description"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `description`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Short description of the repository from Docker Hub.

## <a name="date_registered"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `date_registered`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** ISO timestamp of when the repository was created.

## <a name="is_official"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `is_official`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if this is an official Docker Hub repository.

## <a name="source"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `source`

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

### <a name="source_fetched_at"></a>9.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `fetched_at`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

### <a name="source_built_at"></a>9.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `built_at`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

### <a name="source_version"></a>9.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="source_checksum"></a>9.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checksum`

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-07-06 at 00:31:07 +0000
