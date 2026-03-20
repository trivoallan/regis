---
sidebar_position: 1
---

# Installation

`regis-cli` is a powerful Docker registry analysis tool designed to inspect container images, evaluate security policies via playbooks, and generate comprehensive reports.

## Prerequisites

The requirements depend on whether you use the Docker image or install the tool locally.

- **Core Requirement**:
  - **Skopeo**: Essential for multi-architecture registry inspection and metadata extraction.
- **Optional Analyzers**:
  - **Trivy**: Required for vulnerability scanning and SBOM generation.
  - **Hadolint**: Required for Dockerfile linting.
  - **Dockle**: Required for container image security linting.

## Installation

### Docker (Recommended)

The easiest way to use `regis-cli` without managing local dependencies is to use the official Docker image. It comes pre-packaged with Skopeo, Trivy, Hadolint, and Dockle.

```bash
docker run --rm trivoallan/regis-cli --help
```

### Local Installation

If you prefer a local installation, ensure you have **Python 3.14 or later** and **Skopeo** installed in your system.

```bash
pip install regis-cli
```

:::tip
For developers wanting to contribute to the project, use **Pipenv**:
`pipenv install --dev`
:::
