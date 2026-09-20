---
sidebar_position: 2
tags:
  - analyzers
---

# Image Analysis

You can analyze any public container image using the built-in [analyzers](../concepts/analyzers.md). By default, `regis` produces a JSON report on `stdout`.

```bash
regis analyze nginx:latest
```

## Generating an HTML Report

To generate a self-contained HTML report alongside the JSON report, use the `--html` flag:

```bash
regis analyze nginx:latest --html
```

This writes a single, portable `report.html` file — no server or base URL configuration required. Open it in any browser or ship it as a CI artifact. See [Reports](../concepts/reports.md) for details on the report architecture.

## Advanced Tools

`regis` includes specialized subcommands for advanced workflows:

- `bootstrap`: Infrastructure as Code (IaC) for your analysis. Bootstrap a new Git repository or a new [playbook](../concepts/playbooks.md).
- `evaluate`: Test [playbooks](../concepts/playbooks.md) against existing analysis reports without re-fetching image data.

:::note
GitLab CI integration ships as a reusable template from its own repository,
[`trivoallan/regis-gitlab`](https://github.com/trivoallan/regis-gitlab). See the
**[GitLab integration guide](./integrations/gitlab.md)**.
:::
