# secrets.output

**Title:** secrets.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Secret detection results from TruffleHog.

| Property                               | Pattern | Type            | Deprecated | Definition | Title/Description                                |
| -------------------------------------- | ------- | --------------- | ---------- | ---------- | ------------------------------------------------ |
| + [analyzer](#analyzer )               | No      | const           | No         | -          | -                                                |
| + [repository](#repository )           | No      | string          | No         | -          | -                                                |
| + [tag](#tag )                         | No      | string          | No         | -          | -                                                |
| + [scanner_version](#scanner_version ) | No      | string          | No         | -          | -                                                |
| + [secrets_count](#secrets_count )     | No      | integer         | No         | -          | -                                                |
| + [verified_count](#verified_count )   | No      | integer         | No         | -          | Secrets TruffleHog verified as live credentials. |
| + [findings](#findings )               | No      | array of object | No         | -          | -                                                |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

Specific value: `"secrets"`

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

## <a name="secrets_count"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `secrets_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="verified_count"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `verified_count`

|          |           |
| -------- | --------- |
| **Type** | `integer` |

**Description:** Secrets TruffleHog verified as live credentials.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="findings"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `findings`

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

| Each item of this array must be   | Description |
| --------------------------------- | ----------- |
| [findings items](#findings_items) | -           |

### <a name="findings_items"></a>7.1. findings items

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                                        | Pattern | Type    | Deprecated | Definition | Title/Description |
| ----------------------------------------------- | ------- | ------- | ---------- | ---------- | ----------------- |
| + [DetectorName](#findings_items_DetectorName ) | No      | string  | No         | -          | -                 |
| + [Verified](#findings_items_Verified )         | No      | boolean | No         | -          | -                 |
| - [Redacted](#findings_items_Redacted )         | No      | string  | No         | -          | -                 |
| - [layer](#findings_items_layer )               | No      | string  | No         | -          | -                 |

#### <a name="findings_items_DetectorName"></a>7.1.1. Property `DetectorName`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="findings_items_Verified"></a>7.1.2. Property `Verified`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

#### <a name="findings_items_Redacted"></a>7.1.3. Property `Redacted`

|          |          |
| -------- | -------- |
| **Type** | `string` |

#### <a name="findings_items_layer"></a>7.1.4. Property `layer`

|          |          |
| -------- | -------- |
| **Type** | `string` |

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-06-06 at 19:49:31 +0200
