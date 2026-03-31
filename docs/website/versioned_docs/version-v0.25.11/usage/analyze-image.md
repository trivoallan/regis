---
tags:
  - analyzers
---

# Image Analysis

You can analyze any public container image. By default, `regis` produces a JSON report on `stdout`.

```bash
regis analyze nginx:latest
```

## Generating a Web Report

To generate a rich, interactive HTML report alongside the JSON report, use the `--site` (or `-s`) flag:

```bash
regis analyze nginx:latest --site --open
```

The `--open` flag will automatically launch your default browser to view the generated dashboard.

`regis` now uses a modern **Single Page Application (SPA)** based on Docusaurus to provide an exceptional viewing experience.

Reports are written to the `reports/` directory by default (e.g., `reports/docker.io/library/nginx/sha256-.../index.html`).

### Serving from Subpaths

Because the report is an SPA, it needs to know its base URL if it's not served from the root of a domain. Use the `--base-url` flag for this:

```bash
# Example for GitLab artifacts
regis analyze nginx:latest --site --base-url "/group/project/-/jobs/123/artifacts/file/reports/123/"
```

:::tip
When using the [GitLab integration](./integrations/gitlab.md), this base URL is calculated automatically by our standard CI template.
:::

## Advanced Tools

`regis` includes specialized subcommands for advanced workflows:

- `bootstrap`: Infrastructure as Code (IaC) for your analysis. Bootstrap a new Git repository or a new playbook.
- `evaluate`: Test playbooks against existing analysis reports without re-fetching image data.
- `gitlab`: Seamless integration with GitLab CI/CD for automated reporting and MR updates.

:::info
Our **[GitLab integration](./integrations/gitlab.md)** is currently the most feature-rich, offering automated Merge Request comments, status updates, and deep CI/CD pipeline integration.
:::
