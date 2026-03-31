---
tags:
  - playbooks
---

# Playbooks

Playbooks are the core of the `regis` evaluation engine. They define the security and compliance rules that the tool evaluates against container image metadata.

## Purpose

A playbook serves two primary functions:

1.  **Policy Enforcement**: It defines a set of "scorecards" (rules) that an image must pass to be considered compliant.
2.  **Report Structuring**: It defines the layout and content of the generated HTML report, including pages, sections, and widgets.

By using playbooks, you can decouple the raw data extraction (performed by analyzers like Skopeo or Trivy) from the business logic used to evaluate that data. This allow you to apply different compliance standards to different environments or projects without changing the underlying analysis code.

## Core Concepts

The following concepts are central to understanding and creating playbooks. For a complete technical reference of all available attributes, refer to the [Playbook Schema Definition](../reference/schemas/playbook/definition.schema.md).

### Scorecards

A scorecard is a single evaluation rule. It defines a condition that must evaluate to true for the scorecard to pass. Scorecards are typically grouped into sections and can be assigned to priority levels (such as critical, warning, or info).

### UI Structure

Playbooks define how analysis results are presented in the HTML report through a hierarchical structure:

- **Pages**: The top-level containers in the report. Each page is a distinct view in the SPA.
- **Sections**: Groups of related scorecards and widgets within a page.
- **Widgets**: Interactive UI components that display specific values or metrics. Widgets can be key-value summaries, KPI cards, or detailed tables.
  rendered from templates.

For example, a section named "Mandatory Requirements" becomes `mandatory_requirements`.

### Tiers

Playbooks can define **Tiers** to categorize the overall quality of an image based on the compliance score. Each tier is defined by a name and a condition.

```yaml
tiers:
  - name: Gold
    condition: { ">": [{ var: rules_summary.score }, 90] }
  - name: Silver
    condition: { ">": [{ var: rules_summary.score }, 70] }
  - name: Bronze
    condition: { ">": [{ var: rules_summary.score }, 50] }
```

The evaluator checks tiers in the order they are defined. The first tier whose condition evaluates to truthy is assigned to the report.

### Badges

**Badges** provide high-level visual status indicators in the report header. They are dynamic and support variable interpolation using the `${var.path}` syntax.

```yaml
badges:
  - slug: score
    scope: Score
    value: "${rules_summary.score}"
    class: information
  - slug: freshness
    scope: Freshness
    condition: { "==": [{ var: rules.freshness-age.passed }, true] }
    class: success
```

| Field       | Description                                                                                                                 |
| :---------- | :-------------------------------------------------------------------------------------------------------------------------- |
| `slug`      | A unique machine-readable identifier for the badge (used for lookups and integrations).                                     |
| `scope`     | The primary label for the badge (e.g., "Score", "CVE").                                                                     |
| `value`     | The value to display. Can use `${}` interpolation to reference report data.                                                 |
| `condition` | A JSON Logic expression. If provided, the badge is only displayed when the condition is truthy.                             |
| `class`     | The visual style/color of the badge. Supported: `success` (green), `warning` (yellow), `error` (red), `information` (blue). |

## Evaluation Mechanism

`regis` uses two powerful technologies to evaluate and present data in playbooks.

### JSON Logic

Scorecard conditions and widget display preferences use **JSON Logic**. This is a lightweight, language-agnostic way to define complex conditional logic as JSON objects.

You use JSON Logic to access analysis results and perform comparisons. For example, to check if an image has no critical vulnerabilities, you would use:

```json
{ "==": [{ "var": "results.trivy.critical_count" }, 0] }
```

Or, to check the score of a specific section using its normalized name:

```json
{
  ">=": [
    { "var": "playbooks.0.pages.compliance.sections.security_checks.score" },
    90
  ]
}
```

Commonly used operators include:

- `==`, `!=`: Equality and inequality.
- `>`, `>=`, `<`, `<=`: Numeric comparisons.
- `in`: Checks if a value is present in a list.
- `!`, `!!`: Logical NOT and non-null checks.
- `and`, `or`: Logical combinations.

### Template Interpolation (Jinja2)

While JSON Logic handles the evaluation "truth," `regis` uses **Jinja2** for dynamic data interpolation within the report. You can use Jinja2 expressions within widgets to format values or calculate percentages directly from the analysis context.

For example, to display the overall compliance score in a widget, you might use:

```yaml
- label: Overall Compliance
  value: "{{ playbooks.0.score }}%"
- label: Mandatory Checks
  value: "{{ playbooks.0.pages.compliance.sections.security_checks.score }}%"
```

## GitLab Integration

Playbooks can automate Merge Request (MR) management in GitLab through the `integrations.gitlab` key.

### Badge Synchronization

The `badges` list automatically synchronizes authorized status badges as GitLab labels. Each badge in the list is identified by its **slug**.

```yaml
integrations:
  gitlab:
    badges:
      - score
      - freshness
      - cve-critical
```

