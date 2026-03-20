---
sidebar_position: 1
---

# Architecture

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
    title System Context diagram for regis-cli

    Person(user, "User / CI Bot", "A developer or a CI/CD pipeline.")
    System(regis, "regis-cli", "Analyzes container images and generates reports.")

    System_Ext(registry, "Container Registry", "External registry (GHCR, Docker Hub, etc.).")
    System_Ext(tools, "Security Tools", "External binaries (Trivy, Skopeo, Hadolint).")

    Rel(user, regis, "Uses", "CLI")
    Rel(regis, tools, "Orchestrates", "Shell")
    Rel(tools, registry, "Queries", "HTTPS")
    Rel(regis, user, "Delivers reports", "HTML/JSON")
```

### Container View

```mermaid
C4Container
    title Container diagram for regis-cli

    Person(user, "User / CI Bot", "A developer or a CI/CD pipeline.")
    System_Boundary(boundary, "regis-cli") {
        Container(cli, "CLI Application", "Python, Click", "Handles user input.")
        Container(engine, "Analysis Engine", "Python", "Manages analyzer lifecycle.")
        Container(playbook, "Playbook Engine", "Python, JSON Logic", "Evaluates security rules.")
        Container(reporting, "Reporting Engine", "Python, Jinja2", "Generates reports.")
        Container(connectors, "Registry Connectors", "Python", "Interacts with external tools.")
    }

    System_Ext(registry, "Container Registry", "External registry.")
    System_Ext(tools, "Security Tools", "Trivy, Skopeo, Hadolint, Dockle.")

    Rel(user, cli, "Invokes", "CLI")
    Rel(cli, engine, "Triggers", "Calls")
    Rel(engine, connectors, "Uses", "Calls")
    Rel(connectors, tools, "Executes", "Subprocess")
    Rel(tools, registry, "Queries", "HTTPS")
    Rel(engine, playbook, "Metadata", "Data")
    Rel(playbook, reporting, "Results", "Data")
    Rel(reporting, user, "Outputs", "Files")
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

The reporting layer transforms the analysis and playbook results into various formats.
It uses `Jinja2` templates to produce rich, themeable HTML reports for human review and structured JSON (see [Report Schema](../reference/schemas/report/report.schema.md)) for automated processing.

## Technology Stack

The project uses the following technologies:

- **Language**: Python 3.14+
- **Dependency Management**: Pipenv
- **CLI Framework**: Click
- **Templating**: Jinja2
- **Linting/Formatting**: Ruff
- **External Tools**: Skopeo, Trivy, Hadolint, Dockle
- **Testing**: Pytest
- **CI/CD**: GitHub Actions, Release Please, Super-Linter
