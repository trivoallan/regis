# Regis Well-Known Metadata

**Title:** Regis Well-Known Metadata

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Standard metadata fields recognized by regis across all playbooks.

| Property                      | Pattern | Type             | Deprecated | Definition | Title/Description                |
| ----------------------------- | ------- | ---------------- | ---------- | ---------- | -------------------------------- |
| - [ci.platform](#ciplatform ) | No      | enum (of string) | No         | -          | CI platform running the analysis |
| - [ci.job.id](#cijobid )      | No      | string           | No         | -          | Unique identifier of the CI job  |
| - [ci.job.url](#cijoburl )    | No      | string           | No         | -          | URL to the CI job run            |
| - [](#additionalProperties )  | No      | object           | No         | -          | -                                |

## <a name="ciplatform"></a>1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `ci.platform`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** CI platform running the analysis

Must be one of:
* "github"
* "gitlab"

## <a name="cijobid"></a>2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `ci.job.id`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier of the CI job

## <a name="cijoburl"></a>3. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `ci.job.url`

|            |          |
| ---------- | -------- |
| **Type**   | `string` |
| **Format** | `uri`    |

**Description:** URL to the CI job run

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-04-20 at 23:57:35 +0000
