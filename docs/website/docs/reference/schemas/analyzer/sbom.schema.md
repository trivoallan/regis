# sbom.output

**Title:** sbom.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Software Bill of Materials extracted from a container image using Trivy (CycloneDX).

| Property                                     | Pattern | Type            | Deprecated | Definition | Title/Description                                                                    |
| -------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------------------------------------------ |
| + [analyzer](#analyzer )                     | No      | const           | No         | -          | Unique identifier for the SBOM analyzer.                                             |
| + [repository](#repository )                 | No      | string          | No         | -          | The image repository that was analyzed.                                              |
| + [tag](#tag )                               | No      | string          | No         | -          | The image tag that was analyzed.                                                     |
| + [has_sbom](#has_sbom )                     | No      | boolean         | No         | -          | True if an SBOM was successfully generated.                                          |
| + [sbom_format](#sbom_format )               | No      | string          | No         | -          | The format of the generated SBOM (e.g., CycloneDX).                                  |
| + [sbom_version](#sbom_version )             | No      | string          | No         | -          | Version of the SBOM specification used.                                              |
| + [total_components](#total_components )     | No      | integer         | No         | -          | Total number of software components found (OS packages, apps, etc.).                 |
| + [component_types](#component_types )       | No      | object          | No         | -          | Count of components grouped by type (library, application, framework, …).            |
| + [total_dependencies](#total_dependencies ) | No      | integer         | No         | -          | Total number of dependency relationships found.                                      |
| + [licenses](#licenses )                     | No      | array of string | No         | -          | Sorted unique license identifiers found across all components.                       |
| + [copyleft_licenses](#copyleft_licenses )   | No      | array of string | No         | -          | Sorted subset of licenses that are known copyleft (GPL, LGPL, AGPL, MPL, EPL, etc.). |
| + [components](#components )                 | No      | array of object | No         | -          | List of software components identified in the image.                                 |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the SBOM analyzer.

Specific value: `"sbom"`

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

## <a name="has_sbom"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `has_sbom`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if an SBOM was successfully generated.

## <a name="sbom_format"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `sbom_format`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The format of the generated SBOM (e.g., CycloneDX).

## <a name="sbom_version"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `sbom_version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Version of the SBOM specification used.

## <a name="total_components"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `total_components`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of software components found (OS packages, apps, etc.).

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="component_types"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `component_types`

|                           |                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Type**                  | `object`                                                                                                     |
| **Additional properties** | [![Should-conform](https://img.shields.io/badge/Should-conform-blue)](#component_types_additionalProperties) |

**Description:** Count of components grouped by type (library, application, framework, …).

| Property                                     | Pattern | Type    | Deprecated | Definition | Title/Description |
| -------------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| - [](#component_types_additionalProperties ) | No      | integer | No         | -          | -                 |

### <a name="component_types_additionalProperties"></a>8.1. Property `additionalProperties`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="total_dependencies"></a>9. ![Required](https://img.shields.io/badge/Required-blue) Property `total_dependencies`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of dependency relationships found.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="licenses"></a>10. ![Required](https://img.shields.io/badge/Required-blue) Property `licenses`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Sorted unique license identifiers found across all components.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be   | Description |
| --------------------------------- | ----------- |
| [licenses items](#licenses_items) | -           |

### <a name="licenses_items"></a>10.1. licenses items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="copyleft_licenses"></a>11. ![Required](https://img.shields.io/badge/Required-blue) Property `copyleft_licenses`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** Sorted subset of licenses that are known copyleft (GPL, LGPL, AGPL, MPL, EPL, etc.).

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                     | Description |
| --------------------------------------------------- | ----------- |
| [copyleft_licenses items](#copyleft_licenses_items) | -           |

### <a name="copyleft_licenses_items"></a>11.1. copyleft_licenses items

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="components"></a>12. ![Required](https://img.shields.io/badge/Required-blue) Property `components`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of object` |

**Description:** List of software components identified in the image.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be       | Description |
| ------------------------------------- | ----------- |
| [components items](#components_items) | -           |

### <a name="components_items"></a>12.1. components items

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                                  | Pattern | Type            | Deprecated | Definition | Title/Description                                |
| ----------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------ |
| + [name](#components_items_name )         | No      | string          | No         | -          | Name of the component.                           |
| - [version](#components_items_version )   | No      | string or null  | No         | -          | Installed version of the component.              |
| + [type](#components_items_type )         | No      | string          | No         | -          | Type of component (library, application, etc.).  |
| - [purl](#components_items_purl )         | No      | string or null  | No         | -          | Package URL (purl) for standard identification.  |
| - [licenses](#components_items_licenses ) | No      | array of string | No         | -          | List of licenses associated with this component. |

#### <a name="components_items_name"></a>12.1.1. Property `name`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Name of the component.

#### <a name="components_items_version"></a>12.1.2. Property `version`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Installed version of the component.

#### <a name="components_items_type"></a>12.1.3. Property `type`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Type of component (library, application, etc.).

#### <a name="components_items_purl"></a>12.1.4. Property `purl`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Package URL (purl) for standard identification.

#### <a name="components_items_licenses"></a>12.1.5. Property `licenses`

|          |                   |
| -------- | ----------------- |
| **Type** | `array of string` |

**Description:** List of licenses associated with this component.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                    | Description |
| -------------------------------------------------- | ----------- |
| [licenses items](#components_items_licenses_items) | -           |

##### <a name="components_items_licenses_items"></a>12.1.5.1. licenses items

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-10 at 16:12:31 +0000
