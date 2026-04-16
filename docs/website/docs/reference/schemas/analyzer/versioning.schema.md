# versioning.output

**Title:** versioning.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Report analyzing tag naming conventions and semver adoption.

| Property                                                       | Pattern | Type             | Deprecated | Definition | Title/Description                                                                 |
| -------------------------------------------------------------- | ------- | ---------------- | ---------- | ---------- | --------------------------------------------------------------------------------- |
| + [analyzer](#analyzer )                                       | No      | const            | No         | -          | Unique identifier for the Versioning analyzer.                                    |
| + [repository](#repository )                                   | No      | string           | No         | -          | The image repository that was analyzed.                                           |
| + [total_tags](#total_tags )                                   | No      | integer          | No         | -          | Total number of tags found in the remote repository.                              |
| + [dominant_pattern](#dominant_pattern )                       | No      | enum (of string) | No         | -          | The most frequently occurring tag naming pattern.                                 |
| + [aliases](#aliases )                                         | No      | array of string  | No         | -          | Other tags in the repository that resolve to the same digest as the analyzed tag. |
| - [release_lines](#release_lines )                             | No      | array of string  | No         | -          | Major/Minor versions identified as active release lines.                          |
| + [semver_compliant_percentage](#semver_compliant_percentage ) | No      | number           | No         | -          | Percentage of tags that follow strict Semantic Versioning.                        |
| + [patterns](#patterns )                                       | No      | array of object  | No         | -          | Frequency breakdown of tag naming patterns.                                       |
| + [variants](#variants )                                       | No      | array of object  | No         | -          | Frequency breakdown of tag variants (e.g., -alpine, -slim).                       |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Versioning analyzer.

Specific value: `"versioning"`

## <a name="repository"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The image repository that was analyzed.

## <a name="total_tags"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `total_tags`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of tags found in the remote repository.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="dominant_pattern"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `dominant_pattern`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** The most frequently occurring tag naming pattern.

Must be one of:
* "semver"
* "semver-prerelease"
* "semver-variant"
* "calver"
* "numeric"
* "numeric-variant"
* "hash"
* "named"
* "unknown"

## <a name="aliases"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `aliases`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Other tags in the repository that resolve to the same digest as the analyzed tag.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [aliases items](#aliases_items) | -           |

### <a name="aliases_items"></a>5.1. aliases items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="release_lines"></a>6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `release_lines`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Major/Minor versions identified as active release lines.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be             | Description |
| ------------------------------------------- | ----------- |
| [release_lines items](#release_lines_items) | -           |

### <a name="release_lines_items"></a>6.1. release_lines items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="semver_compliant_percentage"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `semver_compliant_percentage`

|          |          |
| -------- | -------- |
| **Type** | `number` |

**Description:** Percentage of tags that follow strict Semantic Versioning.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

## <a name="patterns"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `patterns`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Frequency breakdown of tag naming patterns.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be   | Description |
| --------------------------------- | ----------- |
| [patterns items](#patterns_items) | -           |

### <a name="patterns_items"></a>8.1. patterns items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                    | Pattern | Type             | Deprecated | Definition | Title/Description                               |
| ------------------------------------------- | ------- | ---------------- | ---------- | ---------- | ----------------------------------------------- |
| + [pattern](#patterns_items_pattern )       | No      | enum (of string) | No         | -          | Pattern identifier.                             |
| + [count](#patterns_items_count )           | No      | integer          | No         | -          | Number of tags matching this pattern.           |
| + [percentage](#patterns_items_percentage ) | No      | number           | No         | -          | Percentage of total tags matching this pattern. |
| + [examples](#patterns_items_examples )     | No      | array of string  | No         | -          | Sample tags matching this pattern.              |

#### <a name="patterns_items_pattern"></a>8.1.1. Property `pattern`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Pattern identifier.

Must be one of:
* "semver"
* "semver-prerelease"
* "semver-variant"
* "calver"
* "numeric"
* "numeric-variant"
* "hash"
* "named"

#### <a name="patterns_items_count"></a>8.1.2. Property `count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Number of tags matching this pattern.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="patterns_items_percentage"></a>8.1.3. Property `percentage`

|          |          |
| -------- | -------- |
| **Type** | `number` |

**Description:** Percentage of total tags matching this pattern.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

#### <a name="patterns_items_examples"></a>8.1.4. Property `examples`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Sample tags matching this pattern.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | 10                 |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                  | Description |
| ------------------------------------------------ | ----------- |
| [examples items](#patterns_items_examples_items) | -           |

##### <a name="patterns_items_examples_items"></a>8.1.4.1. examples items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="variants"></a>9. ![Required](https://img.shields.io/badge/Required-blue) Property `variants`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Frequency breakdown of tag variants (e.g., -alpine, -slim).

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be   | Description |
| --------------------------------- | ----------- |
| [variants items](#variants_items) | -           |

### <a name="variants_items"></a>9.1. variants items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                    | Pattern | Type            | Deprecated | Definition | Title/Description                                      |
| ------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------------ |
| + [name](#variants_items_name )             | No      | string          | No         | -          | Variant name or suffix.                                |
| + [count](#variants_items_count )           | No      | integer         | No         | -          | Number of tags identified with this variant.           |
| + [percentage](#variants_items_percentage ) | No      | number          | No         | -          | Percentage of total tags identified with this variant. |
| + [examples](#variants_items_examples )     | No      | array of string | No         | -          | Sample tags matching this variant.                     |

#### <a name="variants_items_name"></a>9.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Variant name or suffix.

#### <a name="variants_items_count"></a>9.1.2. Property `count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Number of tags identified with this variant.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="variants_items_percentage"></a>9.1.3. Property `percentage`

|          |          |
| -------- | -------- |
| **Type** | `number` |

**Description:** Percentage of total tags identified with this variant.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

#### <a name="variants_items_examples"></a>9.1.4. Property `examples`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Sample tags matching this variant.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | 10                 |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                  | Description |
| ------------------------------------------------ | ----------- |
| [examples items](#variants_items_examples_items) | -           |

##### <a name="variants_items_examples_items"></a>9.1.4.1. examples items

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-16 at 13:57:20 +0000
