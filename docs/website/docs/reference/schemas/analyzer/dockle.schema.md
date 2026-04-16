# dockle.output

**Title:** dockle.output

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                               | Pattern | Type            | Deprecated | Definition | Title/Description                              |
| -------------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------------------- |
| + [analyzer](#analyzer )               | No      | const           | No         | -          | Unique identifier for the Dockle analyzer.     |
| + [repository](#repository )           | No      | string          | No         | -          | The image repository that was analyzed.        |
| + [tag](#tag )                         | No      | string          | No         | -          | The image tag that was analyzed.               |
| - [error](#error )                     | No      | string          | No         | -          | Any error encountered during execution.        |
| + [passed](#passed )                   | No      | boolean         | No         | -          | True if no issues were found, False otherwise. |
| + [issues_count](#issues_count )       | No      | integer         | No         | -          | Total number of issues found.                  |
| + [issues_by_level](#issues_by_level ) | No      | object          | No         | -          | Count of issues grouped by severity level.     |
| + [issues](#issues )                   | No      | array of object | No         | -          | List of issues found by Dockle.                |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Dockle analyzer.

Specific value: `"dockle"`

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

## <a name="error"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `error`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Any error encountered during execution.

## <a name="passed"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if no issues were found, False otherwise.

## <a name="issues_count"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `issues_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of issues found.

## <a name="issues_by_level"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `issues_by_level`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Count of issues grouped by severity level.

| Property                           | Pattern | Type    | Deprecated | Definition | Title/Description |
| ---------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| - [FATAL](#issues_by_level_FATAL ) | No      | integer | No         | -          | -                 |
| - [WARN](#issues_by_level_WARN )   | No      | integer | No         | -          | -                 |
| - [INFO](#issues_by_level_INFO )   | No      | integer | No         | -          | -                 |
| - [SKIP](#issues_by_level_SKIP )   | No      | integer | No         | -          | -                 |
| - [PASS](#issues_by_level_PASS )   | No      | integer | No         | -          | -                 |

### <a name="issues_by_level_FATAL"></a>7.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `FATAL`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_WARN"></a>7.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `WARN`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_INFO"></a>7.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `INFO`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_SKIP"></a>7.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `SKIP`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_PASS"></a>7.5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `PASS`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

## <a name="issues"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `issues`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of issues found by Dockle.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [issues items](#issues_items)   | -           |

### <a name="issues_items"></a>8.1. issues items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                          | Pattern | Type             | Deprecated | Definition | Title/Description                               |
| --------------------------------- | ------- | ---------------- | ---------- | ---------- | ----------------------------------------------- |
| + [code](#issues_items_code )     | No      | string           | No         | -          | Dockle rule code (e.g., CIS-DI-0001).           |
| + [title](#issues_items_title )   | No      | string           | No         | -          | Short description of the rule.                  |
| + [level](#issues_items_level )   | No      | enum (of string) | No         | -          | Severity level of the issue.                    |
| + [alerts](#issues_items_alerts ) | No      | array of string  | No         | -          | Specific details or files related to the issue. |

#### <a name="issues_items_code"></a>8.1.1. Property `code`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Dockle rule code (e.g., CIS-DI-0001).

#### <a name="issues_items_title"></a>8.1.2. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Short description of the rule.

#### <a name="issues_items_level"></a>8.1.3. Property `level`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Severity level of the issue.

Must be one of:
* "FATAL"
* "WARN"
* "INFO"
* "SKIP"
* "PASS"

#### <a name="issues_items_alerts"></a>8.1.4. Property `alerts`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Specific details or files related to the issue.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be            | Description |
| ------------------------------------------ | ----------- |
| [alerts items](#issues_items_alerts_items) | -           |

##### <a name="issues_items_alerts_items"></a>8.1.4.1. alerts items

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-16 at 10:22:31 +0000
