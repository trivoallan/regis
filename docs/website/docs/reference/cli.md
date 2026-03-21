# Commands

This page provides a reference for all commands available in the `regis-cli` tool.

## Global Options

| Option          | Description                                         |
| :-------------- | :-------------------------------------------------- |
| `-v, --verbose` | Enable verbose (DEBUG) logging for troubleshooting. |
| `--help`        | Show the help message and exit.                     |

## Core Commands

### `analyze`

Analyze a Docker image and evaluate playbooks.

```bash
regis-cli analyze [OPTIONS] URL
```

_Options:_

- `-p, --playbook PATH`: Path or URL to custom playbook YAML/JSON file(s).
- `-s, --site`: Generate HTML report site.
- `--auth REGISTRY=USER:PASS`: Provide registry credentials.
- `--cache`: Use existing report.json as cache if available.
- `-o, --output TEMPLATE`: Output filename template.
- `-D, --output-dir TEMPLATE`: Base directory template for output files.
- `--evaluate`: Run rules evaluation after analysis and add results to report.
- `--fail`: Fail command execution if any rule is breached.
- `--fail-level [info|warning|critical]`: Minimum rule level that triggers a command failure (default: critical).
- `--base-url PATH`: Base URL for the HTML report site (useful for GitHub/GitLab Pages or artifacts).
- `--open`: Open the HTML report in the default browser automatically.
- `-A, --archive DIR`: Append the report to an archive directory (writes `manifest.json` and `data.json`).

### `archive add`

Add an existing `report.json` to an archive directory.

```bash
regis-cli archive add REPORT_PATH --archive-dir DIR
```

### `evaluate`

Evaluate playbooks against an existing analysis report (dry-run).

```bash
regis-cli evaluate [OPTIONS] INPUT_PATH
```

_Options:_

- `-p, --playbook PATH`: Path or URL to custom playbook YAML/JSON file(s).
- `-s, --site`: Generate HTML report site.
- `--base-url PATH`: Base URL for the HTML report site.
- `--open`: Open the HTML report in the default browser automatically.

### `check`

Check if an image manifest is accessible on the registry.

```bash
regis-cli check [OPTIONS] URL
```

## Rules Commands

Manage and evaluate rules against reports.

### `rules list`

List all available default rules provided by analyzers, and optionally merge with overrides.

```bash
regis-cli rules list [--rules playbook.yaml]
```

### `rules show`

Show the full JSON definition of a specific rule.

```bash
regis-cli rules show <slug> [--rules rules.yaml]
```

### `rules evaluate`

Evaluate a regis-cli JSON report against rules.

```bash
regis-cli rules evaluate <report.json> [--rules playbook.yaml] [--fail] [--fail-level critical] [-o output.json]
```

## Project Bootstrapping {#bootstrap}

### `bootstrap playbook`

Bootstrap a new custom RegiS playbook from a template.

```bash
regis-cli bootstrap playbook [OUTPUT_DIR] [--no-input]
```

### `bootstrap archive`

Bootstrap a standalone archive viewer site for browsing and filtering historical regis-cli reports. The generated site is built with Docusaurus and Tremor, deploys to GitHub Pages or GitLab Pages, and exposes a PowerBI-compatible JSON endpoint.

```bash
regis-cli bootstrap archive [OUTPUT_DIR] [--no-input]
```

:::note
After a successful bootstrap, all `bootstrap` commands display **Post-install notes** from the template (and then remove the temporary `.regis-post-install.md` file). These notes contain setup instructions for GitHub/GitLab and next steps.
:::

## Utility Commands

### `gitlab`

Commands for seamless integration with GitLab CI/CD.

- `gitlab create-request`: Create a Merge Request comment with analysis status.
- `gitlab update-mr`: Update Merge Request with final results and labels.

### `list`

List all available analyzers (e.g., `skopeo`, `trivy`, `hadolint`).

### `version`

Display the current version of `regis-cli`.
