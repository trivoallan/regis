---
sidebar_position: 1
tags:
  - introduction
---

# Introduction

`regis-cli` is a command-line tool designed to analyze container image registries, evaluate security playbooks, and generate comprehensive reports. It provides deep visibility into container image metadata and security posture, enabling automated policy enforcement in CI/CD environments.

## Purpose

You use `regis-cli` to:

- Analyze multi-architecture container images.
- Evaluate custom security and compliance rules using JSON logic.
- Generate human-readable HTML reports and machine-readable JSON reports.
- Integrate security checks into GitHub Actions or GitLab CI pipelines.

## Architecture

`regis-cli` uses a modular, pluggable architecture that separates data extraction from policy evaluation and reporting.

```mermaid
C4Context
    title System Context — regis-cli

    Person(user, "User / CI Bot", "Developer or automated CI/CD pipeline.")
    System(regis, "regis-cli", "Analyzes container images, evaluates security playbooks, and generates HTML and JSON reports.")
    System_Ext(registry, "Container Registry", "OCI-compliant registry: GHCR, Docker Hub, etc.")
    System_Ext(tools, "Security Tools", "External binaries: Trivy, Skopeo, Hadolint.")

    Rel(user, regis, "Invokes", "CLI / GitHub Actions")
    Rel(regis, tools, "Orchestrates", "Subprocess")
    Rel(tools, registry, "Pulls image data", "HTTPS")
    Rel(regis, user, "Delivers", "HTML / JSON report")

    UpdateElementStyle(user, $fontColor="white", $bgColor="#08427B", $borderColor="#052E56")
    UpdateElementStyle(regis, $fontColor="white", $bgColor="#1168BD", $borderColor="#0B4A87")
    UpdateElementStyle(registry, $fontColor="white", $bgColor="#5D6D7E", $borderColor="#3D4D5E")
    UpdateElementStyle(tools, $fontColor="white", $bgColor="#5D6D7E", $borderColor="#3D4D5E")
    UpdateRelStyle(user, regis, $textColor="#1168BD", $lineColor="#1168BD")
    UpdateRelStyle(regis, user, $textColor="#1A8C4E", $lineColor="#1A8C4E")
    UpdateRelStyle(regis, tools, $textColor="#B7770D", $lineColor="#B7770D")
    UpdateRelStyle(tools, registry, $textColor="#5D6D7E", $lineColor="#5D6D7E")
```

### Container View

