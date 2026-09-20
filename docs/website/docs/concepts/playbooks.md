---
sidebar_position: 3
tags:
  - playbooks
---

# Playbooks

Playbooks are the core of the `regis` evaluation engine. They define the security and compliance rules that the tool evaluates against container image metadata.

## Purpose

A playbook serves two primary functions:

1.  **Policy Enforcement**: It defines a set of rules that an image must pass to be considered compliant.
2.  **Report Structuring**: It controls what badges, tiers, and links appear in the generated report.

By using playbooks, you can decouple the raw data extraction (performed by analyzers like OCI or CVE) from the business logic used to evaluate that data. This allows you to apply different compliance standards to different environments or projects without changing the underlying analysis code.

## Playbook format

Playbooks use a Kubernetes-style resource envelope. Every `playbook.yaml` must declare these four top-level keys:

| Field        | Required | Description                                                           |
| ------------ | -------- | --------------------------------------------------------------------- |
| `apiVersion` | yes      | Must be `regis.io/v1alpha1`.                                          |
| `kind`       | yes      | Must be `Playbook`.                                                   |
| `metadata`   | yes      | Identity and version of this playbook (see below).                    |
| `spec`       | yes      | Rules, tiers, badges, presentation directives, and links (see below). |

### `metadata` fields

| Field                                          | Required | Description                                                                              |
| ---------------------------------------------- | -------- | ---------------------------------------------------------------------------------------- |
| `metadata.name`                                | yes      | Machine identifier — RFC 1123 DNS label (lowercase alphanumerics and `-`, max 63 chars). |
| `metadata.title`                               | no       | Human-readable display name shown in reports.                                            |
| `metadata.description`                         | no       | Human-readable description of what this playbook evaluates.                              |
| `metadata.labels["app.kubernetes.io/version"]` | yes      | SemVer of your playbook bundle (e.g. `"1.0.0"`). Bump when you change rules.             |
| `metadata.annotations`                         | no       | Free-form non-identifying metadata (arbitrary string key/value pairs).                   |

### `spec` fields

| Field               | Required | Description                                                                                                                                     |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `spec.tiers`        | no       | Compliance tier thresholds (Gold / Silver / Bronze).                                                                                            |
| `spec.rules`        | no       | Rules: bindings of a criterion (provider + criterion slug + options).                                                                           |
| `spec.badges`       | no       | Dynamic status badges displayed in the report header.                                                                                           |
| `spec.presentation` | no       | Platform-neutral presentation directives (badge labels, checklists, templates) consumed by integrations (e.g. GitLab MR, GitHub PR, Backstage). |
| `spec.links`        | no       | Custom action links displayed in the report.                                                                                                    |

### Field mapping from the legacy format

If you have an existing playbook that uses the old flat format, run:

```bash
regis playbook upgrade path/to/playbook.yaml
```

The mapping is:

| Legacy field                 | New location                                   |
| ---------------------------- | ---------------------------------------------- |
| `schemaVersion`              | replaced by `apiVersion`                       |
| `version`                    | `metadata.labels["app.kubernetes.io/version"]` |
| `name`                       | `metadata.title`                               |
| `slug`                       | `metadata.name`                                |
| `description`                | `metadata.description`                         |
| `tiers`                      | `spec.tiers`                                   |
| `rules`                      | `spec.rules`                                   |
| `badges`                     | `spec.badges`                                  |
| `integrations`               | `spec.presentation`                            |
| `links`                      | `spec.links`                                   |
| `pages`/`sections`/`sidebar` | removed (not used by the report viewer)        |

## Core Concepts

The following concepts are central to understanding and creating playbooks. For a complete technical reference of all available attributes, refer to the [Playbook Schema Reference](../reference/schemas/playbook/v1alpha1/playbook.schema.md).

### Tiers

Playbooks can define **Tiers** to categorize the overall quality of an image based on the compliance score. Each tier is defined by a name, a condition, and an optional `icon`.

```yaml
spec:
  tiers:
    - name: Gold
      icon: "🥇" # optional display icon (emoji)
      condition: { ">": [{ var: rules_summary.score }, 90] }
    - name: Silver
      icon: "🥈"
      condition: { ">": [{ var: rules_summary.score }, 70] }
    - name: Bronze
      icon: "🥉"
      condition: { ">": [{ var: rules_summary.score }, 50] }
```

The evaluator checks tiers in the order they are defined. The first tier whose condition evaluates to truthy is assigned to the report. The `icon` is surfaced in the analyze verdict block and reports; a tier without an `icon` renders with a neutral marker.

### Badges

**Badges** provide high-level visual status indicators in the report header. They are dynamic and support variable interpolation using the `${var.path}` syntax.

