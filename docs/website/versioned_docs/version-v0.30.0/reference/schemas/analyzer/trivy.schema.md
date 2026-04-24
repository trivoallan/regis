# trivy.output

**Title:** trivy.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Vulnerability scan results from Trivy.

| Property                                       | Pattern | Type            | Deprecated | Definition | Title/Description                                     |
| ---------------------------------------------- | ------- | --------------- | ---------- | ---------- | ----------------------------------------------------- |
| + [analyzer](#analyzer )                       | No      | const           | No         | -          | Unique identifier for the Trivy analyzer.             |
| + [repository](#repository )                   | No      | string          | No         | -          | The image repository that was analyzed.               |
| + [tag](#tag )                                 | No      | string          | No         | -          | The image tag that was analyzed.                      |
| + [trivy_version](#trivy_version )             | No      | string          | No         | -          | Version of the Trivy CLI tool used.                   |
| + [vulnerability_count](#vulnerability_count ) | No      | integer         | No         | -          | Total number of vulnerabilities found.                |
| + [critical_count](#critical_count )           | No      | integer         | No         | -          | Total number of Critical severity vulnerabilities.    |
| + [high_count](#high_count )                   | No      | integer         | No         | -          | Total number of High severity vulnerabilities.        |
| + [medium_count](#medium_count )               | No      | integer         | No         | -          | Total number of Medium severity vulnerabilities.      |
| + [low_count](#low_count )                     | No      | integer         | No         | -          | Total number of Low severity vulnerabilities.         |
| + [unknown_count](#unknown_count )             | No      | integer         | No         | -          | Total number of Unknown severity vulnerabilities.     |
| + [fixed_count](#fixed_count )                 | No      | integer         | No         | -          | Total number of vulnerabilities with available fixes. |
| + [secrets_count](#secrets_count )             | No      | integer         | No         | -          | Total number of secrets or credentials found.         |
| + [targets](#targets )                         | No      | array of object | No         | -          | -                                                     |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Trivy analyzer.

Specific value: `"trivy"`

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

## <a name="trivy_version"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `trivy_version`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Version of the Trivy CLI tool used.

## <a name="vulnerability_count"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `vulnerability_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of vulnerabilities found.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="critical_count"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `critical_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of Critical severity vulnerabilities.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="high_count"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `high_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of High severity vulnerabilities.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="medium_count"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `medium_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of Medium severity vulnerabilities.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="low_count"></a>9. ![Required](https://img.shields.io/badge/Required-blue) Property `low_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of Low severity vulnerabilities.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="unknown_count"></a>10. ![Required](https://img.shields.io/badge/Required-blue) Property `unknown_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of Unknown severity vulnerabilities.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="fixed_count"></a>11. ![Required](https://img.shields.io/badge/Required-blue) Property `fixed_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of vulnerabilities with available fixes.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="secrets_count"></a>12. ![Required](https://img.shields.io/badge/Required-blue) Property `secrets_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Total number of secrets or credentials found.

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

| Property                                             | Pattern | Type                    | Deprecated | Definition | Title/Description                                            |
| ---------------------------------------------------- | ------- | ----------------------- | ---------- | ---------- | ------------------------------------------------------------ |
| - [Secrets](#targets_items_Secrets )                 | No      | array of object or null | No         | -          | List of secrets discovered in this target.                   |
| + [Target](#targets_items_Target )                   | No      | string                  | No         | -          | The scan target (e.g., a file path or OS distribution name). |
| + [Vulnerabilities](#targets_items_Vulnerabilities ) | No      | array of object or null | No         | -          | List of vulnerabilities discovered in this target.           |

#### <a name="targets_items_Secrets"></a>13.1.1. Property `Secrets`

|          |                           |
| -------- | ------------------------- |
| **Type** | `array of object or null` |

**Description:** List of secrets discovered in this target.

|                      | Array restrictions |
| -------------------- | ------------------ |
| **Min items**        | N/A                |
| **Max items**        | N/A                |
| **Items unicity**    | False              |
| **Additional items** | False              |
| **Tuple validation** | See below          |

| Each item of this array must be               | Description |
| --------------------------------------------- | ----------- |
| [Secrets items](#targets_items_Secrets_items) | -           |

##### <a name="targets_items_Secrets_items"></a>13.1.1.1. Secrets items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                             | Pattern | Type   | Deprecated | Definition | Title/Description |
| ---------------------------------------------------- | ------- | ------ | ---------- | ---------- | ----------------- |
| + [RuleID](#targets_items_Secrets_items_RuleID )     | No      | string | No         | -          | -                 |
| + [Title](#targets_items_Secrets_items_Title )       | No      | string | No         | -          | -                 |
| + [Severity](#targets_items_Secrets_items_Severity ) | No      | string | No         | -          | -                 |
| + [Match](#targets_items_Secrets_items_Match )       | No      | string | No         | -          | -                 |

###### <a name="targets_items_Secrets_items_RuleID"></a>13.1.1.1.1. Property `RuleID`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Secrets_items_Title"></a>13.1.1.1.2. Property `Title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Secrets_items_Severity"></a>13.1.1.1.3. Property `Severity`

|          |          |
| -------- | -------- |
| **Type** | `string` |

###### <a name="targets_items_Secrets_items_Match"></a>13.1.1.1.4. Property `Match`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="targets_items_Target"></a>13.1.2. Property `Target`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The scan target (e.g., a file path or OS distribution name).

#### <a name="targets_items_Vulnerabilities"></a>13.1.3. Property `Vulnerabilities`

|          |                           |
| -------- | ------------------------- |
| **Type** | `array of object or null` |

**Description:** List of vulnerabilities discovered in this target.

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

##### <a name="targets_items_Vulnerabilities_items"></a>13.1.3.1. Vulnerabilities items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                                                     | Pattern | Type   | Deprecated | Definition | Title/Description                                         |
| ---------------------------------------------------------------------------- | ------- | ------ | ---------- | ---------- | --------------------------------------------------------- |
| + [VulnerabilityID](#targets_items_Vulnerabilities_items_VulnerabilityID )   | No      | string | No         | -          | CVE ID or tool-specific vulnerability identifier.         |
| + [PkgName](#targets_items_Vulnerabilities_items_PkgName )                   | No      | string | No         | -          | Name of the affected package.                             |
| + [InstalledVersion](#targets_items_Vulnerabilities_items_InstalledVersion ) | No      | string | No         | -          | Version of the package installed in the image.            |
| - [FixedVersion](#targets_items_Vulnerabilities_items_FixedVersion )         | No      | string | No         | -          | Version of the package that contains a fix, if available. |
| + [Severity](#targets_items_Vulnerabilities_items_Severity )                 | No      | string | No         | -          | Severity level assigned by Trivy.                         |
| - [Title](#targets_items_Vulnerabilities_items_Title )                       | No      | string | No         | -          | Short title describing the vulnerability.                 |
| - [Description](#targets_items_Vulnerabilities_items_Description )           | No      | string | No         | -          | Full description of the vulnerability.                    |

###### <a name="targets_items_Vulnerabilities_items_VulnerabilityID"></a>13.1.3.1.1. Property `VulnerabilityID`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** CVE ID or tool-specific vulnerability identifier.

###### <a name="targets_items_Vulnerabilities_items_PkgName"></a>13.1.3.1.2. Property `PkgName`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Name of the affected package.

###### <a name="targets_items_Vulnerabilities_items_InstalledVersion"></a>13.1.3.1.3. Property `InstalledVersion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Version of the package installed in the image.

###### <a name="targets_items_Vulnerabilities_items_FixedVersion"></a>13.1.3.1.4. Property `FixedVersion`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Version of the package that contains a fix, if available.

###### <a name="targets_items_Vulnerabilities_items_Severity"></a>13.1.3.1.5. Property `Severity`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Severity level assigned by Trivy.

###### <a name="targets_items_Vulnerabilities_items_Title"></a>13.1.3.1.6. Property `Title`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Short title describing the vulnerability.

###### <a name="targets_items_Vulnerabilities_items_Description"></a>13.1.3.1.7. Property `Description`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Full description of the vulnerability.

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-22 at 20:05:38 +0000