This ensures that the MR UI (labels) always reflects the visual status shown in the HTML report. Regular condition-based labels are deprecated in favor of this badge-driven approach.

### MR Description Checklists

The `checklists` list adds configurable checklists to the body of the Merge Request description. This lets you define manual verification steps that reviewers must tick off before approving the MR.

Each checklist can have a `title` and a list of `items`. Each item has a mandatory `label` and two optional conditions:

| Field      | Description                                                                                                                                                             |
| :--------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `show_if`  | A JSON Logic expression. If provided, the item is only added to the checklist when the expression evaluates to truthy. Items referencing unavailable data are excluded. |
| `check_if` | A JSON Logic expression. If provided and truthy, the checkbox renders pre-checked (`- [x]`). Otherwise it renders unchecked (`- [ ]`).                                  |

```yaml
integrations:
  gitlab:
    checklists:
      - title: 📝 Security Review
        items:
          - label: Security review completed # <1>
          - label: No critical vulnerabilities found
            show_if: { "==": [{ var: results.trivy.critical_count }, 0] } # <2>
            check_if: { "==": [{ var: results.trivy.critical_count }, 0] } # <3>
      - title: 🚀 Compliance checks
        items:
          - label: Image from a trusted registry
            show_if:
              {
                "in":
                  [{ var: request.registry }, [docker.io, quay.io, ghcr.io]],
              }
            check_if:
              {
                "in":
                  [{ var: request.registry }, [docker.io, quay.io, ghcr.io]],
              }
```

(1) Unconditional item — always included, always unchecked.
(2) `show_if` — only included when `critical_count` equals 0.
(3) `check_if` — if included, renders pre-checked when `critical_count` is 0.

:::tip
You can use `show_if` and `check_if` independently. For example, an item may always be shown (`no show_if`) but pre-checked only when a condition passes.
:::

The engine exposes the resolved checklists as `mr_description_checklists` (a list of `{title, items: [{label, checked}]}` objects) in the playbook evaluation result. The CI layer converts this list to Markdown checklists with H2 titles and appends it to the MR description.

### MR Templates

The `templates` list lets you define Cookiecutter templates that will be rendered directly into the Merge Request branch by the pipeline. This is useful for automatically generating boilerplate code, security compliance files, or evidence reports based on the analysis results.

Each item must have a `url` and an optional `condition`:

| Field       | Description                                                                                                                                              |
| :---------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`       | The HTTP URL or local path to a Cookiecutter template folder or repository.                                                                              |
| `directory` | If `url` points to an overarching Git repository containing multiple environments, this specifies the subdirectory containing the Cookiecutter template. |
| `condition` | A JSON Logic expression. If provided, the template is only evaluated and generated when the condition evaluates to truthy.                               |

```yaml
integrations:
  gitlab:
    templates:
      - url: "https://github.com/my-org/security-evidence-template"
        directory: "templates/my-evidence" # optional
        condition: { ">": [{ var: results.trivy.critical_count }, 0] }
```

:::warning
Because Cookiecutter ignores extra context variables that aren't defined in the template, your template's `cookiecutter.json` **must** include a `"regis"` property (even if it's just an empty object) to receive the analysis context:

```json
{
  "regis": {}
}
```

:::

During evaluation, templates whose condition passes are aggregated. The CLI then executes these templates with access to the full analysis context (e.g., `cookiecutter.regis.score`), and writes the generated files back to the current working directory so they can be committed to the MR branch.

## Creating a Custom Playbook

While you can write a playbook from scratch, the easiest way to start is by using the `bootstrap playbook` command. This creates a new directory with a pre-configured playbook template and all necessary files.

```bash
regis bootstrap playbook my-custom-playbook
```

This command will prompt you for basic information (name, slug, etc.) and generate a skeleton playbook that you can then customize with your own rules and scorecards. For more information, see the [Bootstrapping Reference](../reference/cli.md#bootstrap).

## Example Playbook

The following example shows a simplified playbook definition:

```yaml
name: Minimal Playbook
slug: minimal
pages:
  - title: Compliance Overview
    slug: index
    sections:
      - name: Security Checks
        scorecards:
          - name: no-root
            title: Image must not run as root
            condition:
              "!=": [{ var: results.skopeo.platforms.0.user }, root]
        widgets:
          - label: Compliance Level
            value: "{{ playbooks.0.score }}%"
```

:::tip
To see the full set of rules and report organization enforced by the tool out-of-the-box, check the [Default Playbook Reference](../reference/playbooks/default/index.md).
:::

## Local Evaluation (Dry-run)

When developing custom playbooks, you can evaluate them against existing analysis results without re-running the full image analysis. This is faster and doesn't require registry access once you have a base `report.json`.

Use the `evaluate` subcommand:

```bash
# 1. Run a full analysis once to get the raw data
regis analyze nginx:latest -o report.json

# 2. Iterate on your playbook locally
regis evaluate report.json -p my-playbook.yaml --site
```

The `evaluate` command supports most of the reporting options found in `analyze`, including `--site`, `--theme`, and `--output-dir`.
