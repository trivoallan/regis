# Regis Well-Known Metadata

**Title:** Regis Well-Known Metadata

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Standard metadata fields recognized by regis across all playbooks.

| Property                     | Pattern | Type   | Deprecated | Definition | Title/Description                                    |
| ---------------------------- | ------- | ------ | ---------- | ---------- | ---------------------------------------------------- |
| - [ci](#ci )                 | No      | object | No         | -          | Continuous-integration context for the analysis run. |
| - [](#additionalProperties ) | No      | object | No         | -          | -                                                    |

## <a name="ci"></a>1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `ci`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

**Description:** Continuous-integration context for the analysis run.

| Property                        | Pattern | Type             | Deprecated | Definition | Title/Description                |
| ------------------------------- | ------- | ---------------- | ---------- | ---------- | -------------------------------- |
| - [platform](#ci_platform )     | No      | enum (of string) | No         | -          | CI platform running the analysis |
| - [job](#ci_job )               | No      | object           | No         | -          | -                                |
| - [](#ci_additionalProperties ) | No      | object           | No         | -          | -                                |

### <a name="ci_platform"></a>1.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `platform`

|          |                    |
| -------- | ------------------ |
| **Type** | `enum (of string)` |

**Description:** CI platform running the analysis

Must be one of:
* "github"
* "gitlab"

### <a name="ci_job"></a>1.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `job`

|                           |                                                                             |
| ------------------------- | --------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                    |
| **Additional properties** | ![Any type: allowed](https://img.shields.io/badge/Any%20type-allowed-green) |

| Property                            | Pattern | Type   | Deprecated | Definition | Title/Description               |
| ----------------------------------- | ------- | ------ | ---------- | ---------- | ------------------------------- |
| - [id](#ci_job_id )                 | No      | string | No         | -          | Unique identifier of the CI job |
| - [url](#ci_job_url )               | No      | string | No         | -          | URL to the CI job run           |
| - [](#ci_job_additionalProperties ) | No      | object | No         | -          | -                               |

#### <a name="ci_job_id"></a>1.2.1. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `id`

|          |          |
| -------- | -------- |
| **Type** | `string` |

**Description:** Unique identifier of the CI job

#### <a name="ci_job_url"></a>1.2.2. ![Optional](https://img.shields.io/badge/Optional-yellow) Property `url`

|            |          |
| ---------- | -------- |
| **Type**   | `string` |
| **Format** | `uri`    |

**Description:** URL to the CI job run

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2026-06-22 at 01:48:28 +0000
