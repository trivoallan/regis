---
sidebar_position: 1
---

# Getting Started

`regis` is designed to be easy to set up and run, whether locally or in a CI/CD environment.

## Installation

### Docker (Recommended)

The easiest way to use `regis` without managing local dependencies is to use the official Docker image. It comes pre-packaged with Skopeo, Trivy, Hadolint, and Dockle.

```bash
docker run --rm trivoallan/regis --help
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
pip install regis
```

:::tip
For developers wanting to contribute to the project, use **Pipenv**:
`pipenv install --dev`
:::
