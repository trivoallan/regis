---
sidebar_position: 1
---

# Getting started

## What is `regis-cli`?

`regis-cli` is a **Container Security & Policy-as-Code Orchestration**. It provides unified analysis, custom playbooks, and highly customizable interactive reports for production-ready CI/CD.

:::tip
For a detailed look at how the tool works and its internal structure, see the [Concepts](./concepts) section.
:::

## Installation

### Docker (Recommended)

The easiest way to use `regis-cli` without managing local dependencies is to use the official Docker image. It comes pre-packaged with Skopeo, Trivy, Hadolint, and Dockle.

```bash
docker run --rm trivoallan/regis-cli --help
```

### Local Installation

#### Prerequisites

The requirements depend on whether you use the Docker image or install the tool locally.

- **Core Requirement**:
  - **Skopeo**: Essential for multi-architecture registry inspection and metadata extraction.
- **Optional Analyzers**:
  - **Trivy**: Required for vulnerability scanning and SBOM generation.
  - **Hadolint**: Required for Dockerfile linting.
  - **Dockle**: Required for container image security linting.

```bash
pip install regis-cli
```

:::tip
For developers wanting to contribute to the project, use **Pipenv**:
`pipenv install --dev`
:::
