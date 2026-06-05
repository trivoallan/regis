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

## Create a playbook with the AI assistant

If you use [Claude Code](https://claude.ai/code) with the
[oh-my-claudecode](https://github.com/vibeeval/vibecosystem) plugin, the `create-playbook` skill
ships with this repository and is available automatically when you open it as your working
directory.

### Prerequisites

1. Install [Claude Code](https://claude.ai/code):

   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. Install the oh-my-claudecode plugin:

   ```bash
   omc install
   ```

3. Open this repository as your working directory in Claude Code.

### Invoke the skill

Type the following in Claude Code:

```text
/create-playbook
```

Alternatively, describe what you need and Claude will offer to use the skill:

```text
Create a security playbook for my production images — cve checks,
Dockerfile linting, and GitLab CI integration.
```

### What the assistant does

The assistant guides you through six interactive stages:

| Stage             | What it covers                                                                                               |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| 1. Context        | Playbook name, description, target CI system (GitLab / GitHub / standalone)                                  |
| 2. Rules          | Provider selection (cve, secrets, hadolint, sbom, freshness, scorecarddev, oci…) and threshold configuration |
| 3. Tiers          | Gold / Silver / Bronze scoring thresholds                                                                    |
| 4. CI integration | GitLab badges and checklists, or GitHub Actions                                                              |
| 5. Inputs schema  | _(Optional)_ Validate non-image inputs such as project IDs or security document URLs                         |
| 6. Output         | Writes the playbook bundle to your chosen directory                                                          |

### Output

The skill writes a ready-to-use playbook bundle:

```text
my-policy/
├── playbook.yaml          # Rules, tiers, badges, CI integration
├── README.md              # Generated documentation
└── meta.schema.json       # Optional: project metadata schema
```

Run your new playbook immediately:

```bash
regis analyze nginx:latest --playbook my-policy/ --html
```

---

## Bootstrap a skeleton manually

To start from a minimal skeleton without the AI assistant, use the `bootstrap` command:

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