```yaml
spec:
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
{ "==": [{ "var": "results.cve.critical_count" }, 0] }
```

Or, to check the overall playbook score:

```json
{
  ">=": [{ "var": "playbooks.0.score" }, 90]
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
  value: "{{ playbooks.0.score }}%"
```

## Presentation Directives

`spec.presentation` defines platform-neutral directives that consuming integrations (GitLab MR, GitHub PR, Backstage, etc.) can render. The playbook engine evaluates these directives once and exposes the results in the report; each integration then decides how to surface them.

### Badge Labels

The `badge_labels` list specifies which badge slugs integrations should surface as status labels. Each slug must match a badge defined in `spec.badges`.

```yaml
spec:
  presentation:
    badge_labels:
      - score
      - freshness
      - cve-critical
```

Integrations use this list to keep their label surface (e.g. GitLab MR labels, GitHub PR labels) in sync with the badge values shown in the HTML report.

### Checklists

The `checklists` list adds configurable verification checklists to integration surfaces (e.g. the Merge Request or Pull Request description). Each checklist lets you define manual steps that reviewers must tick off before approving.

Each checklist can have a `title` and a list of `items`. Each item has a mandatory `label` and two optional conditions:

| Field      | Description                                                                                                                                                             |
| :--------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `show_if`  | A JSON Logic expression. If provided, the item is only added to the checklist when the expression evaluates to truthy. Items referencing unavailable data are excluded. |
| `check_if` | A JSON Logic expression. If provided and truthy, the checkbox renders pre-checked (`- [x]`). Otherwise it renders unchecked (`- [ ]`).                                  |

```yaml
spec:
  presentation:
    checklists:
      - title: 📝 Security Review
        items:
          - label: Security review completed # <1>
          - label: No critical vulnerabilities found
            show_if: { "==": [{ var: results.cve.critical_count }, 0] } # <2>
            check_if: { "==": [{ var: results.cve.critical_count }, 0] } # <3>
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

The engine exposes the resolved checklists as `checklists` (a list of `{title, items: [{label, checked}]}` objects) in the playbook evaluation result. Each integration converts this list to its native format — for example, a GitLab CI job appends them as Markdown checklists to the MR description.

### Templates

The `templates` list lets you define Cookiecutter templates that integrations can render into their target branch or workspace. This is useful for automatically generating boilerplate code, security compliance files, or evidence reports based on the analysis results.

Each item must have a `url` and an optional `condition`:

| Field       | Description                                                                                                                                              |
| :---------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`       | The HTTP URL or local path to a Cookiecutter template folder or repository.                                                                              |
| `directory` | If `url` points to an overarching Git repository containing multiple environments, this specifies the subdirectory containing the Cookiecutter template. |
| `condition` | A JSON Logic expression. If provided, the template is only evaluated and generated when the condition evaluates to truthy.                               |

```yaml
spec:
  presentation:
    templates:
      - url: "https://github.com/my-org/security-evidence-template"
        directory: "templates/my-evidence" # optional
        condition: { ">": [{ var: results.cve.critical_count }, 0] }
```

:::warning
Because Cookiecutter ignores extra context variables that aren't defined in the template, your template's `cookiecutter.json` **must** include a `"regis"` property (even if it's just an empty object) to receive the analysis context:

```json
{
  "regis": {}
}
```

:::

During evaluation, templates whose condition passes are aggregated and exposed as `templates` in the playbook result. Each integration then executes these templates with the full analysis context (e.g., `cookiecutter.regis.score`) and writes the generated files to the appropriate location.

## Bundle Structure

A playbook is a **directory** (bundle) rather than a single file. The bundle uses fixed filenames by convention:

```text
my-playbook/
├── playbook.yaml        # apiVersion/kind/metadata/spec envelope
├── meta.schema.json     # JSON Schema for --meta validation
└── README.md
```

You can pass a bundle directory anywhere a playbook path is accepted:

```bash
regis analyze myimage:latest --playbook ./my-playbook/
```

Legacy single-file playbooks using the old `schemaVersion`/`name` format are automatically upgraded on load. To migrate permanently, run:

```bash
regis playbook upgrade path/to/playbook.yaml
```

---

## Metadata

Playbooks can declare required and optional metadata fields that must be supplied by the project using `--meta KEY=VALUE` flags. Typical use cases: internal project identifiers, security validation document URLs, or compliance ticket references.

### Well-known fields

Regis ships with a base schema defining standard CI metadata fields:

| Field         | Type                     | Description           |
| ------------- | ------------------------ | --------------------- |
| `ci.platform` | `"github"` \| `"gitlab"` | CI platform           |
| `ci.job.id`   | `string`                 | CI job identifier     |
| `ci.job.url`  | `string` (URI)           | URL to the CI job run |

These fields are always recognized — no schema required to use them.

### Extending the schema

To declare project-specific required or optional fields, create a `meta.schema.json` inside the bundle that extends the well-known base via JSON Schema `allOf`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "allOf": [{ "$ref": "https://regis/schemas/meta/well-known.schema.json" }],
  "properties": {
    "PROJECT_ID": {
      "type": "string",
      "description": "Internal project identifier"
    },
    "SEC_DOC_URL": {
      "type": "string",
      "format": "uri",
      "description": "Link to security validation document"
    }
  },
  "required": ["PROJECT_ID"]
}
```

Missing required fields make the `metadata` analyzer report a validation failure, and `regis analyze` exits with code `3` — see [Consequences of an invalid field](#consequences-of-an-invalid-field). Optional fields that are not provided are recorded as `{"valid": true}` and do not fail the analysis.

### Supplying a schema outside a bundle

A schema does not have to live in a bundle. `--meta-schema` takes a path to a JSON Schema
file and can be repeated:

```bash
regis analyze myimage:latest \
  --playbook ./my-playbook/ \
  --meta-schema ./schemas/saisine.schema.json \
  -m SAISINE_URL=https://saisine.example/contester
