# cve.output

**Title:** cve.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Vulnerability scan results from Grype.

| Property                                       | Pattern | Type            | Deprecated | Definition | Title/Description              |
| ---------------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------ |
| + [analyzer](#analyzer )                       | No      | const           | No         | -          | -                              |
| + [repository](#repository )                   | No      | string          | No         | -          | -                              |
| + [tag](#tag )                                 | No      | string          | No         | -          | -                              |
| + [scanner_version](#scanner_version )         | No      | string          | No         | -          | Version of the grype CLI used. |
| + [vulnerability_count](#vulnerability_count ) | No      | integer         | No         | -          | -                              |
| + [critical_count](#critical_count )           | No      | integer         | No         | -          | -                              |
| + [high_count](#high_count )                   | No      | integer         | No         | -          | -                              |
| + [medium_count](#medium_count )               | No      | integer         | No         | -          | -                              |
| + [low_count](#low_count )                     | No      | integer         | No         | -          | -                              |
| + [negligible_count](#negligible_count )       | No      | integer         | No         | -          | -                              |
| + [unknown_count](#unknown_count )             | No      | integer         | No         | -          | -                              |
| + [fixed_count](#fixed_count )                 | No      | integer         | No         | -          | -                              |
| + [targets](#targets )                         | No      | array of object | No         | -          | -                              |
| - [source](#source )                           | No      | object          | No         | -          | -                              |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

Specific value: `"cve"`

## <a name="repository"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="tag"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `tag`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="scanner_version"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `scanner_version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Version of the grype CLI used.

## <a name="vulnerability_count"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `vulnerability_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="critical_count"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `critical_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="high_count"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `high_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="medium_count"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `medium_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="low_count"></a>9. ![Required](https://img.shields.io/badge/Required-blue) Property `low_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="negligible_count"></a>10. ![Required](https://img.shields.io/badge/Required-blue) Property `negligible_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="unknown_count"></a>11. ![Required](https://img.shields.io/badge/Required-blue) Property `unknown_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="fixed_count"></a>12. ![Required](https://img.shields.io/badge/Required-blue) Property `fixed_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="targets"></a>13. ![Required](https://img.shields.io/badge/Required-blue) Property `targets`

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
| [targets items](#targets_items) | -           |

### <a name="targets_items"></a>13.1. targets items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                             | Pattern | Type                    | Deprecated | Definition | Title/Description                    |
| ---------------------------------------------------- | ------- | ----------------------- | ---------- | ---------- | ------------------------------------ |
| + [Target](#targets_items_Target )                   | No      | string                  | No         | -          | Artifact type (apk, deb, python, …). |
| + [Vulnerabilities](#targets_items_Vulnerabilities ) | No      | array of object or null | No         | -          | -                                    |

#### <a name="targets_items_Target"></a>13.1.1. Property `Target`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Artifact type (apk, deb, python, …).

#### <a name="targets_items_Vulnerabilities"></a>13.1.2. Property `Vulnerabilities`

|          |                           |
| -------- | ------------------------- |
| **Type** | `array of object or null` |

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be                               | Description |
| ------------------------------------------------------------- | ----------- |
| [Vulnerabilities items](#targets_items_Vulnerabilities_items) | -           |

##### <a name="targets_items_Vulnerabilities_items"></a>13.1.2.1. Vulnerabilities items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                     | Pattern | Type   | Deprecated | Definition | Title/Description |
| ---------------------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| + [VulnerabilityID](#targets_items_Vulnerabilities_items_VulnerabilityID )   | No      | string | No         | -          | -                 |
| + [PkgName](#targets_items_Vulnerabilities_items_PkgName )                   | No      | string | No         | -          | -                 |
| + [InstalledVersion](#targets_items_Vulnerabilities_items_InstalledVersion ) | No      | string | No         | -          | -                 |
| - [FixedVersion](#targets_items_Vulnerabilities_items_FixedVersion )         | No      | string | No         | -          | -                 |
| + [Severity](#targets_items_Vulnerabilities_items_Severity )                 | No      | string | No         | -          | -                 |
| - [Title](#targets_items_Vulnerabilities_items_Title )                       | No      | string | No         | -          | -                 |
| - [Description](#targets_items_Vulnerabilities_items_Description )           | No      | string | No         | -          | -                 |

###### <a name="targets_items_Vulnerabilities_items_VulnerabilityID"></a>13.1.2.1.1. Property `VulnerabilityID`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Vulnerabilities_items_PkgName"></a>13.1.2.1.2. Property `PkgName`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Vulnerabilities_items_InstalledVersion"></a>13.1.2.1.3. Property `InstalledVersion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Vulnerabilities_items_FixedVersion"></a>13.1.2.1.4. Property `FixedVersion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Vulnerabilities_items_Severity"></a>13.1.2.1.5. Property `Severity`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Vulnerabilities_items_Title"></a>13.1.2.1.6. Property `Title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Vulnerabilities_items_Description"></a>13.1.2.1.7. Property `Description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

## <a name="source"></a>14. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `source`

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

| Property                            | Pattern | Type   | Deprecated | Definition | Title/Description |
| ----------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| - [fetched_at](#source_fetched_at ) | No      | string | No         | -          | -                 |
| - [built_at](#source_built_at )     | No      | string | No         | -          | -                 |
| - [version](#source_version )       | No      | string | No         | -          | -                 |
| - [checksum](#source_checksum )     | No      | string | No         | -          | -                 |

### <a name="source_fetched_at"></a>14.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `fetched_at`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

### <a name="source_built_at"></a>14.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `built_at`

|            |             |
| ---------- | ----------- |
| **Type**   | `string`    |
| **Format** | `date-time` |

### <a name="source_version"></a>14.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

### <a name="source_checksum"></a>14.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `checksum`

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-06-22 at 01:48:28 +0000
