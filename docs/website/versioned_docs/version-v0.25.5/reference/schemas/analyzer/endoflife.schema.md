# endoflife.output

**Title:** endoflife.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Report containing lifecycle information from endoflife.date.

| Property                                      | Pattern | Type            | Deprecated | Definition | Title/Description                                                    |
| --------------------------------------------- | ------- | --------------- | ---------- | ---------- | -------------------------------------------------------------------- |
| + [analyzer](#analyzer)                       | No      | const           | No         | -          | Unique identifier for the EndOfLife analyzer.                        |
| + [repository](#repository)                   | No      | string          | No         | -          | The image repository that was analyzed.                              |
| + [product](#product)                         | No      | string          | No         | -          | Product slug used to query endoflife.date.                           |
| + [product_found](#product_found)             | No      | boolean         | No         | -          | Whether the product was found on endoflife.date.                     |
| + [tag](#tag)                                 | No      | string          | No         | -          | Image tag that was analyzed.                                         |
| + [matched_cycle](#matched_cycle)             | No      | object or null  | No         | -          | Release cycle matching the image tag, or null if no match.           |
| + [is_eol](#is_eol)                           | No      | boolean or null | No         | -          | Whether the matched cycle has reached end-of-life. Null if no match. |
| + [active_cycles_count](#active_cycles_count) | No      | integer or null | No         | -          | Number of currently supported release cycles.                        |
| + [eol_cycles_count](#eol_cycles_count)       | No      | integer or null | No         | -          | Number of end-of-life release cycles.                                |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the EndOfLife analyzer.

Specific value: `"endoflife"`

## <a name="repository"></a>2. ![Required](https://img.shields.io/badge/Required-blue) Property `repository`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** The image repository that was analyzed.

## <a name="product"></a>3. ![Required](https://img.shields.io/badge/Required-blue) Property `product`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Product slug used to query endoflife.date.

## <a name="product_found"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `product_found`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether the product was found on endoflife.date.

## <a name="tag"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `tag`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Image tag that was analyzed.

## <a name="matched_cycle"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `matched_cycle`

|          |                  |
| -------- | ---------------- |
| **Type** | `object or null` |

**Description:** Release cycle matching the image tag, or null if no match.

| Property                                                    | Pattern | Type              | Deprecated | Definition | Title/Description                                 |
| ----------------------------------------------------------- | ------- | ----------------- | ---------- | ---------- | ------------------------------------------------- |
| - [cycle](#matched_cycle_cycle)                             | No      | string            | No         | -          | Release cycle identifier (e.g., '22.04').         |
| - [release_date](#matched_cycle_release_date)               | No      | string or null    | No         | -          | Official release date of the cycle.               |
| - [eol](#matched_cycle_eol)                                 | No      | string or boolean | No         | -          | End-of-life date or status for this cycle.        |
| - [latest](#matched_cycle_latest)                           | No      | string or null    | No         | -          | Latest version available in this cycle.           |
| - [latest_release_date](#matched_cycle_latest_release_date) | No      | string or null    | No         | -          | Release date of the latest version in this cycle. |
| - [lts](#matched_cycle_lts)                                 | No      | boolean           | No         | -          | Whether this is a Long Term Support cycle.        |

### <a name="matched_cycle_cycle"></a>6.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `cycle`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Release cycle identifier (e.g., '22.04').

### <a name="matched_cycle_release_date"></a>6.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `release_date`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Official release date of the cycle.

### <a name="matched_cycle_eol"></a>6.3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `eol`

|          |                     |
| -------- | ------------------- |
| **Type** | `string or boolean` |

**Description:** End-of-life date or status for this cycle.

### <a name="matched_cycle_latest"></a>6.4. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `latest`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Latest version available in this cycle.

### <a name="matched_cycle_latest_release_date"></a>6.5. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `latest_release_date`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** Release date of the latest version in this cycle.

### <a name="matched_cycle_lts"></a>6.6. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `lts`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** Whether this is a Long Term Support cycle.

## <a name="is_eol"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `is_eol`

|          |                   |
| -------- | ----------------- |
| **Type** | `boolean or null` |

**Description:** Whether the matched cycle has reached end-of-life. Null if no match.

## <a name="active_cycles_count"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `active_cycles_count`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Number of currently supported release cycles.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="eol_cycles_count"></a>9. ![Required](https://img.shields.io/badge/Required-blue) Property `eol_cycles_count`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Number of end-of-life release cycles.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

---

Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-03-31 at 07:14:29 +0000