```

Local paths only, JSON only. Every source in force stacks by `allOf`, in this order:

1. the well-known schema;
2. each `--playbook` bundle's `meta.schema.json`;
3. each `--meta-schema` path, in the order given.

A source can only **add** constraints. Passing your own schema cannot relax a requirement a
playbook declares, so a caller cannot disarm a playbook's regime.

The schemas actually loaded are recorded in the report under
`results.metadata.schema_sources`, so an auditor can tell which regime sealed a report — and
an empty list means no requirement was in force.

:::warning
A `--playbook` passed as a **file** (or a URL) cannot carry a `meta.schema.json`. When you
supply `--meta` and no schema can be loaded, regis warns on stderr and
`schema_sources` stays empty. Use a bundle directory or `--meta-schema` to make a
requirement enforceable.
:::

A schema that cannot be read or parsed aborts the analysis with exit code `1`. A broken
regime is not an absent regime.

### Consequences of an invalid field

There are two ways to require a metadata field, and they are complementary rather than
interchangeable:

|                   | Schema `required`                        | Playbook rule over `metadata.*`     |
| ----------------- | ---------------------------------------- | ----------------------------------- |
| Meaning           | the call is malformed                    | the absence is part of the verdict  |
| Exit code         | **3**, whether or not `--fail` is passed | **1**, with `--fail`                |
| Recorded in       | `results.metadata.metadata_validation`   | `rules`, `tier`, badges, checklists |
| Degrades the tier | no                                       | yes                                 |

Exit code `3` is deliberately not gated on `--fail`: `--fail` governs the verdict on the
_image_, and a malformed invocation is not a verdict. That is what lets a caller tell
"image refused by the rules" from "call missing a required field" without parsing the
report. The report is always written before the exit, so the failing fields are available
in `results.metadata.metadata_validation`.

Exit `3` applies only when a schema beyond the well-known one is in force. With no such
source, a violation of the well-known schema is recorded in the report and warned about on
stderr, leaving the exit code unchanged.

For a hard governance gate, use **both**: `required` in the schema so a missing field stops
the pipeline, and a rule over `metadata.*` so the report itself states the requirement. See
[Using metadata in rules, badges, and checklists](#using-metadata-in-rules-badges-and-checklists).

### Derogation: `--meta-advisory`

The party that ships a `meta.schema.json` and the party whose pipeline pays for a violation are
not always the same — a governance team may publish the bundle while a caller only consumes it.
For that caller, `--meta-advisory` (or `REGIS_META_ADVISORY=1`) suspends the sanction **without
suspending the finding**:

```bash
regis analyze myimage:latest -p ./regime/ --meta-advisory -m PROJECT_ID=PROJ-42
# exit 0, and the report still says what is missing
```

What it changes and what it does not:

|                                        | Enforcing (default) | `--meta-advisory`                             |
| -------------------------------------- | ------------------- | --------------------------------------------- |
| Exit code on a violation               | `3`                 | `0`                                           |
| `results.metadata.valid`               | `false`             | `false` — unchanged                           |
| `results.metadata.metadata_validation` | names the fields    | names the fields — unchanged                  |
| `results.metadata.enforcement`         | `"enforcing"`       | `"advisory"`                                  |
| Warning on stderr                      | error, then exit    | warning, **not silenced by `--quiet`**        |
| A rule breach with `--fail`            | `1`                 | `1` — the derogation never covers the verdict |

The derogation is recorded in the report, not just in the command line, so a downstream
orchestrator reading a stored report sees that it was used and **can refuse it**:

```bash
jq -e '.results.metadata.enforcement == "enforcing"' report.json
```

Use it to cross a migration, or when you do not own the schema that constrains you — not as a
standing setting. It is a documented derogation, which is why it leaves a trace.

### Supplying metadata

Pass metadata at analysis time using `--meta`:

```bash
regis analyze myimage:latest \
  --playbook ./my-playbook/ \
  -m PROJECT_ID=PROJ-42 \
  -m SEC_DOC_URL=https://jira.example.com/browse/SEC-99 \
  -m ci.platform=github
