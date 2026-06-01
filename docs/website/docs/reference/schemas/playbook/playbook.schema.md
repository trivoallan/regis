# playbook.v1alpha1.Playbook

**Title:** playbook.v1alpha1.Playbook

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Schema for regis Playbook resources (Kubernetes-style envelope).

| Property                     | Pattern | Type   | Deprecated | Definition | Title/Description                                                  |
| ---------------------------- | ------- | ------ | ---------- | ---------- | ------------------------------------------------------------------ |
| + [apiVersion](#apiVersion ) | No      | const  | No         | -          | API group and version. Must equal 'regis.trivoallan.dev/v1alpha1'. |
| + [kind](#kind )             | No      | const  | No         | -          | Resource kind. Must equal 'Playbook'.                              |
| + [metadata](#metadata )     | No      | object | No         | -          | -                                                                  |
| + [spec](#spec )             | No      | object | No         | -          | Playbook body: rules, tiers, badges, integrations, links.          |

## <a name="apiVersion"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `apiVersion`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** API group and version. Must equal 'regis.trivoallan.dev/v1alpha1'.

Specific value: `"regis.trivoallan.dev/v1alpha1"`

## <a name="kind"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `kind`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Resource kind. Must equal 'Playbook'.

Specific value: `"Playbook"`

## <a name="metadata"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `metadata`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                | Pattern | Type   | Deprecated | Definition | Title/Description                                                         |
| --------------------------------------- | ------- | ------ | ---------- | ---------- | ------------------------------------------------------------------------- |
| + [name](#metadata_name )               | No      | string | No         | -          | Machine identifier (RFC 1123 DNS label): lowercase alphanumerics and '-'. |
| - [title](#metadata_title )             | No      | string | No         | -          | Human-readable display name.                                              |
| - [description](#metadata_description ) | No      | string | No         | -          | Human-readable description of what this playbook evaluates.               |
| + [labels](#metadata_labels )           | No      | object | No         | -          | -                                                                         |
| - [annotations](#metadata_annotations ) | No      | object | No         | -          | Free-form non-identifying metadata.                                       |

### <a name="metadata_name"></a>3.1. ![Required](https://img.shields.io/badge/Required-blue) Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Machine identifier (RFC 1123 DNS label): lowercase alphanumerics and '-'.

| Restrictions                      |                                                                                                                                   |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Max length**                    | 63                                                                                                                                |
| **Must match regular expression** | ```^[a-z0-9]([-a-z0-9]*[a-z0-9])?$``` [Test](https://regex101.com/?regex=%5E%5Ba-z0-9%5D%28%5B-a-z0-9%5D%2A%5Ba-z0-9%5D%29%3F%24) |

### <a name="metadata_title"></a>3.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable display name.

### <a name="metadata_description"></a>3.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable description of what this playbook evaluates.

### <a name="metadata_labels"></a>3.4. ![Required](https://img.shields.io/badge/Required-blue) Property `labels`

|                           |                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Type**                  | `object`                                                                                                     |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#metadata_labels_additionalProperties) |

| Property                                                                 | Pattern | Type   | Deprecated | Definition | Title/Description                             |
| ------------------------------------------------------------------------ | ------- | ------ | ---------- | ---------- | --------------------------------------------- |
| + [app.kubernetes.io/version](#metadata_labels_appkubernetesio/version ) | No      | string | No         | -          | SemVer of the playbook bundle (e.g. "1.2.3"). |
| - [](#metadata_labels_additionalProperties )                             | No      | string | No         | -          | -                                             |

#### <a name="metadata_labels_appkubernetesio/version"></a>3.4.1. ![Required](https://img.shields.io/badge/Required-blue) Property `app.kubernetes.io/version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** SemVer of the playbook bundle (e.g. "1.2.3").

| Restrictions                      |                                                                                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Must match regular expression** | ```^(0\|[1-9]\d*)\.(0\|[1-9]\d*)\.(0\|[1-9]\d*)$``` [Test](https://regex101.com/?regex=%5E%280%7C%5B1-9%5D%5Cd%2A%29%5C.%280%7C%5B1-9%5D%5Cd%2A%29%5C.%280%7C%5B1-9%5D%5Cd%2A%29%24) |

#### <a name="metadata_labels_additionalProperties"></a>3.4.2. Property `additionalProperties`

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="metadata_annotations"></a>3.5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `annotations`

|                           |                                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                                          |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#metadata_annotations_additionalProperties) |

**Description:** Free-form non-identifying metadata.

| Property                                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#metadata_annotations_additionalProperties ) | No      | string | No         | -          | -                 |

#### <a name="metadata_annotations_additionalProperties"></a>3.5.1. Property `additionalProperties`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="spec"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `spec`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Playbook body: rules, tiers, badges, integrations, links.

| Property                              | Pattern | Type            | Deprecated | Definition | Title/Description                                                                                                           |
| ------------------------------------- | ------- | --------------- | ---------- | ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| - [links](#spec_links )               | No      | array of object | No         | -          | Optional custom links to display as actions for this playbook.                                                              |
| - [integrations](#spec_integrations ) | No      | object          | No         | -          | Optional third-party platform integrations (e.g. GitLab, GitHub).                                                           |
| - [rules](#spec_rules )               | No      | array of object | No         | -          | Custom rule overrides or template instantiations.                                                                           |
| - [tiers](#spec_tiers )               | No      | array of object | No         | -          | Compliance tier thresholds. Each tier is awarded when its JsonLogic condition evaluates to true, evaluated in order.        |
| - [badges](#spec_badges )             | No      | array of object | No         | -          | Dynamic status badges displayed in the report header. Each badge is conditionally rendered based on a JsonLogic expression. |

### <a name="spec_links"></a>4.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `links`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Optional custom links to display as actions for this playbook.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be  | Description |
| -------------------------------- | ----------- |
| [links items](#spec_links_items) | -           |

#### <a name="spec_links_items"></a>4.1.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                    | Pattern | Type                                           | Deprecated | Definition                  | Title/Description                                                         |
| ------------------------------------------- | ------- | ---------------------------------------------- | ---------- | --------------------------- | ------------------------------------------------------------------------- |
| + [label](#spec_links_items_label )         | No      | string                                         | No         | -                           | Display label for the link.                                               |
| + [url](#spec_links_items_url )             | No      | string                                         | No         | -                           | URL template which can use {metadata[key]} placeholders or Jinja2 syntax. |
| - [condition](#spec_links_items_condition ) | No      | object, array, string, number, boolean or null | No         | In ../jsonlogic.schema.json | jsonlogic                                                                 |

##### <a name="spec_links_items_label"></a>4.1.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

##### <a name="spec_links_items_url"></a>4.1.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** URL template which can use {metadata[key]} placeholders or Jinja2 syntax.

##### <a name="spec_links_items_condition"></a>4.1.1.3. Property `condition`

**Title:** jsonlogic

|                |                                                  |
| -------------- | ------------------------------------------------ |
| **Type**       | `object, array, string, number, boolean or null` |
| **Defined in** | ../jsonlogic.schema.json                         |

**Description:** Optional JsonLogic expression to determine if the link should be displayed.

### <a name="spec_integrations"></a>4.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `integrations`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional third-party platform integrations (e.g. GitLab, GitHub).

| Property                               | Pattern | Type   | Deprecated | Definition | Title/Description |
| -------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [gitlab](#spec_integrations_gitlab ) | No      | object | No         | -          | -                 |

#### <a name="spec_integrations_gitlab"></a>4.2.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `gitlab`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                              | Pattern | Type            | Deprecated | Definition | Title/Description                                                                           |
| ----------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------- |
| - [badges](#spec_integrations_gitlab_badges )         | No      | array of string | No         | -          | List of badge slugs to be imported as GitLab Merge Request labels.                          |
| - [checklist](#spec_integrations_gitlab_checklist )   | No      | array           | No         | -          | (Deprecated) Single checklist items added as checkboxes to the Merge Request description.   |
| - [checklists](#spec_integrations_gitlab_checklists ) | No      | array of object | No         | -          | Configurable checklists added as checkboxes to the Merge Request description.               |
| - [templates](#spec_integrations_gitlab_templates )   | No      | array of object | No         | -          | URLs to Cookiecutter templates that will be rendered and added to the Merge Request branch. |

##### <a name="spec_integrations_gitlab_badges"></a>4.2.1.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of badge slugs to be imported as GitLab Merge Request labels.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                        | Description |
| ------------------------------------------------------ | ----------- |
| [badges items](#spec_integrations_gitlab_badges_items) | -           |

###### <a name="spec_integrations_gitlab_badges_items"></a>4.2.1.1.1. badges items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="spec_integrations_gitlab_checklist"></a>4.2.1.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checklist`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** (Deprecated) Single checklist items added as checkboxes to the Merge Request description.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                             | Description |
| ----------------------------------------------------------- | ----------- |
| [checklist_item](#spec_integrations_gitlab_checklist_items) | -           |

###### <a name="spec_integrations_gitlab_checklist_items"></a>4.2.1.2.1. checklist_item

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/checklist_item                                         |

| Property                                                          | Pattern | Type   | Deprecated | Definition | Title/Description                                                                                                                                     |
| ----------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| + [label](#spec_integrations_gitlab_checklist_items_label )       | No      | string | No         | -          | Text of the checkbox item.                                                                                                                            |
| - [show_if](#spec_integrations_gitlab_checklist_items_show_if )   | No      | object | No         | -          | Optional JsonLogic expression. If provided, the item is only included when the expression evaluates to truthy.                                        |
| - [check_if](#spec_integrations_gitlab_checklist_items_check_if ) | No      | object | No         | -          | Optional JsonLogic expression. If provided and evaluates to truthy, the checkbox renders pre-checked (- [x]). Otherwise it renders unchecked (- [ ]). |

###### <a name="spec_integrations_gitlab_checklist_items_label"></a>4.2.1.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Text of the checkbox item.

###### <a name="spec_integrations_gitlab_checklist_items_show_if"></a>4.2.1.2.1.2. Property `show_if`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional JsonLogic expression. If provided, the item is only included when the expression evaluates to truthy.

###### <a name="spec_integrations_gitlab_checklist_items_check_if"></a>4.2.1.2.1.3. Property `check_if`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional JsonLogic expression. If provided and evaluates to truthy, the checkbox renders pre-checked (- [x]). Otherwise it renders unchecked (- [ ]).

##### <a name="spec_integrations_gitlab_checklists"></a>4.2.1.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checklists`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Configurable checklists added as checkboxes to the Merge Request description.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                | Description |
| -------------------------------------------------------------- | ----------- |
| [checklists items](#spec_integrations_gitlab_checklists_items) | -           |

###### <a name="spec_integrations_gitlab_checklists_items"></a>4.2.1.3.1. checklists items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                     | Pattern | Type   | Deprecated | Definition | Title/Description                |
| ------------------------------------------------------------ | ------- | ------ | ---------- | ---------- | -------------------------------- |
| - [title](#spec_integrations_gitlab_checklists_items_title ) | No      | string | No         | -          | Display title for the checklist. |
| + [items](#spec_integrations_gitlab_checklists_items_items ) | No      | array  | No         | -          | Items in this checklist.         |

###### <a name="spec_integrations_gitlab_checklists_items_title"></a>4.2.1.3.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display title for the checklist.

###### <a name="spec_integrations_gitlab_checklists_items_items"></a>4.2.1.3.1.2. Property `items`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** Items in this checklist.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                          | Description |
| ------------------------------------------------------------------------ | ----------- |
| [checklist_item](#spec_integrations_gitlab_checklists_items_items_items) | -           |

###### <a name="spec_integrations_gitlab_checklists_items_items_items"></a>4.2.1.3.1.2.1. checklist_item

|                           |                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                              |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red)                        |
| **Same definition as**    | [spec_integrations_gitlab_checklist_items](#spec_integrations_gitlab_checklist_items) |

##### <a name="spec_integrations_gitlab_templates"></a>4.2.1.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `templates`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** URLs to Cookiecutter templates that will be rendered and added to the Merge Request branch.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                              | Description |
| ------------------------------------------------------------ | ----------- |
| [templates items](#spec_integrations_gitlab_templates_items) | -           |

###### <a name="spec_integrations_gitlab_templates_items"></a>4.2.1.4.1. templates items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                                            | Pattern | Type                                           | Deprecated | Definition                                        | Title/Description                                                    |
| ------------------------------------------------------------------- | ------- | ---------------------------------------------- | ---------- | ------------------------------------------------- | -------------------------------------------------------------------- |
| + [url](#spec_integrations_gitlab_templates_items_url )             | No      | string                                         | No         | -                                                 | Cookiecutter template URL or path.                                   |
| - [directory](#spec_integrations_gitlab_templates_items_directory ) | No      | string                                         | No         | -                                                 | Optional subdirectory within the repository containing the template. |
| - [condition](#spec_integrations_gitlab_templates_items_condition ) | No      | object, array, string, number, boolean or null | No         | Same as [condition](#spec_links_items_condition ) | jsonlogic                                                            |

###### <a name="spec_integrations_gitlab_templates_items_url"></a>4.2.1.4.1.1. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Cookiecutter template URL or path.

###### <a name="spec_integrations_gitlab_templates_items_directory"></a>4.2.1.4.1.2. Property `directory`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Optional subdirectory within the repository containing the template.

###### <a name="spec_integrations_gitlab_templates_items_condition"></a>4.2.1.4.1.3. Property `condition`

**Title:** jsonlogic

|                        |                                                  |
| ---------------------- | ------------------------------------------------ |
| **Type**               | `object, array, string, number, boolean or null` |
| **Same definition as** | [condition](#spec_links_items_condition)         |

**Description:** JSON Logic expression to conditionally render the template.

### <a name="spec_rules"></a>4.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Custom rule overrides or template instantiations.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be  | Description |
| -------------------------------- | ----------- |
| [rules items](#spec_rules_items) | -           |

#### <a name="spec_rules_items"></a>4.3.1. rules items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                  | Pattern | Type             | Deprecated | Definition | Title/Description                                   |
| ----------------------------------------- | ------- | ---------------- | ---------- | ---------- | --------------------------------------------------- |
| - [slug](#spec_rules_items_slug )         | No      | string           | No         | -          | Unique identifier for the rule instance.            |
| - [provider](#spec_rules_items_provider ) | No      | string           | No         | -          | Analyzer name (e.g. 'cve').                         |
| - [rule](#spec_rules_items_rule )         | No      | string           | No         | -          | Template name within the provider (e.g. 'cve-max'). |
| - [options](#spec_rules_items_options )   | No      | object           | No         | -          | Configuration parameters for the rule template.     |
| - [enable](#spec_rules_items_enable )     | No      | boolean          | No         | -          | Whether to enable this rule.                        |
| - [level](#spec_rules_items_level )       | No      | enum (of string) | No         | -          | Severity level of the rule.                         |
| - [tags](#spec_rules_items_tags )         | No      | array of string  | No         | -          | Arbitrary tags.                                     |
| - [messages](#spec_rules_items_messages ) | No      | object           | No         | -          | -                                                   |

##### <a name="spec_rules_items_slug"></a>4.3.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule instance.

##### <a name="spec_rules_items_provider"></a>4.3.1.2. Property `provider`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Analyzer name (e.g. 'cve').

##### <a name="spec_rules_items_rule"></a>4.3.1.3. Property `rule`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Template name within the provider (e.g. 'cve-max').

##### <a name="spec_rules_items_options"></a>4.3.1.4. Property `options`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Configuration parameters for the rule template.

| Property                                              | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#spec_rules_items_options_additionalProperties ) | No      | object | No         | -          | -                 |

##### <a name="spec_rules_items_enable"></a>4.3.1.5. Property `enable`

|             |           |
| ----------- | --------- |
| **Type**    | `boolean` |
| **Default** | `true`    |

**Description:** Whether to enable this rule.

##### <a name="spec_rules_items_level"></a>4.3.1.6. Property `level`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Severity level of the rule.

Must be one of:
* "info"
* "warning"
* "critical"
* "none"

##### <a name="spec_rules_items_tags"></a>4.3.1.7. Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Arbitrary tags.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be            | Description |
| ------------------------------------------ | ----------- |
| [tags items](#spec_rules_items_tags_items) | -           |

###### <a name="spec_rules_items_tags_items"></a>4.3.1.7.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="spec_rules_items_messages"></a>4.3.1.8. Property `messages`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                   | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [pass](#spec_rules_items_messages_pass ) | No      | string | No         | -          | -                 |
| - [fail](#spec_rules_items_messages_fail ) | No      | string | No         | -          | -                 |

###### <a name="spec_rules_items_messages_pass"></a>4.3.1.8.1. Property `pass`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="spec_rules_items_messages_fail"></a>4.3.1.8.2. Property `fail`

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="spec_tiers"></a>4.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `tiers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Compliance tier thresholds. Each tier is awarded when its JsonLogic condition evaluates to true, evaluated in order.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be  | Description |
| -------------------------------- | ----------- |
| [tiers items](#spec_tiers_items) | -           |

#### <a name="spec_tiers_items"></a>4.4.1. tiers items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                    | Pattern | Type                                           | Deprecated | Definition                                        | Title/Description                      |
| ------------------------------------------- | ------- | ---------------------------------------------- | ---------- | ------------------------------------------------- | -------------------------------------- |
| + [name](#spec_tiers_items_name )           | No      | string                                         | No         | -                                                 | Tier name (e.g. Gold, Silver, Bronze). |
| + [condition](#spec_tiers_items_condition ) | No      | object, array, string, number, boolean or null | No         | Same as [condition](#spec_links_items_condition ) | jsonlogic                              |

##### <a name="spec_tiers_items_name"></a>4.4.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Tier name (e.g. Gold, Silver, Bronze).

##### <a name="spec_tiers_items_condition"></a>4.4.1.2. Property `condition`

**Title:** jsonlogic

|                        |                                                  |
| ---------------------- | ------------------------------------------------ |
| **Type**               | `object, array, string, number, boolean or null` |
| **Same definition as** | [condition](#spec_links_items_condition)         |

**Description:** JsonLogic expression evaluated against the report context.

### <a name="spec_badges"></a>4.5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** Dynamic status badges displayed in the report header. Each badge is conditionally rendered based on a JsonLogic expression.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be    | Description |
| ---------------------------------- | ----------- |
| [badges items](#spec_badges_items) | -           |

#### <a name="spec_badges_items"></a>4.5.1. badges items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                     | Pattern | Type                                           | Deprecated | Definition                                        | Title/Description                                                             |
| -------------------------------------------- | ------- | ---------------------------------------------- | ---------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| + [slug](#spec_badges_items_slug )           | No      | string                                         | No         | -                                                 | Unique identifier for the badge.                                              |
| + [scope](#spec_badges_items_scope )         | No      | string                                         | No         | -                                                 | Category label displayed on the left part of the badge (e.g. CVE, Freshness). |
| + [value](#spec_badges_items_value )         | No      | string                                         | No         | -                                                 | Value displayed on the right part of the badge.                               |
| + [condition](#spec_badges_items_condition ) | No      | object, array, string, number, boolean or null | No         | Same as [condition](#spec_links_items_condition ) | jsonlogic                                                                     |
| + [class](#spec_badges_items_class )         | No      | enum (of string)                               | No         | -                                                 | Visual style class for the badge.                                             |

##### <a name="spec_badges_items_slug"></a>4.5.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

##### <a name="spec_badges_items_scope"></a>4.5.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Category label displayed on the left part of the badge (e.g. CVE, Freshness).

##### <a name="spec_badges_items_value"></a>4.5.1.3. Property `value`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Value displayed on the right part of the badge.

##### <a name="spec_badges_items_condition"></a>4.5.1.4. Property `condition`

**Title:** jsonlogic

|                        |                                                  |
| ---------------------- | ------------------------------------------------ |
| **Type**               | `object, array, string, number, boolean or null` |
| **Same definition as** | [condition](#spec_links_items_condition)         |

**Description:** JsonLogic expression. The badge is shown when this evaluates to truthy.

##### <a name="spec_badges_items_class"></a>4.5.1.5. Property `class`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Visual style class for the badge.

Must be one of:
* "success"
* "warning"
* "error"
* "information"

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-06-01 at 16:51:05 +0000
