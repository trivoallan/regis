# report

**Title:** report

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Final report envelope produced by regis, containing request metadata and analyzer results.

| Property                           | Pattern | Type            | Deprecated | Definition                                   | Title/Description                                                                                                             |
| ---------------------------------- | ------- | --------------- | ---------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| + [schemaVersion](#schemaVersion ) | No      | integer         | No         | -                                            | Report-structure contract version. Downstream consumers gate rendering on this. Distinct from \`version\` (package/snapshot). |
| + [version](#version )             | No      | string or null  | No         | -                                            | Version of regis that generated this report.                                                                                  |
| - [tier](#tier )                   | No      | string or null  | No         | -                                            | The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.                                                     |
| - [badges](#badges )               | No      | array of object | No         | -                                            | -                                                                                                                             |
| - [metadata](#metadata )           | No      | object          | No         | -                                            | Arbitrary user-provided metadata (from --meta). Optional namespace exposed to rules as metadata.*.                            |
| - [links](#links )                 | No      | array of object | No         | -                                            | Custom templated links.                                                                                                       |
| + [request](#request )             | No      | object          | No         | -                                            | Metadata describing the analysis request.                                                                                     |
| + [results](#results )             | No      | object          | No         | -                                            | Analyzer results keyed by analyzer name.                                                                                      |
| - [playbooks](#playbooks )         | No      | array           | No         | -                                            | List of evaluated playbook results.                                                                                           |
| - [playbook](#playbook )           | No      | object          | No         | Same as [playbook.result](#playbooks_items ) | playbook.result                                                                                                               |
| - [rules](#rules )                 | No      | array of object | No         | -                                            | List of unified rule results (promoted from playbooks[0]).                                                                    |
| - [rules_summary](#rules_summary ) | No      | object          | No         | -                                            | Summary of rule evaluation results.                                                                                           |

## <a name="schemaVersion"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `schemaVersion`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Report-structure contract version. Downstream consumers gate rendering on this. Distinct from `version` (package/snapshot).

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 1 |

## <a name="version"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Version of regis that generated this report.

## <a name="tier"></a>3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `tier`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.

## <a name="badges"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

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

### <a name="badges_items"></a>4.1. badges items

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

#### <a name="badges_items_slug"></a>4.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

#### <a name="badges_items_scope"></a>4.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Domain of the badge (e.g., 'security', 'hygiene').

#### <a name="badges_items_value"></a>4.1.3. Property `value`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Display value or grade (e.g., 'A', '95%').

#### <a name="badges_items_class"></a>4.1.4. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Visual style indicator.

Must be one of:
* "success"
* "warning"
* "error"
* "information"

#### <a name="badges_items_label"></a>4.1.5. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The full label string (scope or scope: value).

## <a name="metadata"></a>5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `metadata`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Arbitrary user-provided metadata (from --meta). Optional namespace exposed to rules as metadata.*.

| Property                              | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#metadata_additionalProperties ) | No      | object | No         | -          | -                 |

## <a name="links"></a>6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `links`

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

### <a name="links_items"></a>6.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                       | Pattern | Type   | Deprecated | Definition | Title/Description           |
| ------------------------------ | ------- | ------ | ---------- | ---------- | --------------------------- |
| + [label](#links_items_label ) | No      | string | No         | -          | Display label for the link. |
| + [url](#links_items_url )     | No      | string | No         | -          | Target URL.                 |

#### <a name="links_items_label"></a>6.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

#### <a name="links_items_url"></a>6.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

## <a name="request"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `request`

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

### <a name="request_url"></a>7.1. ![Required](https://img.shields.io/badge/Required-blue) Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Original URL or image reference provided by the user.

### <a name="request_registry"></a>7.2. ![Required](https://img.shields.io/badge/Required-blue) Property `registry`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Resolved registry hostname (e.g. registry-1.docker.io).

### <a name="request_repository"></a>7.3. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Full repository path (e.g. library/nginx).

### <a name="request_tag"></a>7.4. ![Required](https://img.shields.io/badge/Required-blue) Property `tag`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Image tag that was analyzed.

### <a name="request_digest"></a>7.5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `digest`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Resolved image manifest digest (e.g. sha256-xxx), if available.

### <a name="request_analyzers"></a>7.6. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzers`

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

#### <a name="request_analyzers_items"></a>7.6.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="request_timestamp"></a>7.7. ![Required](https://img.shields.io/badge/Required-blue) Property `timestamp`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

**Description:** ISO 8601 UTC timestamp of the analysis.

## <a name="results"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `results`

|                           |                                                                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                             |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#results_additionalProperties) |

**Description:** Analyzer results keyed by analyzer name.

| Property                             | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#results_additionalProperties ) | No      | object | No         | -          | -                 |

### <a name="results_additionalProperties"></a>8.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

## <a name="playbooks"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `playbooks`

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

### <a name="playbooks_items"></a>9.1. playbook.result

**Title:** playbook.result

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |
| **Defined in**            | ../playbook/result.schema.json                                              |

**Description:** Final playbook result produced by regis, containing metadata and analyzer results.

| Property                                                 | Pattern | Type            | Deprecated | Definition | Title/Description                                                                |
| -------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | -------------------------------------------------------------------------------- |
| + [playbook_name](#playbooks_items_playbook_name )       | No      | string          | No         | -          | Identifier of the playbook that was executed.                                    |
| - [playbook_version](#playbooks_items_playbook_version ) | No      | string or null  | No         | -          | SemVer of the playbook that produced this report.                                |
| - [api_version](#playbooks_items_api_version )           | No      | string or null  | No         | -          | apiVersion of the playbook that produced this result (e.g. "regis.io/v1alpha1"). |
| - [sidebar](#playbooks_items_sidebar )                   | No      | object          | No         | -          | Sidebar navigation metadata for the report UI.                                   |
| - [version](#playbooks_items_version )                   | No      | string or null  | No         | -          | Version of regis that generated this report.                                     |
| - [tier](#playbooks_items_tier )                         | No      | string or null  | No         | -          | The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.        |
| - [badges](#playbooks_items_badges )                     | No      | array of object | No         | -          | -                                                                                |
| - [rules](#playbooks_items_rules )                       | No      | array of object | No         | -          | -                                                                                |
| - [rules_summary](#playbooks_items_rules_summary )       | No      | object          | No         | -          | -                                                                                |
| + [score](#playbooks_items_score )                       | No      | integer         | No         | -          | Overall percentage of the playbook's rules that passed.                          |
| - [links](#playbooks_items_links )                       | No      | array of object | No         | -          | External links associated with this playbook result.                             |
| - [checklists](#playbooks_items_checklists )             | No      | array of object | No         | -          | Resolved checklists surfaced to downstream integrations.                         |
| - [templates](#playbooks_items_templates )               | No      | array of object | No         | -          | Cookiecutter templates surfaced to downstream integrations.                      |

#### <a name="playbooks_items_playbook_name"></a>9.1.1. Property `playbook_name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Identifier of the playbook that was executed.

#### <a name="playbooks_items_playbook_version"></a>9.1.2. Property `playbook_version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** SemVer of the playbook that produced this report.

#### <a name="playbooks_items_api_version"></a>9.1.3. Property `api_version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** apiVersion of the playbook that produced this result (e.g. "regis.io/v1alpha1").

#### <a name="playbooks_items_sidebar"></a>9.1.4. Property `sidebar`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Sidebar navigation metadata for the report UI.

#### <a name="playbooks_items_version"></a>9.1.5. Property `version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Version of regis that generated this report.

#### <a name="playbooks_items_tier"></a>9.1.6. Property `tier`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** The earned tier (e.g. Gold, Silver, Bronze) based on playbook conditions.

#### <a name="playbooks_items_badges"></a>9.1.7. Property `badges`

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

##### <a name="playbooks_items_badges_items"></a>9.1.7.1. badges items

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

###### <a name="playbooks_items_badges_items_slug"></a>9.1.7.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

###### <a name="playbooks_items_badges_items_scope"></a>9.1.7.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Domain of the badge (e.g., 'security', 'hygiene').

###### <a name="playbooks_items_badges_items_value"></a>9.1.7.1.3. Property `value`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Display value or grade (e.g., 'A', '95%').

###### <a name="playbooks_items_badges_items_class"></a>9.1.7.1.4. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Visual style indicator.

Must be one of:
* "success"
* "warning"
* "error"
* "information"

###### <a name="playbooks_items_badges_items_label"></a>9.1.7.1.5. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The full label string (scope or scope: value).

#### <a name="playbooks_items_rules"></a>9.1.8. Property `rules`

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

##### <a name="playbooks_items_rules_items"></a>9.1.8.1. rules items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                   | Pattern | Type             | Deprecated | Definition | Title/Description                                                                           |
| ---------------------------------------------------------- | ------- | ---------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------- |
| + [slug](#playbooks_items_rules_items_slug )               | No      | string           | No         | -          | Unique identifier for the rule.                                                             |
| + [description](#playbooks_items_rules_items_description ) | No      | string           | No         | -          | Human-readable name of the rule.                                                            |
| - [level](#playbooks_items_rules_items_level )             | No      | string           | No         | -          | Severity level of the rule (e.g. critical, warning, info). Distinct from the playbook tier. |
| - [tags](#playbooks_items_rules_items_tags )               | No      | array of string  | No         | -          | Associated metadata tags.                                                                   |
| + [passed](#playbooks_items_rules_items_passed )           | No      | boolean          | No         | -          | Whether the rule criteria were met.                                                         |
| + [status](#playbooks_items_rules_items_status )           | No      | enum (of string) | No         | -          | Detailed execution status.                                                                  |
| + [message](#playbooks_items_rules_items_message )         | No      | string           | No         | -          | Reasoning or details for the rule result.                                                   |
| - [analyzers](#playbooks_items_rules_items_analyzers )     | No      | array of string  | No         | -          | List of analyzers that contributed data to this rule.                                       |
| - [criterion](#playbooks_items_rules_items_criterion )     | No      | string           | No         | -          | Slug of the criterion template this rule instantiated, when applicable.                     |

###### <a name="playbooks_items_rules_items_slug"></a>9.1.8.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule.

###### <a name="playbooks_items_rules_items_description"></a>9.1.8.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable name of the rule.

###### <a name="playbooks_items_rules_items_level"></a>9.1.8.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Severity level of the rule (e.g. critical, warning, info). Distinct from the playbook tier.

###### <a name="playbooks_items_rules_items_tags"></a>9.1.8.1.4. Property `tags`

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

###### <a name="playbooks_items_rules_items_tags_items"></a>9.1.8.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_items_passed"></a>9.1.8.1.5. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether the rule criteria were met.

###### <a name="playbooks_items_rules_items_status"></a>9.1.8.1.6. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Detailed execution status.

Must be one of:
* "passed"
* "failed"
* "incomplete"

###### <a name="playbooks_items_rules_items_message"></a>9.1.8.1.7. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Reasoning or details for the rule result.

###### <a name="playbooks_items_rules_items_analyzers"></a>9.1.8.1.8. Property `analyzers`

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

###### <a name="playbooks_items_rules_items_analyzers_items"></a>9.1.8.1.8.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_items_criterion"></a>9.1.8.1.9. Property `criterion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Slug of the criterion template this rule instantiated, when applicable.

#### <a name="playbooks_items_rules_summary"></a>9.1.9. Property `rules_summary`

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

##### <a name="playbooks_items_rules_summary_score"></a>9.1.9.1. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

##### <a name="playbooks_items_rules_summary_total"></a>9.1.9.2. Property `total`

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

###### <a name="playbooks_items_rules_summary_total_items"></a>9.1.9.2.1. total items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="playbooks_items_rules_summary_passed"></a>9.1.9.3. Property `passed`

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

###### <a name="playbooks_items_rules_summary_passed_items"></a>9.1.9.3.1. passed items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="playbooks_items_rules_summary_by_tag"></a>9.1.9.4. Property `by_tag`

|                           |                                                                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                                          |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#playbooks_items_rules_summary_by_tag_additionalProperties) |

| Property                                                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#playbooks_items_rules_summary_by_tag_additionalProperties ) | No      | object | No         | -          | -                 |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties"></a>9.1.9.4.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                                   | Pattern | Type            | Deprecated | Definition | Title/Description |
| ------------------------------------------------------------------------------------------ | ------- | --------------- | ---------- | ---------- | ----------------- |
| + [rules](#playbooks_items_rules_summary_by_tag_additionalProperties_rules )               | No      | array of string | No         | -          | -                 |
| + [passed_rules](#playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules ) | No      | array of string | No         | -          | -                 |
| + [score](#playbooks_items_rules_summary_by_tag_additionalProperties_score )               | No      | integer         | No         | -          | -                 |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_rules"></a>9.1.9.4.1.1. Property `rules`

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

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_rules_items"></a>9.1.9.4.1.1.1. rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules"></a>9.1.9.4.1.2. Property `passed_rules`

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

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_passed_rules_items"></a>9.1.9.4.1.2.1. passed_rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_rules_summary_by_tag_additionalProperties_score"></a>9.1.9.4.1.3. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

#### <a name="playbooks_items_score"></a>9.1.10. Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Overall percentage of the playbook's rules that passed.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

#### <a name="playbooks_items_links"></a>9.1.11. Property `links`

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

##### <a name="playbooks_items_links_items"></a>9.1.11.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                       | Pattern | Type   | Deprecated | Definition | Title/Description           |
| ---------------------------------------------- | ------- | ------ | ---------- | ---------- | --------------------------- |
| + [label](#playbooks_items_links_items_label ) | No      | string | No         | -          | Display label for the link. |
| + [url](#playbooks_items_links_items_url )     | No      | string | No         | -          | Target URL.                 |

###### <a name="playbooks_items_links_items_label"></a>9.1.11.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

###### <a name="playbooks_items_links_items_url"></a>9.1.11.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

#### <a name="playbooks_items_checklists"></a>9.1.12. Property `checklists`

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

| Each item of this array must be                       | Description |
| ----------------------------------------------------- | ----------- |
| [checklists items](#playbooks_items_checklists_items) | -           |

##### <a name="playbooks_items_checklists_items"></a>9.1.12.1. checklists items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                            | Pattern | Type            | Deprecated | Definition | Title/Description                |
| --------------------------------------------------- | ------- | --------------- | ---------- | ---------- | -------------------------------- |
| + [title](#playbooks_items_checklists_items_title ) | No      | string          | No         | -          | Display title for the checklist. |
| + [items](#playbooks_items_checklists_items_items ) | No      | array of object | No         | -          | -                                |

###### <a name="playbooks_items_checklists_items_title"></a>9.1.12.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display title for the checklist.

###### <a name="playbooks_items_checklists_items_items"></a>9.1.12.1.2. Property `items`

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

| Each item of this array must be                              | Description |
| ------------------------------------------------------------ | ----------- |
| [items items](#playbooks_items_checklists_items_items_items) | -           |

###### <a name="playbooks_items_checklists_items_items_items"></a>9.1.12.1.2.1. items items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                            | Pattern | Type    | Deprecated | Definition | Title/Description |
| ------------------------------------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| + [label](#playbooks_items_checklists_items_items_items_label )     | No      | string  | No         | -          | -                 |
| + [checked](#playbooks_items_checklists_items_items_items_checked ) | No      | boolean | No         | -          | -                 |

###### <a name="playbooks_items_checklists_items_items_items_label"></a>9.1.12.1.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_checklists_items_items_items_checked"></a>9.1.12.1.2.1.2. Property `checked`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

#### <a name="playbooks_items_templates"></a>9.1.13. Property `templates`

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

| Each item of this array must be                     | Description |
| --------------------------------------------------- | ----------- |
| [templates items](#playbooks_items_templates_items) | -           |

##### <a name="playbooks_items_templates_items"></a>9.1.13.1. templates items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `combining`                                                                 |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                   | Pattern | Type   | Deprecated | Definition | Title/Description |
| ---------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [url](#playbooks_items_templates_items_url )             | No      | string | No         | -          | -                 |
| - [package](#playbooks_items_templates_items_package )     | No      | string | No         | -          | -                 |
| - [directory](#playbooks_items_templates_items_directory ) | No      | string | No         | -          | -                 |

| Any of(Option)                                      |
| --------------------------------------------------- |
| [item 0](#playbooks_items_templates_items_anyOf_i0) |
| [item 1](#playbooks_items_templates_items_anyOf_i1) |

###### <a name="playbooks_items_templates_items_anyOf_i0"></a>9.1.13.1.1. Property `item 0`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

###### <a name="autogenerated_heading_2"></a>9.1.13.1.1.1. The following properties are required
* url

###### <a name="playbooks_items_templates_items_anyOf_i1"></a>9.1.13.1.2. Property `item 1`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

###### <a name="autogenerated_heading_3"></a>9.1.13.1.2.1. The following properties are required
* package

###### <a name="playbooks_items_templates_items_url"></a>9.1.13.1.3. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_templates_items_package"></a>9.1.13.1.4. Property `package`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="playbooks_items_templates_items_directory"></a>9.1.13.1.5. Property `directory`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="playbook"></a>10. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `playbook`

**Title:** playbook.result

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |
| **Same definition as**    | [playbook.result](#playbooks_items)                                         |

**Description:** Primary playbook result (shorthand for playbooks[0]).

## <a name="rules"></a>11. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules`

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

### <a name="rules_items"></a>11.1. rules items

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

#### <a name="rules_items_slug"></a>11.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule.

#### <a name="rules_items_description"></a>11.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable name of the rule.

#### <a name="rules_items_level"></a>11.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Severity level of the rule (e.g. critical, warning, info). Distinct from the playbook tier.

#### <a name="rules_items_tags"></a>11.1.4. Property `tags`

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

##### <a name="rules_items_tags_items"></a>11.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_passed"></a>11.1.5. Property `passed`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether the rule criteria were met.

#### <a name="rules_items_status"></a>11.1.6. Property `status`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Detailed execution status.

Must be one of:
* "passed"
* "failed"
* "incomplete"

#### <a name="rules_items_message"></a>11.1.7. Property `message`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Reasoning or details for the rule result.

#### <a name="rules_items_analyzers"></a>11.1.8. Property `analyzers`

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

##### <a name="rules_items_analyzers_items"></a>11.1.8.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_criterion"></a>11.1.9. Property `criterion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Slug of the criterion template this rule instantiated, when applicable.

## <a name="rules_summary"></a>12. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules_summary`

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

### <a name="rules_summary_score"></a>12.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

### <a name="rules_summary_total"></a>12.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `total`

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

#### <a name="rules_summary_total_items"></a>12.2.1. total items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="rules_summary_passed"></a>12.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `passed`

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

#### <a name="rules_summary_passed_items"></a>12.3.1. passed items

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="rules_summary_by_tag"></a>12.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `by_tag`

|                           |                                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                          |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#rules_summary_by_tag_additionalProperties) |

| Property                                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#rules_summary_by_tag_additionalProperties ) | No      | object | No         | -          | -                 |

#### <a name="rules_summary_by_tag_additionalProperties"></a>12.4.1. Property `additionalProperties`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                   | Pattern | Type            | Deprecated | Definition | Title/Description                    |
| -------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------ |
| + [rules](#rules_summary_by_tag_additionalProperties_rules )               | No      | array of string | No         | -          | List of rule slugs in this group.    |
| + [passed_rules](#rules_summary_by_tag_additionalProperties_passed_rules ) | No      | array of string | No         | -          | List of slugs for rules that passed. |
| + [score](#rules_summary_by_tag_additionalProperties_score )               | No      | integer         | No         | -          | Percentage score for this group.     |

##### <a name="rules_summary_by_tag_additionalProperties_rules"></a>12.4.1.1. ![Required](https://img.shields.io/badge/Required-blue) Property `rules`

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

###### <a name="rules_summary_by_tag_additionalProperties_rules_items"></a>12.4.1.1.1. rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_summary_by_tag_additionalProperties_passed_rules"></a>12.4.1.2. ![Required](https://img.shields.io/badge/Required-blue) Property `passed_rules`

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

###### <a name="rules_summary_by_tag_additionalProperties_passed_rules_items"></a>12.4.1.2.1. passed_rules items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_summary_by_tag_additionalProperties_score"></a>12.4.1.3. ![Required](https://img.shields.io/badge/Required-blue) Property `score`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Percentage score for this group.

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 0   |
| **Maximum**  | &le; 100 |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-06-19 at 19:15:13 +0000
