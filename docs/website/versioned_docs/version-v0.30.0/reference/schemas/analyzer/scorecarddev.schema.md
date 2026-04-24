# scorecarddev.output

**Title:** scorecarddev.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Report containing OpenSSF Scorecard security assessment for the image source repository.

| Property                                       | Pattern | Type            | Deprecated | Definition | Title/Description                                          |
| ---------------------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------------------------------- |
| + [analyzer](#analyzer )                       | No      | const           | No         | -          | Unique identifier for the Scorecard analyzer.              |
| + [repository](#repository )                   | No      | string          | No         | -          | Docker image repository path.                              |
| + [source_repo](#source_repo )                 | No      | string or null  | No         | -          | Resolved source code repository URL, or null if not found. |
| + [scorecard_available](#scorecard_available ) | No      | boolean         | No         | -          | Whether OpenSSF Scorecard data was successfully retrieved. |
| + [score](#score )                             | No      | number or null  | No         | -          | Overall Scorecard score (0-10), or null if unavailable.    |
| + [checks](#checks )                           | No      | array of object | No         | -          | Individual Scorecard check results.                        |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Scorecard analyzer.

Specific value: `"scorecarddev"`

## <a name="repository"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Docker image repository path.

## <a name="source_repo"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `source_repo`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Resolved source code repository URL, or null if not found.

## <a name="scorecard_available"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `scorecard_available`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether OpenSSF Scorecard data was successfully retrieved.

## <a name="score"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `score`

|          |                  |
| -------- | ---------------- |
| **Type** | `number or null` |

**Description:** Overall Scorecard score (0-10), or null if unavailable.

## <a name="checks"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `checks`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Individual Scorecard check results.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [checks items](#checks_items)   | -           |

### <a name="checks_items"></a>6.1. checks items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                          | Pattern | Type    | Deprecated | Definition | Title/Description                                           |
| --------------------------------- | ------- | ------- | ---------- | ---------- | ----------------------------------------------------------- |
| + [name](#checks_items_name )     | No      | string  | No         | -          | Check name (e.g. Maintained, Code-Review, Vulnerabilities). |
| + [score](#checks_items_score )   | No      | integer | No         | -          | Check score (-1 to 10). -1 means not applicable.            |
| + [reason](#checks_items_reason ) | No      | string  | No         | -          | Human-readable explanation of the score.                    |

#### <a name="checks_items_name"></a>6.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Check name (e.g. Maintained, Code-Review, Vulnerabilities).

#### <a name="checks_items_score"></a>6.1.2. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Check score (-1 to 10). -1 means not applicable.

#### <a name="checks_items_reason"></a>6.1.3. Property `reason`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable explanation of the score.

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-22 at 20:05:38 +0000
