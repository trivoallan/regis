---
sidebar_position: 4
---

# Understand Rules

RegiS evaluates the security and compliance of Docker images through a robust rules engine. Rules define specific conditions that the analysis results must meet.

## Default Analyzer Rules

To provide immediate value out of the box, each analyzer (like Trivy, Dockle, or Skopeo) provides its own built-in default rules. When you run an analysis, `regis-cli` automatically collects the default rules for all analyzers that were executed.

- `trivy-no-critical`: Fails if Trivy finds any critical vulnerabilities.
- `dockle-no-fatal`: Fails if Dockle finds fatal issues.
- `skopeo-no-root`: Fails if the image is configured to run as root.
- `trusted-domain`: Fails if the image does not originate from a trusted registry registry.

You can view all available default rules by running:

```bash
regis-cli rules list
```

To see the exact definition and JSON Logic of a specific rule:

```bash
regis-cli rules show trivy-no-critical
```

## Customizing Rules

You can customize or completely replace default rules by defining a `rules` section at the top level of your `playbook.yaml`. The rules engine matches these overrides based on their `slug`.

If you define a rule with the same `slug` as a default rule, your definition will be merged over the default one. You can use this to change the severity level, customize messages, or tweak parameters.

### Example Playbook with Rules

```yaml
name: Custom Security Playbook
rules:
  # Overriding a default rule
  - slug: trivy-no-critical
    title: Custom rules for critical CVEs
    level: warning # Demoting from critical to warning
    messages:
      fail: We found ${results.trivy.critical_count} critical CVEs, please fix them soon!

  # Adding a completely new custom rule
  - slug: company-specific-label
    title: Image must have company label
    level: critical
    tags: [compliance]
    condition:
      "in":
        [
          "my-company.owner",
          { "keys": [{ "var": "results.skopeo.platforms.0.labels" }] },
        ]
    messages:
      pass: "Company label is present."
      fail: "Missing 'my-company.owner' label."

  # Disabling a default rule entirely
  - slug: dockle-no-fatal
    enable: false
```

### Overriding Rule Parameters

Many default rules expose configurable `params` that you can override without rewriting the entire `condition`. The rule engine automatically merges your parameters with the defaults.

#### Common Parameter Examples

```yaml
rules:
  # Change freshness threshold
  - slug: freshness-age
    params:
      max_days: 7

  # Allow some critical CVEs if necessary
  - slug: trivy-no-critical
    params:
      max_count: 5

  # Change the forbidden user
  - slug: skopeo-no-root
    params:
      forbidden_user: "admin"

  # Restrict to specific trusted domains
  - slug: trusted-domain
    params:
      domains: ["my-private-registry.com"]
```

The rule engine applying them to the rule's built-in evaluation condition and output messages using the `${rule.params.key}` interpolation syntax.

## Standard Rule Library

RegiS includes a set of standard rules out-of-the-box. Below are the most common rules and their configurable parameters.

### Security Rules (Trivy & Dockle)

| Slug                  | Description                                    | Default Parameters       |
| :-------------------- | :--------------------------------------------- | :----------------------- |
| `trivy-no-critical`   | Fails if critical vulnerabilities are found.   | `max_count: 0`           |
| `trivy-no-high`       | Fails if high vulnerabilities are found.       | `max_count: 0`           |
| `trivy-fix-available` | Fails if vulnerabilities have a fixed version. | `min_severity: "MEDIUM"` |
| `trivy-secret-scan`   | Fails if embedded secrets are detected.        | None                     |
| `dockle-no-fatal`     | Fails if Dockle finds fatal issues.            | `max_count: 0`           |
| `dockle-max-warnings` | Limit the number of Dockle warnings.           | `max_count: 5`           |

### Image Hygiene & Config (Skopeo)

| Slug                     | Description                               | Default Parameters                            |
| :----------------------- | :---------------------------------------- | :-------------------------------------------- |
| `skopeo-no-root`         | Fails if image runs as a forbidden user.  | `forbidden_user: "root"`                      |
| `skopeo-max-size`        | Limit uncompressed image size.            | `max_mb: 1000`                                |
| `skopeo-max-layers`      | Limit number of filesystem layers.        | `max_layers: 30`                              |
| `skopeo-tag-not-latest`  | Enforce specific tags (blocks `latest`).  | None                                          |
| `skopeo-multi-arch`      | Ensure multi-platform support.            | `min_platforms: 2`                            |
| `skopeo-exposed-ports`   | Restrict permitted exposed ports.         | `allowed_ports: [80, 443]`                    |
| `skopeo-required-labels` | Ensure mandatory OCI/custom labels exist. | `labels: ["org.opencontainers.image.source"]` |
| `skopeo-forbidden-env`   | Guard against forbidden environment keys. | `keys: ["DEBUG", "SECRET_KEY"]`               |

### Lifecycle Rules

- `freshness-age`: Fails if the image is older than `max_days` (default: 30).
- `trusted-domain`: Restricts image origin to a list of `domains`.

## Rule Evaluation Mechanism

Rules are evaluated using **JSON Logic**. The evaluation context provides access to the flattened report data.

### String Interpolation

Rule messages (`pass` and `fail`) support string interpolation using the `${path.to.var}` syntax. These paths correspond to the flattened keys in the analysis report.

```yaml
messages:
  pass: Image is less than 30 days old (${results.freshness.age_days} days).
  fail: Image is older than 30 days (${results.freshness.age_days} days).
```

### Evaluating Rules

To evaluate an analysis report against your rules:

```bash
regis-cli rules evaluate path/to/report.json --rules playbook.yaml
```

:::note
The `--rules` (or `-r`) flag accepts both standalone `rules.yaml` files and full `playbook.yaml` files.
:::

The output will display a score percentage and the pass/fail status of each rule. You can also export the results to JSON using `-o rules_report.json`.

### CI/CD Integration

Use the `--fail` flag to automatically exit with a non-zero code if critical rules fail, which is useful for blocking CI/CD pipelines:

```bash
# Fail if any CRITICAL rule is breached
regis-cli rules evaluate <report.json> [--rules playbook.yaml] [--fail] [--fail-level critical]

# Fail if any WARNING or CRITICAL rule is breached
regis-cli rules evaluate report.json --rules playbook.yaml --fail --fail-level warning
```
