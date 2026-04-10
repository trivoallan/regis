# freshness.output

**Title:** freshness.output

|                           |                                                                |
| ------------------------- | -------------------------------------------------------------- |
| **Type**                  | `object`                                                       |
| **Additional properties** | ![Not allowed](https://img.shields.io/badge/Not%20allowed-red) |

**Description:** Image age and delta versus latest tag.

| Property                                     | Pattern | Type            | Deprecated | Definition | Title/Description                                                      |
| -------------------------------------------- | ------- | --------------- | ---------- | ---------- | ---------------------------------------------------------------------- |
| + [analyzer](#analyzer )                     | No      | const           | No         | -          | Unique identifier for the Freshness analyzer.                          |
| + [repository](#repository )                 | No      | string          | No         | -          | The image repository that was analyzed.                                |
| + [tag](#tag )                               | No      | string          | No         | -          | The image tag that was analyzed.                                       |
| + [tag_created](#tag_created )               | No      | string or null  | No         | -          | ISO timestamp of when the current tag was created.                     |
| + [latest_created](#latest_created )         | No      | string or null  | No         | -          | ISO timestamp of when the 'latest' tag was created.                    |
| + [age_days](#age_days )                     | No      | integer or null | No         | -          | Number of days since the current tag was created.                      |
| + [behind_latest_days](#behind_latest_days ) | No      | integer or null | No         | -          | Number of days between the creation of this tag and the 'latest' tag.  |
| + [is_latest](#is_latest )                   | No      | boolean         | No         | -          | True if the current tag points to the same digest as the 'latest' tag. |

## <a name="analyzer"></a>1. ![Required](https://img.shields.io/badge/Required-blue) Property `analyzer`

|          |         |
| -------- | ------- |
| **Type** | `const` |

**Description:** Unique identifier for the Freshness analyzer.

Specific value: `"freshness"`

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

## <a name="tag_created"></a>4. ![Required](https://img.shields.io/badge/Required-blue) Property `tag_created`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** ISO timestamp of when the current tag was created.

## <a name="latest_created"></a>5. ![Required](https://img.shields.io/badge/Required-blue) Property `latest_created`

|          |                  |
| -------- | ---------------- |
| **Type** | `string or null` |

**Description:** ISO timestamp of when the 'latest' tag was created.

## <a name="age_days"></a>6. ![Required](https://img.shields.io/badge/Required-blue) Property `age_days`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Number of days since the current tag was created.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="behind_latest_days"></a>7. ![Required](https://img.shields.io/badge/Required-blue) Property `behind_latest_days`

|          |                   |
| -------- | ----------------- |
| **Type** | `integer or null` |

**Description:** Number of days between the creation of this tag and the 'latest' tag.

| Restrictions |        |
| ------------ | ------ |
| **Minimum**  | &ge; 0 |

## <a name="is_latest"></a>8. ![Required](https://img.shields.io/badge/Required-blue) Property `is_latest`

|          |           |
| -------- | --------- |
| **Type** | `boolean` |

**Description:** True if the current tag points to the same digest as the 'latest' tag.

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-10 at 15:10:32 +0000
