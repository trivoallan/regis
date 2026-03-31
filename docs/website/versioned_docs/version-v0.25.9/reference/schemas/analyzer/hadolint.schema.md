# hadolint.output

**Title:** hadolint.output

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                              | Pattern | Type            | Deprecated | Definition | Title/Description                              |
| ------------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------------------- |
| + [analyzer](#analyzer)               | No      | const           | No         | -          | Unique identifier for the Hadolint analyzer.   |
| + [repository](#repository)           | No      | string          | No         | -          | The image repository that was analyzed.        |
| + [tag](#tag)                         | No      | string          | No         | -          | The image tag that was analyzed.               |
| - [error](#error)                     | No      | string          | No         | -          | Any error encountered during execution.        |
| + [passed](#passed)                   | No      | boolean         | No         | -          | True if no issues were found, False otherwise. |
| + [issues_count](#issues_count)       | No      | integer         | No         | -          | Total number of issues found.                  |
| + [issues_by_level](#issues_by_level) | No      | object          | No         | -          | Count of issues grouped by severity level.     |
| + [issues](#issues)                   | No      | array of object | No         | -          | List of issues found by Hadolint.              |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Hadolint analyzer.

Specific value: `"hadolint"`

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

| Property                              | Pattern | Type    | Deprecated | Definition | Title/Description |
| ------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| - [error](#issues_by_level_error)     | No      | integer | No         | -          | -                 |
| - [warning](#issues_by_level_warning) | No      | integer | No         | -          | -                 |
| - [info](#issues_by_level_info)       | No      | integer | No         | -          | -                 |
| - [style](#issues_by_level_style)     | No      | integer | No         | -          | -                 |

### <a name="issues_by_level_error"></a>7.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `error`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_warning"></a>7.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `warning`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_info"></a>7.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `info`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

### <a name="issues_by_level_style"></a>7.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `style`

|             |           |
| ----------- | --------- |
| **Type**    | `integer` |
| **Default** | `0`       |

## <a name="issues"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `issues`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of issues found by Hadolint.

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

| Property                           | Pattern | Type             | Deprecated | Definition | Title/Description                     |
| ---------------------------------- | ------- | ---------------- | ---------- | ---------- | ------------------------------------- |
| + [code](#issues_items_code)       | No      | string           | No         | -          | Hadolint rule code (e.g., DL3008).    |
| + [level](#issues_items_level)     | No      | enum (of string) | No         | -          | Severity level of the issue.          |
| + [message](#issues_items_message) | No      | string           | No         | -          | Description of the issue.             |
| - [line](#issues_items_line)       | No      | integer or null  | No         | -          | Line number in the pseudo-Dockerfile. |

#### <a name="issues_items_code"></a>8.1.1. Property `code`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Hadolint rule code (e.g., DL3008).

#### <a name="issues_items_level"></a>8.1.2. Property `level`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Severity level of the issue.

Must be one of:

- "error"
- "warning"
- "info"
- "style"

#### <a name="issues_items_message"></a>8.1.3. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Description of the issue.

#### <a name="issues_items_line"></a>8.1.4. Property `line`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Line number in the pseudo-Dockerfile.

---

Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-03-31 at 07:55:14 +0000
