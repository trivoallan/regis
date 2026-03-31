# report.definition

**Title:** report.definition

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Final report envelope produced by regis, containing request metadata and analyzer results.

| Property                          | Pattern | Type            | Deprecated | Definition                     | Title/Description                                                         |
| --------------------------------- | ------- | --------------- | ---------- | ------------------------------ | ------------------------------------------------------------------------- |
| + [version](#version)             | No      | string or null  | No         | -                              | Version of regis that generated this report.                              |
| - [tier](#tier)                   | No      | string or null  | No         | -                              | The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions. |
| - [badges](#badges)               | No      | array of object | No         | -                              | -                                                                         |
| - [metadata](#metadata)           | No      | object          | No         | -                              | Arbitrary user-provided metadata.                                         |
| - [links](#links)                 | No      | array of object | No         | -                              | Custom templated links.                                                   |
| + [request](#request)             | No      | object          | No         | -                              | Metadata describing the analysis request.                                 |
| + [results](#results)             | No      | object          | No         | -                              | Analyzer results keyed by analyzer name.                                  |
| - [playbooks](#playbooks)         | No      | array           | No         | -                              | List of evaluated playbook results.                                       |
| - [playbook](#playbook)           | No      | object          | No         | In playbook_result.schema.json | Primary playbook result (shorthand for playbooks[0]).                     |
| - [rules](#rules)                 | No      | array of object | No         | -                              | List of unified rule results (promoted from playbooks[0]).                |
| - [rules_summary](#rules_summary) | No      | object          | No         | -                              | Summary of rule evaluation results.                                       |

## <a name="version"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Version of regis that generated this report.

## <a name="tier"></a>2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `tier`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.

## <a name="badges"></a>3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [badges items](#badges_items)   | -           |

### <a name="badges_items"></a>3.1. badges items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                       | Pattern | Type             | Deprecated | Definition | Title/Description |
| ------------------------------ | ------- | ---------------- | ---------- | ---------- | ----------------- |
| - [slug](#badges_items_slug)   | No      | string           | No         | -          | -                 |
| + [scope](#badges_items_scope) | No      | string           | No         | -          | -                 |
| - [value](#badges_items_value) | No      | string or null   | No         | -          | -                 |
| + [class](#badges_items_class) | No      | enum (of string) | No         | -          | -                 |
| - [label](#badges_items_label) | No      | string           | No         | -          | -                 |

#### <a name="badges_items_slug"></a>3.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="badges_items_scope"></a>3.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="badges_items_value"></a>3.1.3. Property `value`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

#### <a name="badges_items_class"></a>3.1.4. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

Must be one of:

- "success"
- "warning"
- "error"
- "information"

#### <a name="badges_items_label"></a>3.1.5. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="metadata"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `metadata`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Arbitrary user-provided metadata.

| Property                             | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#metadata_additionalProperties) | No      | object | No         | -          | -                 |

## <a name="links"></a>5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `links`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Custom templated links.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [links items](#links_items)     | -           |

### <a name="links_items"></a>5.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                      | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| + [label](#links_items_label) | No      | string | No         | -          | -                 |
| + [url](#links_items_url)     | No      | string | No         | -          | -                 |

#### <a name="links_items_label"></a>5.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="links_items_url"></a>5.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="request"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `request`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Metadata describing the analysis request.

| Property                            | Pattern | Type            | Deprecated | Definition | Title/Description                                               |
| ----------------------------------- | ------- | --------------- | ---------- | ---------- | --------------------------------------------------------------- |
| + [url](#request_url)               | No      | string          | No         | -          | Original URL or image reference provided by the user.           |
| + [registry](#request_registry)     | No      | string          | No         | -          | Resolved registry hostname (e.g. registry-1.docker.io).         |
| + [repository](#request_repository) | No      | string          | No         | -          | Full repository path (e.g. library/nginx).                      |
| + [tag](#request_tag)               | No      | string          | No         | -          | Image tag that was analyzed.                                    |
| - [digest](#request_digest)         | No      | string          | No         | -          | Resolved image manifest digest (e.g. sha256-xxx), if available. |
| + [analyzers](#request_analyzers)   | No      | array of string | No         | -          | List of analyzer names that were executed.                      |
| + [timestamp](#request_timestamp)   | No      | string          | No         | -          | ISO 8601 UTC timestamp of the analysis.                         |
| - [metadata](#request_metadata)     | No      | object          | No         | -          | Arbitrary user-provided metadata.                               |

### <a name="request_url"></a>6.1. ![Required](https://img.shields.io/badge/Required-blue) Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Original URL or image reference provided by the user.

### <a name="request_registry"></a>6.2. ![Required](https://img.shields.io/badge/Required-blue) Property `registry`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Resolved registry hostname (e.g. registry-1.docker.io).

### <a name="request_repository"></a>6.3. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Full repository path (e.g. library/nginx).

### <a name="request_tag"></a>6.4. ![Required](https://img.shields.io/badge/Required-blue) Property `tag`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Image tag that was analyzed.

### <a name="request_digest"></a>6.5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `digest`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Resolved image manifest digest (e.g. sha256-xxx), if available.

### <a name="request_analyzers"></a>6.6. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of analyzer names that were executed.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be             | Description |
| ------------------------------------------- | ----------- |
| [analyzers items](#request_analyzers_items) | -           |

#### <a name="request_analyzers_items"></a>6.6.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="request_timestamp"></a>6.7. ![Required](https://img.shields.io/badge/Required-blue) Property `timestamp`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

**Description:** ISO 8601 UTC timestamp of the analysis.

### <a name="request_metadata"></a>6.8. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `metadata`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Arbitrary user-provided metadata.

| Property                                     | Pattern | Type   | Deprecated | Definition | Title/Description |
| -------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#request_metadata_additionalProperties) | No      | object | No         | -          | -                 |

## <a name="results"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `results`

|                           |                                                                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                             |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#results_additionalProperties) |

**Description:** Analyzer results keyed by analyzer name.

| Property                            | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#results_additionalProperties) | No      | object | No         | -          | -                 |

### <a name="results_additionalProperties"></a>7.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

## <a name="playbooks"></a>8. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `playbooks`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** List of evaluated playbook results.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                 | Description                                                                                                    |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [playbook_result.schema.json](#playbooks_items) | 😅 ERROR in schema generation, a referenced schema could not be loaded, no documentation here unfortunately 🏜️ |

### <a name="playbooks_items"></a>8.1. playbook_result.schema.json

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |
| **Defined in**            | playbook_result.schema.json                                                 |

**Description:** 😅 ERROR in schema generation, a referenced schema could not be loaded, no documentation here unfortunately 🏜️

## <a name="playbook"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `playbook`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |
| **Defined in**            | playbook_result.schema.json                                                 |

**Description:** Primary playbook result (shorthand for playbooks[0]).

## <a name="rules"></a>10. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of unified rule results (promoted from playbooks[0]).

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [rules items](#rules_items)     | -           |

### <a name="rules_items"></a>10.1. rules items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                              | Pattern | Type             | Deprecated | Definition | Title/Description |
| ------------------------------------- | ------- | ---------------- | ---------- | ---------- | ----------------- |
| + [slug](#rules_items_slug)           | No      | string           | No         | -          | -                 |
| + [title](#rules_items_title)         | No      | string           | No         | -          | -                 |
| - [level](#rules_items_level)         | No      | string           | No         | -          | -                 |
| - [tags](#rules_items_tags)           | No      | array of string  | No         | -          | -                 |
| + [passed](#rules_items_passed)       | No      | boolean          | No         | -          | -                 |
| + [status](#rules_items_status)       | No      | enum (of string) | No         | -          | -                 |
| + [message](#rules_items_message)     | No      | string           | No         | -          | -                 |
| - [analyzers](#rules_items_analyzers) | No      | array of string  | No         | -          | -                 |

#### <a name="rules_items_slug"></a>10.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_title"></a>10.1.2. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_level"></a>10.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_tags"></a>10.1.4. Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be       | Description |
| ------------------------------------- | ----------- |
| [tags items](#rules_items_tags_items) | -           |

##### <a name="rules_items_tags_items"></a>10.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_passed"></a>10.1.5. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

#### <a name="rules_items_status"></a>10.1.6. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

Must be one of:

- "passed"
- "failed"
- "incomplete"

#### <a name="rules_items_message"></a>10.1.7. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_analyzers"></a>10.1.8. Property `analyzers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                 | Description |
| ----------------------------------------------- | ----------- |
| [analyzers items](#rules_items_analyzers_items) | -           |

##### <a name="rules_items_analyzers_items"></a>10.1.8.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="rules_summary"></a>11. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules_summary`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Summary of rule evaluation results.

| Property                          | Pattern | Type            | Deprecated | Definition | Title/Description |
| --------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| - [score](#rules_summary_score)   | No      | integer         | No         | -          | -                 |
| - [total](#rules_summary_total)   | No      | array of string | No         | -          | -                 |
| - [passed](#rules_summary_passed) | No      | array of string | No         | -          | -                 |
| - [by_tag](#rules_summary_by_tag) | No      | object          | No         | -          | -                 |

### <a name="rules_summary_score"></a>11.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

### <a name="rules_summary_total"></a>11.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `total`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be           | Description |
| ----------------------------------------- | ----------- |
| [total items](#rules_summary_total_items) | -           |

#### <a name="rules_summary_total_items"></a>11.2.1. total items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="rules_summary_passed"></a>11.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `passed`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be             | Description |
| ------------------------------------------- | ----------- |
| [passed items](#rules_summary_passed_items) | -           |

#### <a name="rules_summary_passed_items"></a>11.3.1. passed items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="rules_summary_by_tag"></a>11.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `by_tag`

|                           |                                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                          |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#rules_summary_by_tag_additionalProperties) |

| Property                                         | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#rules_summary_by_tag_additionalProperties) | No      | object | No         | -          | -                 |

#### <a name="rules_summary_by_tag_additionalProperties"></a>11.4.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                  | Pattern | Type            | Deprecated | Definition | Title/Description |
| ------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| + [rules](#rules_summary_by_tag_additionalProperties_rules)               | No      | array of string | No         | -          | -                 |
| + [passed_rules](#rules_summary_by_tag_additionalProperties_passed_rules) | No      | array of string | No         | -          | -                 |
| + [score](#rules_summary_by_tag_additionalProperties_score)               | No      | integer         | No         | -          | -                 |

##### <a name="rules_summary_by_tag_additionalProperties_rules"></a>11.4.1.1. ![Required](https://img.shields.io/badge/Required-blue) Property `rules`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                       | Description |
| --------------------------------------------------------------------- | ----------- |
| [rules items](#rules_summary_by_tag_additionalProperties_rules_items) | -           |

###### <a name="rules_summary_by_tag_additionalProperties_rules_items"></a>11.4.1.1.1. rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_summary_by_tag_additionalProperties_passed_rules"></a>11.4.1.2. ![Required](https://img.shields.io/badge/Required-blue) Property `passed_rules`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                                     | Description |
| ----------------------------------------------------------------------------------- | ----------- |
| [passed_rules items](#rules_summary_by_tag_additionalProperties_passed_rules_items) | -           |

###### <a name="rules_summary_by_tag_additionalProperties_passed_rules_items"></a>11.4.1.2.1. passed_rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_summary_by_tag_additionalProperties_score"></a>11.4.1.3. ![Required](https://img.shields.io/badge/Required-blue) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

---

Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-03-31 at 08:29:45 +0000
