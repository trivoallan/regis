---
sidebar_position: 4
tags:
  - playbooks
  - rules
---

# Playbook customisation

Playbooks let you define your own security policies and customise the structure of your reports.
While the [Default Playbook](../reference/playbooks/default/index.md) covers many best practices,
you may want to create one tailored to your organisation's needs.

## Bootstrap a skeleton

The fastest way to start is to scaffold a minimal skeleton with the `bootstrap`
command, then edit it to match your policy:

```bash
regis bootstrap playbook my-security-policy
```

This creates a `my-security-policy/` directory with a `playbook.yaml` stub. The command prompts
you for:

- **Name**: The display name of your playbook (for example, "Corporate Security Policy").
- **Slug**: A short identifier used for file generation (for example, `corp-security`).

---

## Understand the playbook structure

A minimal playbook uses the Kubernetes-style envelope (`apiVersion`/`kind`/`metadata`/`spec`). Each rule binds a provider criterion by slug:

```yaml
# yaml-language-server: $schema=https://trivoallan.github.io/regis/schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: my-security-policy # machine id — RFC 1123 DNS label
  title: My Security Policy # display name
  labels:
    app.kubernetes.io/version: "1.0.0"

spec:
  tiers:
    - name: Gold
      condition: { ">": [{ var: rules_summary.score }, 90] }
    - name: Silver
      condition: { ">": [{ var: rules_summary.score }, 70] }

  rules:
    - provider: cve
      criterion: cve-count
      slug: cve-critical
      level: critical
      options:
        level: critical
        max_count: 0

    - provider: hadolint
      criterion: severity-count
      slug: hadolint-errors
      level: warning
      options:
        level: error
        max_count: 0
```

Key concepts:

- **Rules** (under `spec.rules`): Each rule binds a provider criterion (`criterion:`) with a
  unique `slug`, a `level` that affects scoring, and provider-specific `options`.
- **Tiers** (under `spec.tiers`): Named compliance levels resolved from `rules_summary.score`
  using JSON Logic conditions.
- **Results path**: Raw analyser data is accessible via dot-notation
  (for example, `results.cve.critical_count`).

:::tip
To migrate an existing playbook from the old `schemaVersion`/`name` format, run
`regis playbook upgrade path/to/playbook.yaml`. See the
[upgrade guide](../upgrade/playbook-schema-v1.md) for details.
:::

---

## Run your playbook

```bash
regis analyze nginx:latest --playbook my-policy/ --html
```

## Iterate locally (dry-run)

Iterate on rules without re-analysing the image:

```bash
# 1. Save analysis results
regis analyze nginx:latest -o report.json

# 2. Re-evaluate against the saved report
regis evaluate report.json --playbook my-policy/ --html
```

:::tip
For the full list of available rule templates, providers, and advanced options (badges, GitLab
checklists, inputs schema), see the
[Playbook Schema Reference](../reference/schemas/playbook/v1alpha1/playbook.schema.md) and the
[Playbooks concept guide](../concepts/playbooks.md).
:::
