---
sidebar_position: 2
tags:
  - analyzers
---

# Analyzers

`regis` uses a pluggable architecture where separate **Analyzers** are responsible for extracting specific types of data from container images or their build artifacts.

Each analyzer runs independently and contributes to a unified data model that is later evaluated against your [Playbooks](./playbooks.md).

## Core Analyzers

:::info[Reference]
RegiS includes several built-in analyzers.
For a complete list and technical details for each, see the [Analyzers Reference](../reference/analyzers/).
:::

- **OCI**: Fetches low-level image metadata (labels, architecture, layers, creation date) directly from the registry via `regctl`.
- **CVE**: Performs vulnerability scanning (CVEs) via grype.
- **Secrets**: Detects embedded secrets and credentials via trufflehog.
- **SBOM**: Generates a Software Bill of Materials (CycloneDX / SPDX) via syft.
- **Hadolint**: Lints Dockerfiles to ensure best practices and security standards are met.
- **Freshness**: Calculates the "age" of an image relative to its base image and updates.
- **End-Of-Life (EOL)**: Checks if the base OS or language runtime is approaching its end of support.
- **Popularity**: (Optional) Analyzes registry metrics to gauge community adoption.

## What an analyzer exposes

An analyzer produces three kinds of output. Keep them distinct — they play
different roles in the [four-layer model](./rules.md#the-four-layer-model).

- **Metrics** are aggregate measurements: `critical_count`, `has_sbom`, `score`,
  `age_days`, the list of detected licenses. Metrics live under the `results.*`
  namespace (for example, `results.cve.critical_count`) and are **what
  [criteria](./rules.md#criteria-vs-rules) evaluate**. When you write a rule
  condition, you read metrics.
- **Findings** are individual detections of a _problem_: a specific CVE on a
  package, a leaked secret. Findings are evidence — they back the metric and let
  you drill down into _why_ a count is what it is. Security analyzers (CVE,
  Secrets) produce findings; rules typically evaluate the metric that aggregates
  them, not each finding.
- **Components (inventory)** are the contents of the image, not problems. The SBOM
  analyzer enumerates the packages and libraries in the image. A component is
  _inventory_, **not a finding** — having a package is not, by itself, an issue.
  Do not treat SBOM components as findings.

:::tip
Rule of thumb: criteria read **metrics** (`results.*`); **findings** and
**components** are evidence you inspect in the report, not values you compare in a
condition.
:::

## How it works

Below is the step-by-step process `regis` follows when analyzing an image:

```mermaid
graph TD
    A[Start: regis analyze] --> B[Fetch Metadata via regctl]
    B --> C{Run Analyzers}
    C --> D[grype: Vulns / syft: SBOM]
    C --> E[Hadolint: Linter]
    C --> F[OCI: Metadata]
    C --> G[...]

    D --> H[Aggregate Results]
    E --> H
    F --> H
    G --> H

    H --> I[Execute Playbook Engine]
    I --> J[Evaluate Policies via jsonLogic]
    J --> K[Generate Interactive HTML Report]
    J --> L[Output Machine-readable JSON]
    K --> M[End]
    L --> M
```

1. **Extraction**: The CLI invokes the configured analyzers.
2. **Normalization**: Results from different tools (JSON, text, etc.) are normalized into a standard `regis` format.
3. **Context Injection**: This data becomes the "Context" for rule evaluation.

:::tip
You can enable or disable specific analyzers via the CLI flags or the configuration file to speed up analysis if you only need specific data.
:::