```

Metadata is stored in the report under the top-level `metadata` namespace, making it accessible in all rule conditions, badges, and template expressions (for example `{"var": "metadata.ci.platform"}`).

### Deferred metadata (--rerun)

Metadata is often not available at analysis time — for example, the security validation document URL is only known after a parallel approval process completes. You can re-inject metadata without re-running the full image analysis:

```bash
# Day 1: full analysis (PROJECT_ID not yet known)
regis analyze myimage:latest --playbook ./my-playbook/

# Day N: once the project ID is confirmed
regis analyze --rerun metadata \
  --report ./reports/registry/repo/digest/ \
  -m PROJECT_ID=PROJ-42 \
  -m SEC_DOC_URL=https://jira.example.com/browse/SEC-99
```

The `--rerun` path updates `report.json` in place and replays the full playbook evaluation (rules → tiers → badges) against the patched data. It enforces the same schemas — pass the same `--playbook` and `--meta-schema` as the original run — and exits `3` the same way when a required field is still missing.

### Using metadata in rules, badges, and checklists

Metadata values are accessible under `metadata.*` via JSON Logic `var`:

**Rule — require PROJECT_ID before granting a compliance tier:**

```yaml
spec:
  rules:
    - provider: metadata
      criterion: metadata
      slug: project-registered
      level: critical
      condition:
        "!!": [{ var: "metadata.PROJECT_ID" }]
      messages:
        pass: "Project ID provided: ${metadata.PROJECT_ID}"
        fail: "PROJECT_ID is required for compliance reporting"
```

**Badge — display the project ID:**

```yaml
spec:
  badges:
    - slug: project-id
      scope: Project
      value: "${metadata.PROJECT_ID}"
      condition:
        "!!": [{ var: "metadata.PROJECT_ID" }]
      class: information
```

**Presentation checklist — link to the security document:**

```yaml
spec:
  presentation:
    checklists:
      - title: 📋 Security Evidence
        items:
          - label: Security validation document submitted
            show_if: { "!!": [{ var: "metadata.SEC_DOC_URL" }] }
            check_if: { "!!": [{ var: "metadata.SEC_DOC_URL" }] }
          - label: "Review document: ${metadata.SEC_DOC_URL}"
            show_if: { "!!": [{ var: "metadata.SEC_DOC_URL" }] }
```

**Tier condition — gate Gold tier on CI platform:**

```yaml
spec:
  tiers:
    - name: Gold
      condition:
        and:
          - { ">": [{ var: rules_summary.score }, 90] }
          - { "==": [{ var: "metadata.ci.platform" }, "github"] }
```

---

## Creating a Custom Playbook

While you can write a playbook from scratch, the easiest way to start is by using the `bootstrap playbook` command. This creates a new directory with a pre-configured playbook template and all necessary files.

```bash
regis bootstrap playbook my-custom-playbook
```

This command will prompt you for basic information (name, slug, etc.) and generate a skeleton playbook that you can then customize with your own rules and scorecards. For more information, see the [Bootstrapping Reference](../reference/cli.md#bootstrap).

## Example Playbook

The following example shows a minimal valid playbook definition:

```yaml
# yaml-language-server: $schema=https://trivoallan.github.io/regis/schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.io/v1alpha1
kind: Playbook
metadata:
  name: minimal
  title: Minimal Playbook
  labels:
    app.kubernetes.io/version: "1.0.0"
spec:
  tiers:
    - name: Gold
      condition: { ">": [{ var: rules_summary.score }, 90] }
    - name: Silver
      condition: { ">": [{ var: rules_summary.score }, 70] }
    - name: Bronze
      condition: { ">": [{ var: rules_summary.score }, 50] }
  rules:
    - provider: oci
      criterion: user-blacklist
      slug: no-root
      level: critical
      options:
        blacklist: [root, "0"]
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
regis evaluate report.json -p my-playbook.yaml --html
```

The `evaluate` command supports most of the reporting options found in `analyze`, including `--html` and `--output-dir`.
