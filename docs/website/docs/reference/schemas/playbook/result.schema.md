# playbook.result

**Title:** playbook.result

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Final playbook result produced by regis, containing metadata and analyzer results.

| Property                                 | Pattern | Type            | Deprecated | Definition | Title/Description                                                                   |
| ---------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------------------------------------------------------------------------- |
| + [playbook_name](#playbook_name )       | No      | string          | No         | -          | Identifier of the playbook that was executed.                                       |
| - [playbook_version](#playbook_version ) | No      | string or null  | No         | -          | SemVer of the playbook that produced this report.                                   |
| - [ruleset_hash](#ruleset_hash )         | No      | string          | No         | -          | Tamper-evident sha256 fingerprint of the resolved, enforced ruleset (sha256:<hex>). |
| - [api_version](#api_version )           | No      | string or null  | No         | -          | apiVersion of the playbook that produced this result (e.g. "regis.io/v1alpha1").    |
| - [sidebar](#sidebar )                   | No      | object          | No         | -          | Sidebar navigation metadata for the report UI.                                      |
| - [version](#version )                   | No      | string or null  | No         | -          | Version of regis that generated this report.                                        |
| - [tier](#tier )                         | No      | string or null  | No         | -          | The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.           |
| - [badges](#badges )                     | No      | array of object | No         | -          | -                                                                                   |
| - [rules](#rules )                       | No      | array of object | No         | -          | -                                                                                   |
| - [rules_summary](#rules_summary )       | No      | object          | No         | -          | -                                                                                   |
| + [score](#score )                       | No      | integer         | No         | -          | Overall percentage of the playbook's rules that passed.                             |
| - [links](#links )                       | No      | array of object | No         | -          | External links associated with this playbook result.                                |
| - [checklists](#checklists )             | No      | array of object | No         | -          | Resolved checklists surfaced to downstream integrations.                            |
| - [templates](#templates )               | No      | array of object | No         | -          | Cookiecutter templates surfaced to downstream integrations.                         |

## <a name="playbook_name"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `playbook_name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Identifier of the playbook that was executed.

## <a name="playbook_version"></a>2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `playbook_version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** SemVer of the playbook that produced this report.

## <a name="ruleset_hash"></a>3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `ruleset_hash`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Tamper-evident sha256 fingerprint of the resolved, enforced ruleset (sha256:<hex>).

## <a name="api_version"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `api_version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** apiVersion of the playbook that produced this result (e.g. "regis.io/v1alpha1").

## <a name="sidebar"></a>5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `sidebar`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Sidebar navigation metadata for the report UI.

## <a name="version"></a>6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Version of regis that generated this report.

## <a name="tier"></a>7. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `tier`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.

## <a name="badges"></a>8. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

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

### <a name="badges_items"></a>8.1. badges items

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

#### <a name="badges_items_slug"></a>8.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

#### <a name="badges_items_scope"></a>8.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Domain of the badge (e.g., 'security', 'hygiene').

#### <a name="badges_items_value"></a>8.1.3. Property `value`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Display value or grade (e.g., 'A', '95%').

#### <a name="badges_items_class"></a>8.1.4. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Visual style indicator.

Must be one of:
* "success"
* "warning"
* "error"
* "information"

#### <a name="badges_items_label"></a>8.1.5. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The full label string (scope or scope: value).

## <a name="rules"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules`

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
| [rules items](#rules_items)     | -           |

### <a name="rules_items"></a>9.1. rules items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                   | Pattern | Type             | Deprecated | Definition | Title/Description                                                                           |
| ------------------------------------------ | ------- | ---------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------- |
| + [slug](#rules_items_slug )               | No      | string           | No         | -          | Unique identifier for the rule.                                                             |
| + [description](#rules_items_description ) | No      | string           | No         | -          | Human-readable name of the rule.                                                            |
| - [level](#rules_items_level )             | No      | string           | No         | -          | Severity level of the rule (e.g. critical, warning, info). Distinct from the playbook tier. |
| - [tags](#rules_items_tags )               | No      | array of string  | No         | -          | Associated metadata tags.                                                                   |
| + [passed](#rules_items_passed )           | No      | boolean          | No         | -          | Whether the rule criteria were met.                                                         |
| + [status](#rules_items_status )           | No      | enum (of string) | No         | -          | Detailed execution status.                                                                  |
| + [message](#rules_items_message )         | No      | string           | No         | -          | Reasoning or details for the rule result.                                                   |
| - [analyzers](#rules_items_analyzers )     | No      | array of string  | No         | -          | List of analyzers that contributed data to this rule.                                       |
| - [criterion](#rules_items_criterion )     | No      | string           | No         | -          | Slug of the criterion template this rule instantiated, when applicable.                     |

#### <a name="rules_items_slug"></a>9.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule.

#### <a name="rules_items_description"></a>9.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable name of the rule.

#### <a name="rules_items_level"></a>9.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Severity level of the rule (e.g. critical, warning, info). Distinct from the playbook tier.

#### <a name="rules_items_tags"></a>9.1.4. Property `tags`

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

##### <a name="rules_items_tags_items"></a>9.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_passed"></a>9.1.5. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether the rule criteria were met.

#### <a name="rules_items_status"></a>9.1.6. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Detailed execution status.

Must be one of:
* "passed"
* "failed"
* "incomplete"

#### <a name="rules_items_message"></a>9.1.7. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Reasoning or details for the rule result.

#### <a name="rules_items_analyzers"></a>9.1.8. Property `analyzers`

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

##### <a name="rules_items_analyzers_items"></a>9.1.8.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_criterion"></a>9.1.9. Property `criterion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Slug of the criterion template this rule instantiated, when applicable.

## <a name="rules_summary"></a>10. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules_summary`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                           | Pattern | Type            | Deprecated | Definition | Title/Description |
| ---------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| + [score](#rules_summary_score )   | No      | integer         | No         | -          | -                 |
| + [total](#rules_summary_total )   | No      | array of string | No         | -          | -                 |
| + [passed](#rules_summary_passed ) | No      | array of string | No         | -          | -                 |
| - [by_tag](#rules_summary_by_tag ) | No      | object          | No         | -          | -                 |

### <a name="rules_summary_score"></a>10.1. ![Required](https://img.shields.io/badge/Required-blue) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

### <a name="rules_summary_total"></a>10.2. ![Required](https://img.shields.io/badge/Required-blue) Property `total`

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

#### <a name="rules_summary_total_items"></a>10.2.1. total items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="rules_summary_passed"></a>10.3. ![Required](https://img.shields.io/badge/Required-blue) Property `passed`

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

#### <a name="rules_summary_passed_items"></a>10.3.1. passed items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="rules_summary_by_tag"></a>10.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `by_tag`

|                           |                                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                          |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#rules_summary_by_tag_additionalProperties) |

| Property                                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#rules_summary_by_tag_additionalProperties ) | No      | object | No         | -          | -                 |

#### <a name="rules_summary_by_tag_additionalProperties"></a>10.4.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                   | Pattern | Type            | Deprecated | Definition | Title/Description |
| -------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| + [rules](#rules_summary_by_tag_additionalProperties_rules )               | No      | array of string | No         | -          | -                 |
| + [passed_rules](#rules_summary_by_tag_additionalProperties_passed_rules ) | No      | array of string | No         | -          | -                 |
| + [score](#rules_summary_by_tag_additionalProperties_score )               | No      | integer         | No         | -          | -                 |

##### <a name="rules_summary_by_tag_additionalProperties_rules"></a>10.4.1.1. ![Required](https://img.shields.io/badge/Required-blue) Property `rules`

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

###### <a name="rules_summary_by_tag_additionalProperties_rules_items"></a>10.4.1.1.1. rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_summary_by_tag_additionalProperties_passed_rules"></a>10.4.1.2. ![Required](https://img.shields.io/badge/Required-blue) Property `passed_rules`

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

###### <a name="rules_summary_by_tag_additionalProperties_passed_rules_items"></a>10.4.1.2.1. passed_rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_summary_by_tag_additionalProperties_score"></a>10.4.1.3. ![Required](https://img.shields.io/badge/Required-blue) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

## <a name="score"></a>11. ![Required](https://img.shields.io/badge/Required-blue) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Overall percentage of the playbook's rules that passed.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

## <a name="links"></a>12. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `links`

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

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [links items](#links_items)     | -           |

### <a name="links_items"></a>12.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                       | Pattern | Type   | Deprecated | Definition | Title/Description           |
| ------------------------------ | ------- | ------ | ---------- | ---------- | --------------------------- |
| + [label](#links_items_label ) | No      | string | No         | -          | Display label for the link. |
| + [url](#links_items_url )     | No      | string | No         | -          | Target URL.                 |

#### <a name="links_items_label"></a>12.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

#### <a name="links_items_url"></a>12.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

## <a name="checklists"></a>13. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checklists`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Resolved checklists surfaced to downstream integrations.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be       | Description |
| ------------------------------------- | ----------- |
| [checklists items](#checklists_items) | -           |

### <a name="checklists_items"></a>13.1. checklists items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                            | Pattern | Type            | Deprecated | Definition | Title/Description                |
| ----------------------------------- | ------- | --------------- | ---------- | ---------- | -------------------------------- |
| + [title](#checklists_items_title ) | No      | string          | No         | -          | Display title for the checklist. |
| + [items](#checklists_items_items ) | No      | array of object | No         | -          | -                                |

#### <a name="checklists_items_title"></a>13.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display title for the checklist.

#### <a name="checklists_items_items"></a>13.1.2. Property `items`

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

| Each item of this array must be              | Description |
| -------------------------------------------- | ----------- |
| [items items](#checklists_items_items_items) | -           |

##### <a name="checklists_items_items_items"></a>13.1.2.1. items items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                            | Pattern | Type    | Deprecated | Definition | Title/Description |
| --------------------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| + [label](#checklists_items_items_items_label )     | No      | string  | No         | -          | -                 |
| + [checked](#checklists_items_items_items_checked ) | No      | boolean | No         | -          | -                 |

###### <a name="checklists_items_items_items_label"></a>13.1.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="checklists_items_items_items_checked"></a>13.1.2.1.2. Property `checked`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

## <a name="templates"></a>14. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `templates`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Cookiecutter templates surfaced to downstream integrations.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be     | Description |
| ----------------------------------- | ----------- |
| [templates items](#templates_items) | -           |

### <a name="templates_items"></a>14.1. templates items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `combining`                                                                 |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                   | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [url](#templates_items_url )             | No      | string | No         | -          | -                 |
| - [package](#templates_items_package )     | No      | string | No         | -          | -                 |
| - [directory](#templates_items_directory ) | No      | string | No         | -          | -                 |

| Any of(Option)                      |
| ----------------------------------- |
| [item 0](#templates_items_anyOf_i0) |
| [item 1](#templates_items_anyOf_i1) |

#### <a name="templates_items_anyOf_i0"></a>14.1.1. Property `item 0`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

##### <a name="autogenerated_heading_2"></a>14.1.1.1. The following properties are required
* url

#### <a name="templates_items_anyOf_i1"></a>14.1.2. Property `item 1`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

##### <a name="autogenerated_heading_3"></a>14.1.2.1. The following properties are required
* package

#### <a name="templates_items_url"></a>14.1.3. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="templates_items_package"></a>14.1.4. Property `package`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="templates_items_directory"></a>14.1.5. Property `directory`

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-07-27 at 01:58:23 +0000
