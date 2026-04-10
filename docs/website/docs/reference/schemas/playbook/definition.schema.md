# playbook.definition

**Title:** playbook.definition

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Schema for regis playbook definition files (YAML or JSON).

| Property                         | Pattern | Type            | Deprecated | Definition | Title/Description                                                                                                                        |
| -------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| + [name](#name )                 | No      | string          | No         | -          | Display name of the playbook.                                                                                                            |
| - [description](#description )   | No      | string          | No         | -          | Human-readable description of what this playbook evaluates.                                                                              |
| - [slug](#slug )                 | No      | string          | No         | -          | Short identifier used for HTML report filename generation.                                                                               |
| - [links](#links )               | No      | array of object | No         | -          | Optional custom links to display as actions for this playbook.                                                                           |
| - [pages](#pages )               | No      | array           | No         | -          | Deprecated: List of playbook pages for the legacy Jinja2 HTML renderer. Not used by the Docusaurus report viewer. Use \`rules\` instead. |
| - [sections](#sections )         | No      | array           | No         | -          | Deprecated: List of playbook sections for the legacy renderer. Not used by the Docusaurus report viewer. Use \`rules\` instead.          |
| - [sidebar](#sidebar )           | No      | object          | No         | -          | Deprecated: Sidebar navigation for the legacy Jinja2 renderer.                                                                           |
| - [integrations](#integrations ) | No      | object          | No         | -          | Optional third-party platform integrations (e.g. GitLab, GitHub).                                                                        |
| - [rules](#rules )               | No      | array of object | No         | -          | Custom rule overrides or template instantiations.                                                                                        |
| - [tiers](#tiers )               | No      | array of object | No         | -          | Compliance tier thresholds. Each tier is awarded when its JsonLogic condition evaluates to true, evaluated in order.                     |
| - [badges](#badges )             | No      | array of object | No         | -          | Dynamic status badges displayed in the report header. Each badge is conditionally rendered based on a JsonLogic expression.              |

## <a name="name"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display name of the playbook.

## <a name="description"></a>2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable description of what this playbook evaluates.

## <a name="slug"></a>3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Short identifier used for HTML report filename generation.

## <a name="links"></a>4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `links`

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

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [links items](#links_items)     | -           |

### <a name="links_items"></a>4.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                               | Pattern | Type                                           | Deprecated | Definition               | Title/Description                                                         |
| -------------------------------------- | ------- | ---------------------------------------------- | ---------- | ------------------------ | ------------------------------------------------------------------------- |
| + [label](#links_items_label )         | No      | string                                         | No         | -                        | Display label for the link.                                               |
| + [url](#links_items_url )             | No      | string                                         | No         | -                        | URL template which can use {metadata[key]} placeholders or Jinja2 syntax. |
| - [condition](#links_items_condition ) | No      | object, array, string, number, boolean or null | No         | In jsonlogic.schema.json | jsonlogic                                                                 |

#### <a name="links_items_label"></a>4.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the link.

#### <a name="links_items_url"></a>4.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** URL template which can use {metadata[key]} placeholders or Jinja2 syntax.

#### <a name="links_items_condition"></a>4.1.3. Property `condition`

**Title:** jsonlogic

|                |                                                  |
| -------------- | ------------------------------------------------ |
| **Type**       | `object, array, string, number, boolean or null` |
| **Defined in** | jsonlogic.schema.json                            |

**Description:** Optional JsonLogic expression to determine if the link should be displayed.

## <a name="pages"></a>5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `pages`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** Deprecated: List of playbook pages for the legacy Jinja2 HTML renderer. Not used by the Docusaurus report viewer. Use `rules` instead.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | 1                  |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description                          |
| ------------------------------- | ------------------------------------ |
| [page](#pages_items)            | A playbook page containing sections. |

### <a name="pages_items"></a>5.1. page

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/page                                                   |

**Description:** A playbook page containing sections.

| Property                             | Pattern | Type   | Deprecated | Definition | Title/Description                                                                                               |
| ------------------------------------ | ------- | ------ | ---------- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| + [title](#pages_items_title )       | No      | string | No         | -          | Display name of the page.                                                                                       |
| - [slug](#pages_items_slug )         | No      | string | No         | -          | Short identifier used for HTML report filename generation. If not provided, it falls back to the playbook slug. |
| + [sections](#pages_items_sections ) | No      | array  | No         | -          | List of playbook sections.                                                                                      |

#### <a name="pages_items_title"></a>5.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display name of the page.

#### <a name="pages_items_slug"></a>5.1.2. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Short identifier used for HTML report filename generation. If not provided, it falls back to the playbook slug.

#### <a name="pages_items_sections"></a>5.1.3. Property `sections`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** List of playbook sections.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | 1                  |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be        | Description                                                                         |
| -------------------------------------- | ----------------------------------------------------------------------------------- |
| [section](#pages_items_sections_items) | A playbook section containing scorecards, optional levels, and display preferences. |

##### <a name="pages_items_sections_items"></a>5.1.3.1. section

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/section                                                |

**Description:** A playbook section containing scorecards, optional levels, and display preferences.

| Property                                                | Pattern | Type   | Deprecated | Definition         | Title/Description                                                                                                     |
| ------------------------------------------------------- | ------- | ------ | ---------- | ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| - [name](#pages_items_sections_items_name )             | No      | string | No         | -                  | Display name of the section.                                                                                          |
| - [hint](#pages_items_sections_items_hint )             | No      | string | No         | -                  | Optional informative text displayed below the section name.                                                           |
| - [display](#pages_items_sections_items_display )       | No      | object | No         | In #/$defs/display | Rendering preferences for the section.                                                                                |
| - [levels](#pages_items_sections_items_levels )         | No      | array  | No         | -                  | Priority/severity levels used to group scorecards. Built-in fallback order exists for bronze, silver, gold.           |
| - [scorecards](#pages_items_sections_items_scorecards ) | No      | array  | No         | -                  | Evaluation scorecards with JsonLogic conditions.                                                                      |
| - [widgets](#pages_items_sections_items_widgets )       | No      | array  | No         | -                  | KPI and Template widgets displayed in the section.                                                                    |
| - [condition](#pages_items_sections_items_condition )   | No      | object | No         | -                  | Optional jsonLogic expression to conditionally display this section. If it evaluates to falsy, the section is hidden. |

###### <a name="pages_items_sections_items_name"></a>5.1.3.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display name of the section.

###### <a name="pages_items_sections_items_hint"></a>5.1.3.1.2. Property `hint`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Optional informative text displayed below the section name.

###### <a name="pages_items_sections_items_display"></a>5.1.3.1.3. Property `display`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/display                                                |

**Description:** Rendering preferences for the section.

| Property                                                      | Pattern | Type            | Deprecated | Definition | Title/Description                                                       |
| ------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------------------------------------------------------------- |
| - [analyzers](#pages_items_sections_items_display_analyzers ) | No      | array of string | No         | -          | List of analyzer names whose output should be embedded in this section. |
| - [widgets](#pages_items_sections_items_display_widgets )     | No      | array           | No         | -          | KPI widgets displayed in the section header.                            |

###### <a name="pages_items_sections_items_display_analyzers"></a>5.1.3.1.3.1. Property `analyzers`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of analyzer names whose output should be embedded in this section.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                        | Description |
| ---------------------------------------------------------------------- | ----------- |
| [analyzers items](#pages_items_sections_items_display_analyzers_items) | -           |

###### <a name="pages_items_sections_items_display_analyzers_items"></a>5.1.3.1.3.1.1. analyzers items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="pages_items_sections_items_display_widgets"></a>5.1.3.1.3.2. Property `widgets`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** KPI widgets displayed in the section header.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                             | Description                                                                                        |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| [widget](#pages_items_sections_items_display_widgets_items) | A key-value widget displaying a metric from the analysis report, or a custom HTML template widget. |

###### <a name="pages_items_sections_items_display_widgets_items"></a>5.1.3.1.3.2.1. widget

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/widget                                                 |

**Description:** A key-value widget displaying a metric from the analysis report, or a custom HTML template widget.

| Property                                                                    | Pattern | Type   | Deprecated | Definition | Title/Description                                                                                                   |
| --------------------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| - [label](#pages_items_sections_items_display_widgets_items_label )         | No      | string | No         | -          | Display label for the widget.                                                                                       |
| - [value](#pages_items_sections_items_display_widgets_items_value )         | No      | string | No         | -          | Dot-separated path into the report data, e.g. 'results.trivy.critical_count'.                                       |
| - [url](#pages_items_sections_items_display_widgets_items_url )             | No      | string | No         | -          | Optional URL for the widget. Supports Jinja2 templates.                                                             |
| - [icon](#pages_items_sections_items_display_widgets_items_icon )           | No      | string | No         | -          | Emoji or icon displayed alongside the widget.                                                                       |
| - [template](#pages_items_sections_items_display_widgets_items_template )   | No      | string | No         | -          | Path to a Jinja2 HTML template within the theme, e.g. analyzers/trivy/table.html.                                   |
| - [options](#pages_items_sections_items_display_widgets_items_options )     | No      | object | No         | -          | Arbitrary options passed directly to the Jinja2 template.                                                           |
| - [condition](#pages_items_sections_items_display_widgets_items_condition ) | No      | object | No         | -          | Optional jsonLogic expression to conditionally display this widget. If it evaluates to falsy, the widget is hidden. |

###### <a name="pages_items_sections_items_display_widgets_items_label"></a>5.1.3.1.3.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label for the widget.

###### <a name="pages_items_sections_items_display_widgets_items_value"></a>5.1.3.1.3.2.1.2. Property `value`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Dot-separated path into the report data, e.g. 'results.trivy.critical_count'.

###### <a name="pages_items_sections_items_display_widgets_items_url"></a>5.1.3.1.3.2.1.3. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Optional URL for the widget. Supports Jinja2 templates.

###### <a name="pages_items_sections_items_display_widgets_items_icon"></a>5.1.3.1.3.2.1.4. Property `icon`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Emoji or icon displayed alongside the widget.

###### <a name="pages_items_sections_items_display_widgets_items_template"></a>5.1.3.1.3.2.1.5. Property `template`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Path to a Jinja2 HTML template within the theme, e.g. analyzers/trivy/table.html.

###### <a name="pages_items_sections_items_display_widgets_items_options"></a>5.1.3.1.3.2.1.6. Property `options`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Arbitrary options passed directly to the Jinja2 template.

| Property                                                                            | Pattern | Type             | Deprecated | Definition | Title/Description                                                                                   |
| ----------------------------------------------------------------------------------- | ------- | ---------------- | ---------- | ---------- | --------------------------------------------------------------------------------------------------- |
| - [title](#pages_items_sections_items_display_widgets_items_options_title )         | No      | string           | No         | -          | Optional title for the widget. If provided, the widget will be displayed with a header.             |
| - [collapsed](#pages_items_sections_items_display_widgets_items_options_collapsed ) | No      | boolean          | No         | -          | If true, the widget will be collapsible and closed by default.                                      |
| - [align](#pages_items_sections_items_display_widgets_items_options_align )         | No      | enum (of string) | No         | -          | Text alignment for the widget (left, center, or right)                                              |
| - [subvalue](#pages_items_sections_items_display_widgets_items_options_subvalue )   | No      | string           | No         | -          | Additional text/value to display below the main value. Follows identical resolution logic as value. |
| - [class](#pages_items_sections_items_display_widgets_items_options_class )         | No      | string           | No         | -          | Additional CSS class(es) to apply to the widget container.                                          |

###### <a name="pages_items_sections_items_display_widgets_items_options_title"></a>5.1.3.1.3.2.1.6.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Optional title for the widget. If provided, the widget will be displayed with a header.

###### <a name="pages_items_sections_items_display_widgets_items_options_collapsed"></a>5.1.3.1.3.2.1.6.2. Property `collapsed`

|             |           |
| ----------- | --------- |
| **Type**    | `boolean` |
| **Default** | `false`   |

**Description:** If true, the widget will be collapsible and closed by default.

###### <a name="pages_items_sections_items_display_widgets_items_options_align"></a>5.1.3.1.3.2.1.6.3. Property `align`

|             |                    |
| ----------- | ------------------ |
| **Type**    | `enum (of string)` |
| **Default** | `"left"`           |

**Description:** Text alignment for the widget (left, center, or right)

Must be one of:
* "left"
* "center"
* "right"

###### <a name="pages_items_sections_items_display_widgets_items_options_subvalue"></a>5.1.3.1.3.2.1.6.4. Property `subvalue`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Additional text/value to display below the main value. Follows identical resolution logic as value.

###### <a name="pages_items_sections_items_display_widgets_items_options_class"></a>5.1.3.1.3.2.1.6.5. Property `class`

|             |          |
| ----------- | -------- |
| **Type**    | `string` |
| **Default** | `""`     |

**Description:** Additional CSS class(es) to apply to the widget container.

###### <a name="pages_items_sections_items_display_widgets_items_condition"></a>5.1.3.1.3.2.1.7. Property `condition`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional jsonLogic expression to conditionally display this widget. If it evaluates to falsy, the widget is hidden.

###### <a name="pages_items_sections_items_levels"></a>5.1.3.1.4. Property `levels`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** Priority/severity levels used to group scorecards. Built-in fallback order exists for bronze, silver, gold.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                   | Description                                                       |
| ------------------------------------------------- | ----------------------------------------------------------------- |
| [level](#pages_items_sections_items_levels_items) | A priority/severity level used to group and summarise scorecards. |

###### <a name="pages_items_sections_items_levels_items"></a>5.1.3.1.4.1. level

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/level                                                  |

**Description:** A priority/severity level used to group and summarise scorecards.

| Property                                                   | Pattern | Type    | Deprecated | Definition | Title/Description                                                                          |
| ---------------------------------------------------------- | ------- | ------- | ---------- | ---------- | ------------------------------------------------------------------------------------------ |
| + [name](#pages_items_sections_items_levels_items_name )   | No      | string  | No         | -          | Level identifier referenced by scorecards.                                                 |
| - [label](#pages_items_sections_items_levels_items_label ) | No      | string  | No         | -          | Human-readable display label.                                                              |
| - [order](#pages_items_sections_items_levels_items_order ) | No      | integer | No         | -          | Sort order (lower value = higher priority). Built-in defaults: bronze=1, silver=2, gold=3. |

###### <a name="pages_items_sections_items_levels_items_name"></a>5.1.3.1.4.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Level identifier referenced by scorecards.

###### <a name="pages_items_sections_items_levels_items_label"></a>5.1.3.1.4.1.2. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable display label.

###### <a name="pages_items_sections_items_levels_items_order"></a>5.1.3.1.4.1.3. Property `order`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Sort order (lower value = higher priority). Built-in defaults: bronze=1, silver=2, gold=3.

###### <a name="pages_items_sections_items_scorecards"></a>5.1.3.1.5. Property `scorecards`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** Evaluation scorecards with JsonLogic conditions.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                           | Description                                         |
| --------------------------------------------------------- | --------------------------------------------------- |
| [scorecard](#pages_items_sections_items_scorecards_items) | An evaluation scorecard with a JsonLogic condition. |

###### <a name="pages_items_sections_items_scorecards_items"></a>5.1.3.1.5.1. scorecard

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/scorecard                                              |

**Description:** An evaluation scorecard with a JsonLogic condition.

| Property                                                                   | Pattern | Type            | Deprecated | Definition | Title/Description                                                                                                                                                                                       |
| -------------------------------------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| + [name](#pages_items_sections_items_scorecards_items_name )               | No      | string          | No         | -          | Unique identifier for the scorecard.                                                                                                                                                                    |
| - [description](#pages_items_sections_items_scorecards_items_description ) | No      | string          | No         | -          | Human-readable description. Defaults to name if omitted.                                                                                                                                                |
| - [level](#pages_items_sections_items_scorecards_items_level )             | No      | string          | No         | -          | Level this scorecard belongs to. Must match a level name defined in the section.                                                                                                                        |
| - [tags](#pages_items_sections_items_scorecards_items_tags )               | No      | array of string | No         | -          | Arbitrary tags for filtering or grouping.                                                                                                                                                               |
| + [condition](#pages_items_sections_items_scorecards_items_condition )     | No      | object          | No         | -          | JsonLogic expression evaluated against the flattened analysis report. Variables use dot-paths, e.g. {"var": "results.trivy.critical_count"}. Supported operators: ==, !=, >, >=, <, <=, in, !, and, or. |

###### <a name="pages_items_sections_items_scorecards_items_name"></a>5.1.3.1.5.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the scorecard.

###### <a name="pages_items_sections_items_scorecards_items_description"></a>5.1.3.1.5.1.2. Property `description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Human-readable description. Defaults to name if omitted.

###### <a name="pages_items_sections_items_scorecards_items_level"></a>5.1.3.1.5.1.3. Property `level`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Level this scorecard belongs to. Must match a level name defined in the section.

###### <a name="pages_items_sections_items_scorecards_items_tags"></a>5.1.3.1.5.1.4. Property `tags`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Arbitrary tags for filtering or grouping.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                                       | Description |
| --------------------------------------------------------------------- | ----------- |
| [tags items](#pages_items_sections_items_scorecards_items_tags_items) | -           |

###### <a name="pages_items_sections_items_scorecards_items_tags_items"></a>5.1.3.1.5.1.4.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="pages_items_sections_items_scorecards_items_condition"></a>5.1.3.1.5.1.5. Property `condition`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** JsonLogic expression evaluated against the flattened analysis report. Variables use dot-paths, e.g. {"var": "results.trivy.critical_count"}. Supported operators: ==, !=, >, >=, <, <=, in, !, and, or.

###### <a name="pages_items_sections_items_widgets"></a>5.1.3.1.6. Property `widgets`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** KPI and Template widgets displayed in the section.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                     | Description                                                                                        |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| [widget](#pages_items_sections_items_widgets_items) | A key-value widget displaying a metric from the analysis report, or a custom HTML template widget. |

###### <a name="pages_items_sections_items_widgets_items"></a>5.1.3.1.6.1. widget

|                           |                                                                                                       |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                                              |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red)                                        |
| **Same definition as**    | [pages_items_sections_items_display_widgets_items](#pages_items_sections_items_display_widgets_items) |

**Description:** A key-value widget displaying a metric from the analysis report, or a custom HTML template widget.

###### <a name="pages_items_sections_items_condition"></a>5.1.3.1.7. Property `condition`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional jsonLogic expression to conditionally display this section. If it evaluates to falsy, the section is hidden.

## <a name="sections"></a>6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `sections`

|          |         |
| -------- | ------- |
| **Type** | `array` |

**Description:** Deprecated: List of playbook sections for the legacy renderer. Not used by the Docusaurus report viewer. Use `rules` instead.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | 1                  |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be | Description                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| [section](#sections_items)      | A playbook section containing scorecards, optional levels, and display preferences. |

### <a name="sections_items"></a>6.1. section

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Same definition as**    | [pages_items_sections_items](#pages_items_sections_items)      |

**Description:** A playbook section containing scorecards, optional levels, and display preferences.

## <a name="sidebar"></a>7. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `sidebar`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Deprecated: Sidebar navigation for the legacy Jinja2 renderer.

| Property                         | Pattern | Type            | Deprecated | Definition | Title/Description |
| -------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------- |
| - [sections](#sidebar_sections ) | No      | array of object | No         | -          | -                 |
| - [links](#sidebar_links )       | No      | array of object | No         | -          | -                 |

### <a name="sidebar_sections"></a>7.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `sections`

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

| Each item of this array must be           | Description |
| ----------------------------------------- | ----------- |
| [sections items](#sidebar_sections_items) | -           |

#### <a name="sidebar_sections_items"></a>7.1.1. sections items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                  | Pattern | Type            | Deprecated | Definition | Title/Description              |
| ----------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------ |
| - [title](#sidebar_sections_items_title ) | No      | string          | No         | -          | Title of the sidebar section.  |
| + [links](#sidebar_sections_items_links ) | No      | array of object | No         | -          | List of links in this section. |

##### <a name="sidebar_sections_items_title"></a>7.1.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Title of the sidebar section.

##### <a name="sidebar_sections_items_links"></a>7.1.1.2. Property `links`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of links in this section.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                    | Description |
| -------------------------------------------------- | ----------- |
| [links items](#sidebar_sections_items_links_items) | -           |

###### <a name="sidebar_sections_items_links_items"></a>7.1.1.2.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                              | Pattern | Type   | Deprecated | Definition | Title/Description   |
| ----------------------------------------------------- | ------- | ------ | ---------- | ---------- | ------------------- |
| + [label](#sidebar_sections_items_links_items_label ) | No      | string | No         | -          | Display label.      |
| + [url](#sidebar_sections_items_links_items_url )     | No      | string | No         | -          | Target URL.         |
| - [icon](#sidebar_sections_items_links_items_icon )   | No      | string | No         | -          | Icon name or emoji. |

###### <a name="sidebar_sections_items_links_items_label"></a>7.1.1.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label.

###### <a name="sidebar_sections_items_links_items_url"></a>7.1.1.2.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

###### <a name="sidebar_sections_items_links_items_icon"></a>7.1.1.2.1.3. Property `icon`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Icon name or emoji.

### <a name="sidebar_links"></a>7.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `links`

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

| Each item of this array must be     | Description |
| ----------------------------------- | ----------- |
| [links items](#sidebar_links_items) | -           |

#### <a name="sidebar_links_items"></a>7.2.1. links items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                               | Pattern | Type   | Deprecated | Definition | Title/Description   |
| -------------------------------------- | ------- | ------ | ---------- | ---------- | ------------------- |
| + [label](#sidebar_links_items_label ) | No      | string | No         | -          | Display label.      |
| + [url](#sidebar_links_items_url )     | No      | string | No         | -          | Target URL.         |
| - [icon](#sidebar_links_items_icon )   | No      | string | No         | -          | Icon name or emoji. |

##### <a name="sidebar_links_items_label"></a>7.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display label.

##### <a name="sidebar_links_items_url"></a>7.2.1.2. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Target URL.

##### <a name="sidebar_links_items_icon"></a>7.2.1.3. Property `icon`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Icon name or emoji.

## <a name="integrations"></a>8. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `integrations`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional third-party platform integrations (e.g. GitLab, GitHub).

| Property                          | Pattern | Type   | Deprecated | Definition | Title/Description |
| --------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [gitlab](#integrations_gitlab ) | No      | object | No         | -          | -                 |

### <a name="integrations_gitlab"></a>8.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `gitlab`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                         | Pattern | Type            | Deprecated | Definition | Title/Description                                                                           |
| ------------------------------------------------ | ------- | --------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------- |
| - [badges](#integrations_gitlab_badges )         | No      | array of string | No         | -          | List of badge slugs to be imported as GitLab Merge Request labels.                          |
| - [checklist](#integrations_gitlab_checklist )   | No      | array           | No         | -          | (Deprecated) Single checklist items added as checkboxes to the Merge Request description.   |
| - [checklists](#integrations_gitlab_checklists ) | No      | array of object | No         | -          | Configurable checklists added as checkboxes to the Merge Request description.               |
| - [templates](#integrations_gitlab_templates )   | No      | array of object | No         | -          | URLs to Cookiecutter templates that will be rendered and added to the Merge Request branch. |

#### <a name="integrations_gitlab_badges"></a>8.1.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

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

| Each item of this array must be                   | Description |
| ------------------------------------------------- | ----------- |
| [badges items](#integrations_gitlab_badges_items) | -           |

##### <a name="integrations_gitlab_badges_items"></a>8.1.1.1. badges items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="integrations_gitlab_checklist"></a>8.1.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checklist`

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

| Each item of this array must be                        | Description |
| ------------------------------------------------------ | ----------- |
| [checklist_item](#integrations_gitlab_checklist_items) | -           |

##### <a name="integrations_gitlab_checklist_items"></a>8.1.2.1. checklist_item

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |
| **Defined in**            | #/$defs/checklist_item                                         |

| Property                                                     | Pattern | Type   | Deprecated | Definition | Title/Description                                                                                                                                     |
| ------------------------------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| + [label](#integrations_gitlab_checklist_items_label )       | No      | string | No         | -          | Text of the checkbox item.                                                                                                                            |
| - [show_if](#integrations_gitlab_checklist_items_show_if )   | No      | object | No         | -          | Optional JsonLogic expression. If provided, the item is only included when the expression evaluates to truthy.                                        |
| - [check_if](#integrations_gitlab_checklist_items_check_if ) | No      | object | No         | -          | Optional JsonLogic expression. If provided and evaluates to truthy, the checkbox renders pre-checked (- [x]). Otherwise it renders unchecked (- [ ]). |

###### <a name="integrations_gitlab_checklist_items_label"></a>8.1.2.1.1. Property `label`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Text of the checkbox item.

###### <a name="integrations_gitlab_checklist_items_show_if"></a>8.1.2.1.2. Property `show_if`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional JsonLogic expression. If provided, the item is only included when the expression evaluates to truthy.

###### <a name="integrations_gitlab_checklist_items_check_if"></a>8.1.2.1.3. Property `check_if`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Optional JsonLogic expression. If provided and evaluates to truthy, the checkbox renders pre-checked (- [x]). Otherwise it renders unchecked (- [ ]).

#### <a name="integrations_gitlab_checklists"></a>8.1.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checklists`

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

| Each item of this array must be                           | Description |
| --------------------------------------------------------- | ----------- |
| [checklists items](#integrations_gitlab_checklists_items) | -           |

##### <a name="integrations_gitlab_checklists_items"></a>8.1.3.1. checklists items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                | Pattern | Type   | Deprecated | Definition | Title/Description                |
| ------------------------------------------------------- | ------- | ------ | ---------- | ---------- | -------------------------------- |
| - [title](#integrations_gitlab_checklists_items_title ) | No      | string | No         | -          | Display title for the checklist. |
| + [items](#integrations_gitlab_checklists_items_items ) | No      | array  | No         | -          | Items in this checklist.         |

###### <a name="integrations_gitlab_checklists_items_title"></a>8.1.3.1.1. Property `title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Display title for the checklist.

###### <a name="integrations_gitlab_checklists_items_items"></a>8.1.3.1.2. Property `items`

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

| Each item of this array must be                                     | Description |
| ------------------------------------------------------------------- | ----------- |
| [checklist_item](#integrations_gitlab_checklists_items_items_items) | -           |

###### <a name="integrations_gitlab_checklists_items_items_items"></a>8.1.3.1.2.1. checklist_item

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red)              |
| **Same definition as**    | [integrations_gitlab_checklist_items](#integrations_gitlab_checklist_items) |

#### <a name="integrations_gitlab_templates"></a>8.1.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `templates`

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

| Each item of this array must be                         | Description |
| ------------------------------------------------------- | ----------- |
| [templates items](#integrations_gitlab_templates_items) | -           |

##### <a name="integrations_gitlab_templates_items"></a>8.1.4.1. templates items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                                       | Pattern | Type                                           | Deprecated | Definition                                   | Title/Description                                                    |
| -------------------------------------------------------------- | ------- | ---------------------------------------------- | ---------- | -------------------------------------------- | -------------------------------------------------------------------- |
| + [url](#integrations_gitlab_templates_items_url )             | No      | string                                         | No         | -                                            | Cookiecutter template URL or path.                                   |
| - [directory](#integrations_gitlab_templates_items_directory ) | No      | string                                         | No         | -                                            | Optional subdirectory within the repository containing the template. |
| - [condition](#integrations_gitlab_templates_items_condition ) | No      | object, array, string, number, boolean or null | No         | Same as [condition](#links_items_condition ) | jsonlogic                                                            |

###### <a name="integrations_gitlab_templates_items_url"></a>8.1.4.1.1. Property `url`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Cookiecutter template URL or path.

###### <a name="integrations_gitlab_templates_items_directory"></a>8.1.4.1.2. Property `directory`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Optional subdirectory within the repository containing the template.

###### <a name="integrations_gitlab_templates_items_condition"></a>8.1.4.1.3. Property `condition`

**Title:** jsonlogic

|                        |                                                  |
| ---------------------- | ------------------------------------------------ |
| **Type**               | `object, array, string, number, boolean or null` |
| **Same definition as** | [condition](#links_items_condition)              |

**Description:** JSON Logic expression to conditionally render the template.

## <a name="rules"></a>9. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `rules`

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

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [rules items](#rules_items)     | -           |

### <a name="rules_items"></a>9.1. rules items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                             | Pattern | Type             | Deprecated | Definition | Title/Description                                   |
| ------------------------------------ | ------- | ---------------- | ---------- | ---------- | --------------------------------------------------- |
| - [slug](#rules_items_slug )         | No      | string           | No         | -          | Unique identifier for the rule instance.            |
| - [provider](#rules_items_provider ) | No      | string           | No         | -          | Analyzer name (e.g. 'trivy').                       |
| - [rule](#rules_items_rule )         | No      | string           | No         | -          | Template name within the provider (e.g. 'cve-max'). |
| - [options](#rules_items_options )   | No      | object           | No         | -          | Configuration parameters for the rule template.     |
| - [enable](#rules_items_enable )     | No      | boolean          | No         | -          | Whether to enable this rule.                        |
| - [level](#rules_items_level )       | No      | enum (of string) | No         | -          | Severity level of the rule.                         |
| - [tags](#rules_items_tags )         | No      | array of string  | No         | -          | Arbitrary tags.                                     |
| - [messages](#rules_items_messages ) | No      | object           | No         | -          | -                                                   |

#### <a name="rules_items_slug"></a>9.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the rule instance.

#### <a name="rules_items_provider"></a>9.1.2. Property `provider`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Analyzer name (e.g. 'trivy').

#### <a name="rules_items_rule"></a>9.1.3. Property `rule`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Template name within the provider (e.g. 'cve-max').

#### <a name="rules_items_options"></a>9.1.4. Property `options`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Configuration parameters for the rule template.

| Property                                         | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------------------ | ------- | ------ | ---------- | ---------- | ----------------- |
| - [](#rules_items_options_additionalProperties ) | No      | object | No         | -          | -                 |

#### <a name="rules_items_enable"></a>9.1.5. Property `enable`

|             |           |
| ----------- | --------- |
| **Type**    | `boolean` |
| **Default** | `true`    |

**Description:** Whether to enable this rule.

#### <a name="rules_items_level"></a>9.1.6. Property `level`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** Severity level of the rule.

Must be one of:
* "info"
* "warning"
* "critical"
* "none"

#### <a name="rules_items_tags"></a>9.1.7. Property `tags`

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

| Each item of this array must be       | Description |
| ------------------------------------- | ----------- |
| [tags items](#rules_items_tags_items) | -           |

##### <a name="rules_items_tags_items"></a>9.1.7.1. tags items

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="rules_items_messages"></a>9.1.8. Property `messages`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                              | Pattern | Type   | Deprecated | Definition | Title/Description |
| ------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [pass](#rules_items_messages_pass ) | No      | string | No         | -          | -                 |
| - [fail](#rules_items_messages_fail ) | No      | string | No         | -          | -                 |

##### <a name="rules_items_messages_pass"></a>9.1.8.1. Property `pass`

|          |          |
| -------- | -------- |
| **Type** | `string` |

##### <a name="rules_items_messages_fail"></a>9.1.8.2. Property `fail`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="tiers"></a>10. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `tiers`

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

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [tiers items](#tiers_items)     | -           |

### <a name="tiers_items"></a>10.1. tiers items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                               | Pattern | Type                                           | Deprecated | Definition                                   | Title/Description                      |
| -------------------------------------- | ------- | ---------------------------------------------- | ---------- | -------------------------------------------- | -------------------------------------- |
| + [name](#tiers_items_name )           | No      | string                                         | No         | -                                            | Tier name (e.g. Gold, Silver, Bronze). |
| + [condition](#tiers_items_condition ) | No      | object, array, string, number, boolean or null | No         | Same as [condition](#links_items_condition ) | jsonlogic                              |

#### <a name="tiers_items_name"></a>10.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Tier name (e.g. Gold, Silver, Bronze).

#### <a name="tiers_items_condition"></a>10.1.2. Property `condition`

**Title:** jsonlogic

|                        |                                                  |
| ---------------------- | ------------------------------------------------ |
| **Type**               | `object, array, string, number, boolean or null` |
| **Same definition as** | [condition](#links_items_condition)              |

**Description:** JsonLogic expression evaluated against the report context.

## <a name="badges"></a>11. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `badges`

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

| Each item of this array must be | Description |
| ------------------------------- | ----------- |
| [badges items](#badges_items)   | -           |

### <a name="badges_items"></a>11.1. badges items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                | Pattern | Type                                           | Deprecated | Definition                                   | Title/Description                                                             |
| --------------------------------------- | ------- | ---------------------------------------------- | ---------- | -------------------------------------------- | ----------------------------------------------------------------------------- |
| + [slug](#badges_items_slug )           | No      | string                                         | No         | -                                            | Unique identifier for the badge.                                              |
| + [scope](#badges_items_scope )         | No      | string                                         | No         | -                                            | Category label displayed on the left part of the badge (e.g. CVE, Freshness). |
| + [value](#badges_items_value )         | No      | string                                         | No         | -                                            | Value displayed on the right part of the badge.                               |
| + [condition](#badges_items_condition ) | No      | object, array, string, number, boolean or null | No         | Same as [condition](#links_items_condition ) | jsonlogic                                                                     |
| + [class](#badges_items_class )         | No      | enum (of string)                               | No         | -                                            | Visual style class for the badge.                                             |

#### <a name="badges_items_slug"></a>11.1.1. Property `slug`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier for the badge.

#### <a name="badges_items_scope"></a>11.1.2. Property `scope`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Category label displayed on the left part of the badge (e.g. CVE, Freshness).

#### <a name="badges_items_value"></a>11.1.3. Property `value`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Value displayed on the right part of the badge.

#### <a name="badges_items_condition"></a>11.1.4. Property `condition`

**Title:** jsonlogic

|                        |                                                  |
| ---------------------- | ------------------------------------------------ |
| **Type**               | `object, array, string, number, boolean or null` |
| **Same definition as** | [condition](#links_items_condition)              |

**Description:** JsonLogic expression. The badge is shown when this evaluates to truthy.

#### <a name="badges_items_class"></a>11.1.5. Property `class`

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
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-10 at 12:50:09 +0000
