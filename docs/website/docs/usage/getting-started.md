---
sidebar_position: 1
---

# Getting Started

`regis` is designed to be easy to set up and run, whether locally or in a CI/CD environment.

## Installation

### Docker (Recommended)

The easiest way to use `regis` without managing local dependencies is to use the official Docker image. It comes pre-packaged with regctl, grype, syft, trufflehog, Hadolint, and Dockle.

```bash
docker run --rm trivoallan/regis --help
```

### Local Installation

#### Prerequisites

The requirements depend on whether you use the Docker image or install the tool locally.

- **Core Requirement**:
  - **regctl**: Essential for multi-architecture registry inspection and metadata extraction.
- **Optional [Analyzers](../concepts/analyzers.md)**:
  - **grype**: Required for vulnerability (CVE) scanning.
  - **syft**: Required for SBOM generation.
  - **trufflehog**: Required for embedded secret detection.
  - **Hadolint**: Required for Dockerfile linting.
  - **Dockle**: Required for container image security linting.

```bash
pip install regis
```

:::tip
For developers wanting to contribute to the project, use **Pipenv**:
`pipenv install --dev`
:::

## GitHub Repository Configuration

If you plan to use automated documentation snapshots or the archive feature on a GitHub repository with protected branches, ensure that the **"Allow auto-merge"** option is enabled in your repository's general settings. This allows the automated workflows to synchronize documentation safely without manual intervention on every update. See the [GitHub Actions integration guide](./integrations/github.md) for more details.

## Your First Analysis

Run your first analysis against a public image to see Regis in action:

```bash
regis analyze alpine:latest --evaluate --html
```

This command:

- Runs all built-in [analyzers](../concepts/analyzers.md) against the `alpine:latest` image
- Evaluates results against the default [playbook](../concepts/playbooks.md)
- Writes a self-contained `report.html` you can open in any browser

Open the generated `report.html` to see a compliance score, vulnerability findings, best practice checks, and image metadata. See [Scoring](../concepts/scoring.md) to understand how scores are calculated. For an interactive, filterable dashboard and multi-archive browsing, see the standalone [regis-dashboard](https://github.com/trivoallan/regis-dashboard) project.

**Next steps:**

- Define custom rules: [Custom Playbooks](./custom-playbook.md)
- Integrate into your workflow: [CI/CD Integration](./integrations/github.md)
- Track changes over time: [Archives](../concepts/archives.md)
- Fine-tune behavior: [Advanced Configuration](./configuration.md)
