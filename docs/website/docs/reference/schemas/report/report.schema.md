# report

**Title:** report

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Final report envelope produced by regis, containing request metadata and analyzer results.

| Property                           | Pattern | Type            | Deprecated | Definition                                   | Title/Description                                                         |
| ---------------------------------- | ------- | --------------- | ---------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| + [version](#version )             | No      | string or null  | No         | -                                            | Version of regis that generated this report.                              |
| - [tier](#tier )                   | No      | string or null  | No         | -                                            | The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions. |
| - [badges](#badges )               | No      | array of object | No         | -                                            | -                                                                         |
| - [metadata](#metadata )           | No      | object          | No         | -                                            | Arbitrary user-provided metadata.                                         |
| - [links](#links )                 | No      | array of object | No         | -                                            | Custom templated links.                                                   |
| + [request](#request )             | No      | object          | No         | -                                            | Metadata describing the analysis request.                                 |
| + [results](#results )             | No      | object          | No         | -                                            | Analyzer results keyed by analyzer name.                                  |
| - [playbooks](#playbooks )         | No      | array           | No         | -                                            | List of evaluated playbook results.                                       |
| - [playbook](#playbook )           | No      | object          | No         | Same as [playbook.result](#playbooks_items ) | playbook.result                                                           |
| - [rules](#rules )                 | No      | array of object | No         | -                                            | List of unified rule results (promoted from playbooks[0]).                |
| - [rules_summary](#rules_summary ) | No      | object          | No         | -                                            | Summary of rule evaluation results.                                       |

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

| Property                        | Pattern | Type             | Deprecated | Definition | Title/Description                                  |
| ------------------------------- | ------- | ---------------- | ---------- | ---------- | -------------------------------------------------- |
| - [slug](#badges_items_slug )   | No      | string           | No         | -          | Unique identifier for the badge.                   |
| + [scope](#badges_items_scope ) | No      | string           | No         | -          | Domain of the badge (e.g., 'security', 'hygiene'). |
| - [value](#badges_items_value ) | No      | string or null   | No         | -          | Display value or grade (e.g., 'A', '95%').         |
| + [class](#badges_items_class ) | No      | enum (of string) | No         | -          | Visual style indicator.                            |
| - [label](#badges_items_label ) | No      | string           | No         | -          | The full label string (scope or scope: value).     |

#### <a name="badges_items_slug"></a>3.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

#### <a name="badges_items_scope"></a>3.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Domain of the badge (e.g., 'security', 'hygiene').

#### <a name="badges_items_value"></a>3.1.3. Property `value`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Display value or grade (e.g., 'A', '95%').

#### <a name="badges_items_class"></a>3.1.4. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Visual style indicator.

Must be one of:
* "success"
* "warning"
* "error"
* "information"

#### <a name="badges_items_label"></a>3.1.5. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The full label string (scope or scope: value).

## <a name="metadata"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `metadata`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Arbitrary user-provided metadata.

| Property                              | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#metadata_additionalProperties ) | No      | object | No         | -          | -                 |

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

| Property                       | Pattern | Type   | Deprecated | Definition | Title/Description           |
| ------------------------------ | ------- | ------ | ---------- | ---------- | --------------------------- |
| + [label](#links_items_label ) | No      | string | No         | -          | Display label for the link. |
| + [url](#links_items_url )     | No      | string | No         | -          | Target URL.                 |

#### <a name="links_items_label"></a>5.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

#### <a name="links_items_url"></a>5.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

## <a name="request"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `request`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Metadata describing the analysis request.

| Property                             | Pattern | Type            | Deprecated | Definition | Title/Description                                               |
| ------------------------------------ | ------- | --------------- | ---------- | ---------- | --------------------------------------------------------------- |
| + [url](#request_url )               | No      | string          | No         | -          | Original URL or image reference provided by the user.           |
| + [registry](#request_registry )     | No      | string          | No         | -          | Resolved registry hostname (e.g. registry-1.docker.io).         |
| + [repository](#request_repository ) | No      | string          | No         | -          | Full repository path (e.g. library/nginx).                      |
| + [tag](#request_tag )               | No      | string          | No         | -          | Image tag that was analyzed.                                    |
| - [digest](#request_digest )         | No      | string or null  | No         | -          | Resolved image manifest digest (e.g. sha256-xxx), if available. |
| + [analyzers](#request_analyzers )   | No      | array of string | No         | -          | List of analyzer names that were executed.                      |
| + [timestamp](#request_timestamp )   | No      | string          | No         | -          | ISO 8601 UTC timestamp of the analysis.                         |
| - [metadata](#request_metadata )     | No      | object          | No         | -          | Arbitrary user-provided metadata.                               |

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

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

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

| Property                                      | Pattern | Type   | Deprecated | Definition | Title/Description |
| --------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#request_metadata_additionalProperties ) | No      | object | No         | -          | -                 |

## <a name="results"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `results`

|                           |                                                                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                             |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#results_additionalProperties) |

**Description:** Analyzer results keyed by analyzer name.

| Property                             | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#results_additionalProperties ) | No      | object | No         | -          | -                 |

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

| Each item of this array must be     | Description                                                                        |
| ----------------------------------- | ---------------------------------------------------------------------------------- |
| [playbook.result](#playbooks_items) | Final playbook result produced by regis, containing metadata and analyzer results. |

### <a name="playbooks_items"></a>8.1. playbook.result

**Title:** playbook.result

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |
| **Defined in**            | ../playbook/result.schema.json                                              |

**Description:** Final playbook result produced by regis, containing metadata and analyzer results.

| Property                                                   | Pattern | Type            | Deprecated | Definition | Title/Description                                                         |
| ---------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------------------------------- |
| + [playbook_name](#playbooks_items_playbook_name )         | No      | string          | No         | -          | Identifier of the playbook that was executed.                             |
| - [sidebar](#playbooks_items_sidebar )                     | No      | object          | No         | -          | Sidebar navigation metadata for the report UI.                            |
| - [version](#playbooks_items_version )                     | No      | string or null  | No         | -          | Version of regis that generated this report.                              |
| - [tier](#playbooks_items_tier )                           | No      | string or null  | No         | -          | The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions. |
| - [badges](#playbooks_items_badges )                       | No      | array of object | No         | -          | -                                                                         |
| - [rules](#playbooks_items_rules )                         | No      | array of object | No         | -          | -                                                                         |
| - [rules_summary](#playbooks_items_rules_summary )         | No      | object          | No         | -          | -                                                                         |
| + [score](#playbooks_items_score )                         | No      | integer         | No         | -          | Overall percentage score for the playbook.                                |
| + [total_scorecards](#playbooks_items_total_scorecards )   | No      | integer         | No         | -          | Total number of scorecards evaluated.                                     |
| + [passed_scorecards](#playbooks_items_passed_scorecards ) | No      | integer         | No         | -          | Number of scorecards that passed.                                         |
| - [links](#playbooks_items_links )                         | No      | array of object | No         | -          | External links associated with this playbook result.                      |
| + [pages](#playbooks_items_pages )                         | No      | array of object | No         | -          | -                                                                         |
| - [mr_templates](#playbooks_items_mr_templates )           | No      | array of object | No         | -          | Cookiecutter templates to be run for MR descriptions.                     |

#### <a name="playbooks_items_playbook_name"></a>8.1.1. Property `playbook_name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Identifier of the playbook that was executed.

#### <a name="playbooks_items_sidebar"></a>8.1.2. Property `sidebar`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Sidebar navigation metadata for the report UI.

#### <a name="playbooks_items_version"></a>8.1.3. Property `version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Version of regis that generated this report.

#### <a name="playbooks_items_tier"></a>8.1.4. Property `tier`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.

#### <a name="playbooks_items_badges"></a>8.1.5. Property `badges`

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

| Each item of this array must be               | Description |
| --------------------------------------------- | ----------- |
| [badges items](#playbooks_items_badges_items) | -           |

##### <a name="playbooks_items_badges_items"></a>8.1.5.1. badges items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                        | Pattern | Type             | Deprecated | Definition | Title/Description                                  |
| ----------------------------------------------- | ------- | ---------------- | ---------- | ---------- | -------------------------------------------------- |
| - [slug](#playbooks_items_badges_items_slug )   | No      | string           | No         | -          | Unique identifier for the badge.                   |
| + [scope](#playbooks_items_badges_items_scope ) | No      | string           | No         | -          | Domain of the badge (e.g., 'security', 'hygiene'). |
| - [value](#playbooks_items_badges_items_value ) | No      | string or null   | No         | -          | Display value or grade (e.g., 'A', '95%').         |
| + [class](#playbooks_items_badges_items_class ) | No      | enum (of string) | No         | -          | Visual style indicator.                            |
| - [label](#playbooks_items_badges_items_label ) | No      | string           | No         | -          | The full label string (scope or scope: value).     |

###### <a name="playbooks_items_badges_items_slug"></a>8.1.5.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

###### <a name="playbooks_items_badges_items_scope"></a>8.1.5.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Domain of the badge (e.g., 'security', 'hygiene').

###### <a name="playbooks_items_badges_items_value"></a>8.1.5.1.3. Property `value`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Display value or grade (e.g., 'A', '95%').

###### <a name="playbooks_items_badges_items_class"></a>8.1.5.1.4. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Visual style indicator.

Must be one of:
* "success"
* "warning"
* "error"
* "information"

###### <a name="playbooks_items_badges_items_label"></a>8.1.5.1.5. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The full label string (scope or scope: value).

#### <a name="playbooks_items_rules"></a>8.1.6. Property `rules`

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

| Each item of this array must be             | Description |
| ------------------------------------------- | ----------- |
| [rules items](#playbooks_items_rules_items) | -           |

##### <a name="playbooks_items_rules_items"></a>8.1.6.1. rules items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                   | Pattern | Type             | Deprecated | Definition | Title/Description                                     |
| ---------------------------------------------------------- | ------- | ---------------- | ---------- | ---------- | ----------------------------------------------------- |
| + [slug](#playbooks_items_rules_items_slug )               | No      | string           | No         | -          | Unique identifier for the rule.                       |
| + [description](#playbooks_items_rules_items_description ) | No      | string           | No         | -          | Human-readable name of the rule.                      |
| - [level](#playbooks_items_rules_items_level )             | No      | string           | No         | -          | Priority level (Gold, Silver, Bronze).                |
| - [tags](#playbooks_items_rules_items_tags )               | No      | array of string  | No         | -          | Associated metadata tags.                             |
| + [passed](#playbooks_items_rules_items_passed )           | No      | boolean          | No         | -          | Whether the rule criteria were met.                   |
| + [status](#playbooks_items_rules_items_status )           | No      | enum (of string) | No         | -          | Detailed execution status.                            |
| + [message](#playbooks_items_rules_items_message )         | No      | string           | No         | -          | Reasoning or details for the rule result.             |
| - [analyzers](#playbooks_items_rules_items_analyzers )     | No      | array of string  | No         | -          | List of analyzers that contributed data to this rule. |

###### <a name="playbooks_items_rules_items_slug"></a>8.1.6.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule.

###### <a name="playbooks_items_rules_items_description"></a>8.1.6.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable name of the rule.

###### <a name="playbooks_items_rules_items_level"></a>8.1.6.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Priority level (Gold, Silver, Bronze).

###### <a name="playbooks_items_rules_items_tags"></a>8.1.6.1.4. Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Associated metadata tags.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                       | Description |
| ----------------------------------------------------- | ----------- |
| [tags items](#playbooks_items_rules_items_tags_items) | -           |

###### <a name="playbooks_items_rules_items_tags_items"></a>8.1.6.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_items_passed"></a>8.1.6.1.5. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether the rule criteria were met.

###### <a name="playbooks_items_rules_items_status"></a>8.1.6.1.6. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Detailed execution status.

Must be one of:
* "passed"
* "failed"
* "incomplete"

###### <a name="playbooks_items_rules_items_message"></a>8.1.6.1.7. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Reasoning or details for the rule result.

###### <a name="playbooks_items_rules_items_analyzers"></a>8.1.6.1.8. Property `analyzers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of analyzers that contributed data to this rule.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                 | Description |
| --------------------------------------------------------------- | ----------- |
| [analyzers items](#playbooks_items_rules_items_analyzers_items) | -           |

###### <a name="playbooks_items_rules_items_analyzers_items"></a>8.1.6.1.8.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="playbooks_items_rules_summary"></a>8.1.7. Property `rules_summary`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                           | Pattern | Type            | Deprecated | Definition | Title/Description |
| -------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| + [score](#playbooks_items_rules_summary_score )   | No      | integer         | No         | -          | -                 |
| + [total](#playbooks_items_rules_summary_total )   | No      | array of string | No         | -          | -                 |
| + [passed](#playbooks_items_rules_summary_passed ) | No      | array of string | No         | -          | -                 |
| - [by_tag](#playbooks_items_rules_summary_by_tag ) | No      | object          | No         | -          | -                 |

##### <a name="playbooks_items_rules_summary_score"></a>8.1.7.1. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

##### <a name="playbooks_items_rules_summary_total"></a>8.1.7.2. Property `total`

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

| Each item of this array must be                           | Description |
| --------------------------------------------------------- | ----------- |
| [total items](#playbooks_items_rules_summary_total_items) | -           |

###### <a name="playbooks_items_rules_summary_total_items"></a>8.1.7.2.1. total items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="playbooks_items_rules_summary_passed"></a>8.1.7.3. Property `passed`

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

| Each item of this array must be                             | Description |
| ----------------------------------------------------------- | ----------- |
| [passed items](#playbooks_items_rules_summary_passed_items) | -           |

###### <a name="playbooks_items_rules_summary_passed_items"></a>8.1.7.3.1. passed items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="playbooks_items_rules_summary_by_tag"></a>8.1.7.4. Property `by_tag`

|                           |                                                                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                                          |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#playbooks_items_rules_summary_by_tag_additionalProperties) |

| Property                                                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#playbooks_items_rules_summary_by_tag_additionalProperties ) | No      | object | No         | -          | -                 |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties"></a>8.1.7.4.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                                   | Pattern | Type            | Deprecated | Definition | Title/Description |
| ------------------------------------------------------------------------------------------ | ------- | --------------- | ---------- | ---------- | ----------------- |
| + [rules](#playbooks_items_rules_summary_by_tag_additionalProperties_rules )               | No      | array of string | No         | -          | -                 |
| + [passed_rules](#playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules ) | No      | array of string | No         | -          | -                 |
| + [score](#playbooks_items_rules_summary_by_tag_additionalProperties_score )               | No      | integer         | No         | -          | -                 |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_rules"></a>8.1.7.4.1.1. Property `rules`

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

| Each item of this array must be                                                       | Description |
| ------------------------------------------------------------------------------------- | ----------- |
| [rules items](#playbooks_items_rules_summary_by_tag_additionalProperties_rules_items) | -           |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_rules_items"></a>8.1.7.4.1.1.1. rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules"></a>8.1.7.4.1.2. Property `passed_rules`

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

| Each item of this array must be                                                                     | Description |
| --------------------------------------------------------------------------------------------------- | ----------- |
| [passed_rules items](#playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules_items) | -           |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules_items"></a>8.1.7.4.1.2.1. passed_rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_score"></a>8.1.7.4.1.3. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

#### <a name="playbooks_items_score"></a>8.1.8. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Overall percentage score for the playbook.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

#### <a name="playbooks_items_total_scorecards"></a>8.1.9. Property `total_scorecards`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of scorecards evaluated.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="playbooks_items_passed_scorecards"></a>8.1.10. Property `passed_scorecards`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Number of scorecards that passed.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

#### <a name="playbooks_items_links"></a>8.1.11. Property `links`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** External links associated with this playbook result.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be             | Description |
| ------------------------------------------- | ----------- |
| [links items](#playbooks_items_links_items) | -           |

##### <a name="playbooks_items_links_items"></a>8.1.11.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                       | Pattern | Type   | Deprecated | Definition | Title/Description           |
| ---------------------------------------------- | ------- | ------ | ---------- | ---------- | --------------------------- |
| + [label](#playbooks_items_links_items_label ) | No      | string | No         | -          | Display label for the link. |
| + [url](#playbooks_items_links_items_url )     | No      | string | No         | -          | Target URL.                 |

###### <a name="playbooks_items_links_items_label"></a>8.1.11.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

###### <a name="playbooks_items_links_items_url"></a>8.1.11.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

#### <a name="playbooks_items_pages"></a>8.1.12. Property `pages`

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

| Each item of this array must be             | Description |
| ------------------------------------------- | ----------- |
| [pages items](#playbooks_items_pages_items) | -           |

##### <a name="playbooks_items_pages_items"></a>8.1.12.1. pages items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                               | Pattern | Type            | Deprecated | Definition | Title/Description                     |
| ---------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------- |
| + [title](#playbooks_items_pages_items_title )                         | No      | string          | No         | -          | Page title.                           |
| - [slug](#playbooks_items_pages_items_slug )                           | No      | string or null  | No         | -          | URL-friendly identifier for the page. |
| + [score](#playbooks_items_pages_items_score )                         | No      | integer         | No         | -          | Percentage score for this page.       |
| + [total_scorecards](#playbooks_items_pages_items_total_scorecards )   | No      | integer         | No         | -          | Total scorecards on this page.        |
| + [passed_scorecards](#playbooks_items_pages_items_passed_scorecards ) | No      | integer         | No         | -          | Passed scorecards on this page.       |
| + [sections](#playbooks_items_pages_items_sections )                   | No      | array of object | No         | -          | -                                     |

###### <a name="playbooks_items_pages_items_title"></a>8.1.12.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Page title.

###### <a name="playbooks_items_pages_items_slug"></a>8.1.12.1.2. Property `slug`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** URL-friendly identifier for the page.

###### <a name="playbooks_items_pages_items_score"></a>8.1.12.1.3. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Percentage score for this page.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

###### <a name="playbooks_items_pages_items_total_scorecards"></a>8.1.12.1.4. Property `total_scorecards`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total scorecards on this page.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_passed_scorecards"></a>8.1.12.1.5. Property `passed_scorecards`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Passed scorecards on this page.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections"></a>8.1.12.1.6. Property `sections`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | 1                  |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                               | Description |
| ------------------------------------------------------------- | ----------- |
| [sections items](#playbooks_items_pages_items_sections_items) | -           |

###### <a name="playbooks_items_pages_items_sections_items"></a>8.1.12.1.6.1. sections items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                              | Pattern | Type            | Deprecated | Definition | Title/Description                  |
| ------------------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------- |
| + [name](#playbooks_items_pages_items_sections_items_name )                           | No      | string          | No         | -          | Section name.                      |
| - [hint](#playbooks_items_pages_items_sections_items_hint )                           | No      | string          | No         | -          | Informative text for the section.  |
| + [score](#playbooks_items_pages_items_sections_items_score )                         | No      | integer         | No         | -          | Percentage score for this section. |
| + [total_scorecards](#playbooks_items_pages_items_sections_items_total_scorecards )   | No      | integer         | No         | -          | Total scorecards in this section.  |
| + [passed_scorecards](#playbooks_items_pages_items_sections_items_passed_scorecards ) | No      | integer         | No         | -          | Passed scorecards in this section. |
| - [levels_summary](#playbooks_items_pages_items_sections_items_levels_summary )       | No      | object          | No         | -          | -                                  |
| - [tags_summary](#playbooks_items_pages_items_sections_items_tags_summary )           | No      | object          | No         | -          | -                                  |
| + [scorecards](#playbooks_items_pages_items_sections_items_scorecards )               | No      | array of object | No         | -          | -                                  |
| - [display](#playbooks_items_pages_items_sections_items_display )                     | No      | object          | No         | -          | -                                  |

###### <a name="playbooks_items_pages_items_sections_items_name"></a>8.1.12.1.6.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Section name.

###### <a name="playbooks_items_pages_items_sections_items_hint"></a>8.1.12.1.6.1.2. Property `hint`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Informative text for the section.

###### <a name="playbooks_items_pages_items_sections_items_score"></a>8.1.12.1.6.1.3. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Percentage score for this section.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

###### <a name="playbooks_items_pages_items_sections_items_total_scorecards"></a>8.1.12.1.6.1.4. Property `total_scorecards`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total scorecards in this section.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections_items_passed_scorecards"></a>8.1.12.1.6.1.5. Property `passed_scorecards`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Passed scorecards in this section.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections_items_levels_summary"></a>8.1.12.1.6.1.6. Property `levels_summary`

|                           |                                                                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Type**                  | `object`                                                                                                                                               |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#playbooks_items_pages_items_sections_items_levels_summary_additionalProperties) |

| Property                                                                               | Pattern | Type   | Deprecated | Definition | Title/Description |
| -------------------------------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#playbooks_items_pages_items_sections_items_levels_summary_additionalProperties ) | No      | object | No         | -          | -                 |

###### <a name="playbooks_items_pages_items_sections_items_levels_summary_additionalProperties"></a>8.1.12.1.6.1.6.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                                                    | Pattern | Type    | Deprecated | Definition | Title/Description |
| ----------------------------------------------------------------------------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| + [total](#playbooks_items_pages_items_sections_items_levels_summary_additionalProperties_total )           | No      | integer | No         | -          | -                 |
| + [passed](#playbooks_items_pages_items_sections_items_levels_summary_additionalProperties_passed )         | No      | integer | No         | -          | -                 |
| + [percentage](#playbooks_items_pages_items_sections_items_levels_summary_additionalProperties_percentage ) | No      | integer | No         | -          | -                 |

###### <a name="playbooks_items_pages_items_sections_items_levels_summary_additionalProperties_total"></a>8.1.12.1.6.1.6.1.1. Property `total`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections_items_levels_summary_additionalProperties_passed"></a>8.1.12.1.6.1.6.1.2. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections_items_levels_summary_additionalProperties_percentage"></a>8.1.12.1.6.1.6.1.3. Property `percentage`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

###### <a name="playbooks_items_pages_items_sections_items_tags_summary"></a>8.1.12.1.6.1.7. Property `tags_summary`

|                           |                                                                                                                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                                                             |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#playbooks_items_pages_items_sections_items_tags_summary_additionalProperties) |

| Property                                                                             | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#playbooks_items_pages_items_sections_items_tags_summary_additionalProperties ) | No      | object | No         | -          | -                 |

###### <a name="playbooks_items_pages_items_sections_items_tags_summary_additionalProperties"></a>8.1.12.1.6.1.7.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                                                  | Pattern | Type    | Deprecated | Definition | Title/Description |
| --------------------------------------------------------------------------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| + [total](#playbooks_items_pages_items_sections_items_tags_summary_additionalProperties_total )           | No      | integer | No         | -          | -                 |
| + [passed](#playbooks_items_pages_items_sections_items_tags_summary_additionalProperties_passed )         | No      | integer | No         | -          | -                 |
| + [percentage](#playbooks_items_pages_items_sections_items_tags_summary_additionalProperties_percentage ) | No      | integer | No         | -          | -                 |

###### <a name="playbooks_items_pages_items_sections_items_tags_summary_additionalProperties_total"></a>8.1.12.1.6.1.7.1.1. Property `total`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections_items_tags_summary_additionalProperties_passed"></a>8.1.12.1.6.1.7.1.2. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

###### <a name="playbooks_items_pages_items_sections_items_tags_summary_additionalProperties_percentage"></a>8.1.12.1.6.1.7.1.3. Property `percentage`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

###### <a name="playbooks_items_pages_items_sections_items_scorecards"></a>8.1.12.1.6.1.8. Property `scorecards`

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

| Each item of this array must be                                                  | Description |
| -------------------------------------------------------------------------------- | ----------- |
| [scorecards items](#playbooks_items_pages_items_sections_items_scorecards_items) | -           |

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items"></a>8.1.12.1.6.1.8.1. scorecards items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                                   | Pattern | Type             | Deprecated | Definition | Title/Description                          |
| ------------------------------------------------------------------------------------------ | ------- | ---------------- | ---------- | ---------- | ------------------------------------------ |
| + [name](#playbooks_items_pages_items_sections_items_scorecards_items_name )               | No      | string           | No         | -          | Unique scorecard identifier.               |
| + [description](#playbooks_items_pages_items_sections_items_scorecards_items_description ) | No      | string           | No         | -          | Display description.                       |
| - [level](#playbooks_items_pages_items_sections_items_scorecards_items_level )             | No      | string or null   | No         | -          | Assigned severity level name.              |
| - [tags](#playbooks_items_pages_items_sections_items_scorecards_items_tags )               | No      | array of string  | No         | -          | Associated search tags.                    |
| - [analyzers](#playbooks_items_pages_items_sections_items_scorecards_items_analyzers )     | No      | array of string  | No         | -          | Analyzers used for this scorecard.         |
| + [passed](#playbooks_items_pages_items_sections_items_scorecards_items_passed )           | No      | boolean          | No         | -          | True if condition was met.                 |
| - [status](#playbooks_items_pages_items_sections_items_scorecards_items_status )           | No      | enum (of string) | No         | -          | Execution status.                          |
| - [condition](#playbooks_items_pages_items_sections_items_scorecards_items_condition )     | No      | string           | No         | -          | The JsonLogic expression evaluated.        |
| - [details](#playbooks_items_pages_items_sections_items_scorecards_items_details )         | No      | string           | No         | -          | Detailed explanation of calculated result. |

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_name"></a>8.1.12.1.6.1.8.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique scorecard identifier.

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_description"></a>8.1.12.1.6.1.8.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display description.

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_level"></a>8.1.12.1.6.1.8.1.3. Property `level`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Assigned severity level name.

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_tags"></a>8.1.12.1.6.1.8.1.4. Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Associated search tags.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                                       | Description |
| ------------------------------------------------------------------------------------- | ----------- |
| [tags items](#playbooks_items_pages_items_sections_items_scorecards_items_tags_items) | -           |

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_tags_items"></a>8.1.12.1.6.1.8.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_analyzers"></a>8.1.12.1.6.1.8.1.5. Property `analyzers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Analyzers used for this scorecard.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                                                 | Description |
| ----------------------------------------------------------------------------------------------- | ----------- |
| [analyzers items](#playbooks_items_pages_items_sections_items_scorecards_items_analyzers_items) | -           |

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_analyzers_items"></a>8.1.12.1.6.1.8.1.5.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_passed"></a>8.1.12.1.6.1.8.1.6. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if condition was met.

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_status"></a>8.1.12.1.6.1.8.1.7. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Execution status.

Must be one of:
* "passed"
* "failed"
* "incomplete"

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_condition"></a>8.1.12.1.6.1.8.1.8. Property `condition`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The JsonLogic expression evaluated.

###### <a name="playbooks_items_pages_items_sections_items_scorecards_items_details"></a>8.1.12.1.6.1.8.1.9. Property `details`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Detailed explanation of calculated result.

###### <a name="playbooks_items_pages_items_sections_items_display"></a>8.1.12.1.6.1.9. Property `display`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                      | Pattern | Type            | Deprecated | Definition | Title/Description |
| ----------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| - [analyzers](#playbooks_items_pages_items_sections_items_display_analyzers ) | No      | array of string | No         | -          | -                 |
| - [widgets](#playbooks_items_pages_items_sections_items_display_widgets )     | No      | array of object | No         | -          | -                 |

###### <a name="playbooks_items_pages_items_sections_items_display_analyzers"></a>8.1.12.1.6.1.9.1. Property `analyzers`

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

| Each item of this array must be                                                        | Description |
| -------------------------------------------------------------------------------------- | ----------- |
| [analyzers items](#playbooks_items_pages_items_sections_items_display_analyzers_items) | -           |

###### <a name="playbooks_items_pages_items_sections_items_display_analyzers_items"></a>8.1.12.1.6.1.9.1.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_pages_items_sections_items_display_widgets"></a>8.1.12.1.6.1.9.2. Property `widgets`

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

| Each item of this array must be                                                    | Description |
| ---------------------------------------------------------------------------------- | ----------- |
| [widgets items](#playbooks_items_pages_items_sections_items_display_widgets_items) | -           |

###### <a name="playbooks_items_pages_items_sections_items_display_widgets_items"></a>8.1.12.1.6.1.9.2.1. widgets items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                                              | Pattern | Type   | Deprecated | Definition | Title/Description                          |
| ----------------------------------------------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ------------------------------------------ |
| - [label](#playbooks_items_pages_items_sections_items_display_widgets_items_label )                   | No      | string | No         | -          | Widget display label.                      |
| - [value](#playbooks_items_pages_items_sections_items_display_widgets_items_value )                   | No      | string | No         | -          | Data resolution path.                      |
| - [icon](#playbooks_items_pages_items_sections_items_display_widgets_items_icon )                     | No      | string | No         | -          | Icon identifier or emoji.                  |
| - [resolved_value](#playbooks_items_pages_items_sections_items_display_widgets_items_resolved_value ) | No      | object | No         | -          | The actual value fetched after resolution. |

###### <a name="playbooks_items_pages_items_sections_items_display_widgets_items_label"></a>8.1.12.1.6.1.9.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Widget display label.

###### <a name="playbooks_items_pages_items_sections_items_display_widgets_items_value"></a>8.1.12.1.6.1.9.2.1.2. Property `value`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Data resolution path.

###### <a name="playbooks_items_pages_items_sections_items_display_widgets_items_icon"></a>8.1.12.1.6.1.9.2.1.3. Property `icon`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Icon identifier or emoji.

###### <a name="playbooks_items_pages_items_sections_items_display_widgets_items_resolved_value"></a>8.1.12.1.6.1.9.2.1.4. Property `resolved_value`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** The actual value fetched after resolution.

#### <a name="playbooks_items_mr_templates"></a>8.1.13. Property `mr_templates`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Cookiecutter templates to be run for MR descriptions.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                           | Description |
| --------------------------------------------------------- | ----------- |
| [mr_templates items](#playbooks_items_mr_templates_items) | -           |

##### <a name="playbooks_items_mr_templates_items"></a>8.1.13.1. mr_templates items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                      | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| + [url](#playbooks_items_mr_templates_items_url )             | No      | string | No         | -          | -                 |
| - [directory](#playbooks_items_mr_templates_items_directory ) | No      | string | No         | -          | -                 |

###### <a name="playbooks_items_mr_templates_items_url"></a>8.1.13.1.1. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_mr_templates_items_directory"></a>8.1.13.1.2. Property `directory`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="playbook"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `playbook`

**Title:** playbook.result

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |
| **Same definition as**    | [playbook.result](#playbooks_items)                                         |

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

| Property                                   | Pattern | Type             | Deprecated | Definition | Title/Description                                     |
| ------------------------------------------ | ------- | ---------------- | ---------- | ---------- | ----------------------------------------------------- |
| + [slug](#rules_items_slug )               | No      | string           | No         | -          | Unique identifier for the rule.                       |
| + [description](#rules_items_description ) | No      | string           | No         | -          | Human-readable name of the rule.                      |
| - [level](#rules_items_level )             | No      | string           | No         | -          | Priority level (Gold, Silver, Bronze).                |
| - [tags](#rules_items_tags )               | No      | array of string  | No         | -          | Associated metadata tags.                             |
| + [passed](#rules_items_passed )           | No      | boolean          | No         | -          | Whether the rule criteria were met.                   |
| + [status](#rules_items_status )           | No      | enum (of string) | No         | -          | Detailed execution status.                            |
| + [message](#rules_items_message )         | No      | string           | No         | -          | Reasoning or details for the rule result.             |
| - [analyzers](#rules_items_analyzers )     | No      | array of string  | No         | -          | List of analyzers that contributed data to this rule. |

#### <a name="rules_items_slug"></a>10.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule.

#### <a name="rules_items_description"></a>10.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable name of the rule.

#### <a name="rules_items_level"></a>10.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Priority level (Gold, Silver, Bronze).

#### <a name="rules_items_tags"></a>10.1.4. Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Associated metadata tags.

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

**Description:** Whether the rule criteria were met.

#### <a name="rules_items_status"></a>10.1.6. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Detailed execution status.

Must be one of:
* "passed"
* "failed"
* "incomplete"

#### <a name="rules_items_message"></a>10.1.7. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Reasoning or details for the rule result.

#### <a name="rules_items_analyzers"></a>10.1.8. Property `analyzers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of analyzers that contributed data to this rule.

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

| Property                           | Pattern | Type            | Deprecated | Definition | Title/Description |
| ---------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| - [score](#rules_summary_score )   | No      | integer         | No         | -          | -                 |
| - [total](#rules_summary_total )   | No      | array of string | No         | -          | -                 |
| - [passed](#rules_summary_passed ) | No      | array of string | No         | -          | -                 |
| - [by_tag](#rules_summary_by_tag ) | No      | object          | No         | -          | -                 |

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

| Property                                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#rules_summary_by_tag_additionalProperties ) | No      | object | No         | -          | -                 |

#### <a name="rules_summary_by_tag_additionalProperties"></a>11.4.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                   | Pattern | Type            | Deprecated | Definition | Title/Description                    |
| -------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------ |
| + [rules](#rules_summary_by_tag_additionalProperties_rules )               | No      | array of string | No         | -          | List of rule slugs in this group.    |
| + [passed_rules](#rules_summary_by_tag_additionalProperties_passed_rules ) | No      | array of string | No         | -          | List of slugs for rules that passed. |
| + [score](#rules_summary_by_tag_additionalProperties_score )               | No      | integer         | No         | -          | Percentage score for this group.     |

##### <a name="rules_summary_by_tag_additionalProperties_rules"></a>11.4.1.1. ![Required](https://img.shields.io/badge/Required-blue) Property `rules`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of rule slugs in this group.

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

**Description:** List of slugs for rules that passed.

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

**Description:** Percentage score for this group.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-02 at 09:39:31 +0000
