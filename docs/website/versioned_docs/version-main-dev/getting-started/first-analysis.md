---
sidebar_position: 2
---

# Running an analysis

You can analyze any public container image. By default, `regis-cli` produces a JSON report on `stdout`.

```bash
regis-cli analyze nginx:latest
```

## Generating a Web Report

To generate a rich HTML report alongside the JSON report, use the `--site` (or `-s`) flag:

```bash
regis-cli analyze nginx:latest --site
```

Reports are written to the `reports/` directory by default (e.g., `reports/docker.io/library/nginx/sha256-.../index.html`).

## Advanced Tools

`regis-cli` includes specialized subcommands for advanced workflows:

- `bootstrap`: Infrastructure as Code (IaC) for your analysis. Bootstrap a new Git repository or a new playbook.
- `evaluate`: Test playbooks against existing analysis reports without re-fetching image data.
- `gitlab`: Seamless integration with GitLab CI/CD for automated reporting and MR updates.

:::info
Our **[GitLab integration](../integrations/gitlab.md)** is currently the most feature-rich, offering automated Merge Request comments, status updates, and deep CI/CD pipeline integration.
:::
