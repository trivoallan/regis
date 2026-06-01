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