```mermaid
C4Container
    title Container Diagram — regis-cli

    Person(user, "User / CI Bot", "Developer or automated CI/CD pipeline.")
    System_Boundary(boundary, "regis-cli") {
        Container(cli, "CLI", "Python · Click", "Entry point: parses arguments and orchestrates the analysis workflow.")
        Container(engine, "Analysis Engine", "Python", "Manages the analyzer lifecycle, shared auth, and result aggregation.")
        Container(playbook, "Playbook Engine", "Python · JSON Logic", "Evaluates consolidated metadata against user-defined security rules.")
        Container(reporting, "Reporting Engine", "React · Docusaurus", "Generates interactive SPA dashboards and structured JSON reports.")
        Container(connectors, "Registry Connectors", "Python", "Delegates extraction tasks to external security tools via subprocess.")
    }

    System_Ext(registry, "Container Registry", "OCI-compliant registry: GHCR, Docker Hub, etc.")
    System_Ext(tools, "Security Tools", "Trivy, Skopeo, Hadolint, Dockle.")

    Rel(user, cli, "Invokes", "CLI / GitHub Actions")
    Rel(cli, engine, "Triggers analysis", "Function call")
    Rel(engine, connectors, "Delegates extraction", "Function call")
    Rel(connectors, tools, "Executes", "Subprocess")
    Rel(tools, registry, "Pulls image data", "HTTPS")
    Rel(engine, playbook, "Passes metadata", "Data")
    Rel(playbook, reporting, "Passes results", "Data")
    Rel(reporting, user, "Outputs", "HTML / JSON files")

    UpdateElementStyle(user, $fontColor="white", $bgColor="#08427B", $borderColor="#052E56")
    UpdateElementStyle(cli, $fontColor="white", $bgColor="#1168BD", $borderColor="#0B4A87")
    UpdateElementStyle(engine, $fontColor="white", $bgColor="#1A8C4E", $borderColor="#136B3B")
    UpdateElementStyle(playbook, $fontColor="white", $bgColor="#B7770D", $borderColor="#8C5B0A")
    UpdateElementStyle(reporting, $fontColor="white", $bgColor="#7B2D8B", $borderColor="#5C2168")
    UpdateElementStyle(connectors, $fontColor="white", $bgColor="#0D7F8C", $borderColor="#0A5F69")
    UpdateElementStyle(registry, $fontColor="white", $bgColor="#5D6D7E", $borderColor="#3D4D5E")
    UpdateElementStyle(tools, $fontColor="white", $bgColor="#5D6D7E", $borderColor="#3D4D5E")
    UpdateRelStyle(user, cli, $textColor="#1168BD", $lineColor="#1168BD")
    UpdateRelStyle(cli, engine, $textColor="#1A8C4E", $lineColor="#1A8C4E")
    UpdateRelStyle(engine, connectors, $textColor="#0D7F8C", $lineColor="#0D7F8C")
    UpdateRelStyle(connectors, tools, $textColor="#5D6D7E", $lineColor="#5D6D7E")
    UpdateRelStyle(tools, registry, $textColor="#5D6D7E", $lineColor="#5D6D7E")
    UpdateRelStyle(engine, playbook, $textColor="#B7770D", $lineColor="#B7770D")
    UpdateRelStyle(playbook, reporting, $textColor="#7B2D8B", $lineColor="#7B2D8B")
    UpdateRelStyle(reporting, user, $textColor="#1A8C4E", $lineColor="#1A8C4E")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Core Components

The following sections describe the primary components of the `regis-cli` system.

### CLI Layer

The command-line interface, built with the `Click` library, handles user input, argument parsing, and command orchestration. It serves as the primary entry point for both manual use and CI/CD integration.

### Analysis Engine

The analysis engine orchestrates the execution of pluggable analyzers. It manages common resources, such as registry authentication and caching, ensuring that analyzers can focus on extracting specific metadata.

### Analyzers

Analyzers are modular components responsible for gathering data from registries or local files. Current built-in analyzers include:

- **Skopeo**: Extracts multi-architecture metadata, labels, and layer information. ([Schema](../reference/schemas/analyzer/skopeo.schema.md))
- **Trivy**: Generates Software Bill of Materials (SBOM) and performs vulnerability scanning. ([Schema](../reference/schemas/analyzer/trivy.schema.md))
- **Hadolint**: Lints Dockerfiles for best practices. ([Schema](../reference/schemas/analyzer/hadolint.schema.md))
- **Dockle**: Container image linter for security and best practices. ([Schema](../reference/schemas/analyzer/dockle.schema.md))
- **Versioning**: Validates semantic versioning consistency. ([Schema](../reference/schemas/analyzer/versioning.schema.md))
- **Freshness**: Calculates image age. ([Schema](../reference/schemas/analyzer/freshness.schema.md))

### Playbook Engine

The playbook engine evaluates consolidated analyzer results against user-defined rules. These rules use `jsonLogic` to define complex conditional logic for security and compliance checks, such as "no critical vulnerabilities" or "maximum image age."

### Reporting Layer

The reporting layer transforms the analysis and playbook results into high-quality, actionable formats.
It leverages a modern **Single Page Application (SPA)** architecture built with **Docusaurus and React** to produce rich, interactive dashboards for human review. It also generates structured JSON (see [Report Schema](../reference/schemas/report/report.schema.md)) for automated processing.

## Technology Stack

The project uses the following technologies:

- **Language**: Python 3.13+
- **Dependency Management**: Pipenv
- **CLI Framework**: Click
- **Templating**: Jinja2 (Data) & Docusaurus/React (UI)
- **Linting/Formatting**: Ruff
- **External Tools**: Skopeo, Trivy, Hadolint, Dockle
- **Testing**: Pytest
- **CI/CD**: GitHub Actions, Release Please, Super-Linter
