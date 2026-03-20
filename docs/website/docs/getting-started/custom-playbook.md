---
sidebar_position: 3
---

# Creating a custom playbook

Playbooks allow you to define your own security policies and customize the structure of your reports. While the [Default Playbook](../reference/playbooks/default/overview.md) covers many best practices, you may want to create a custom one tailored to your organization's specific needs.

## 1. Bootstrapping a Playbook

The easiest way to start is by using the `bootstrap` command. This creates a new directory with a skeleton playbook and necessary configuration files.

```bash
regis-cli bootstrap playbook my-security-policy
```

This command will prompt you for:

- **Name**: The display name of your playbook (e.g., "Corporate Security Policy").
- **Slug**: A unique identifier used for file generation (e.g., `corp-security`).

## 2. Understanding the Structure

A basic playbook (`playbook.yaml`) looks like this:

```yaml
name: My Security Policy
slug: corp-security
sections:
  - name: Critical Checks
    scorecards:
      - name: no-root
        title: Image must not run as root
        condition:
          "!=": [{ var: results.skopeo.platforms.0.user }, root]
```

- **Scorecards**: Individual rules tied to a **condition**.
- **Conditions**: Logic defined using [JSON Logic](https://jsonlogic.com/). They evaluate against the raw analysis data.
- **Results Path**: Data is accessed via dot-notation (e.g., `results.trivy.critical_count`).

## 3. Running your Playbook

To analyze an image using your newly created playbook, use the `--playbook` (or `-p`) flag:

```bash
regis-cli analyze nginx:latest -p my-security-policy/playbook.yaml --site
```

## 4. Local Iteration (Dry-run)

If you already have a report from a previous analysis, you can iterate on your playbook rules without re-analyzing the image:

```bash
# 1. Save analysis results to a file
regis-cli analyze nginx:latest -o report.json

# 2. Test your playbook against the saved report
regis-cli evaluate report.json -p my-security-policy/playbook.yaml --site
```

:::tip
For a full list of available fields and advanced configurations like GitLab integration, check the [Playbook Schema Reference](../reference/schemas/playbook/definition.schema.md) and the [Deep-dive Overview](../overview/playbooks.md).
:::
