# Commands

This page provides a reference for all commands available in the `regis` tool.

## Global Options

| Option          | Description                                         |
| :-------------- | :-------------------------------------------------- |
| `-v, --verbose` | Enable verbose (DEBUG) logging for troubleshooting. |
| `--help`        | Show the help message and exit.                     |

## Core Commands

### `analyze`

Analyze a Docker image and evaluate playbooks.

```bash
regis analyze [OPTIONS] URL
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
regis archive add REPORT_PATH --archive-dir DIR
```

### `evaluate`

Evaluate playbooks against an existing analysis report (dry-run).

```bash
regis evaluate [OPTIONS] INPUT_PATH
```

_Options:_

- `-p, --playbook PATH`: Path or URL to custom playbook YAML/JSON file(s).
- `-s, --site`: Generate HTML report site.
- `--base-url PATH`: Base URL for the HTML report site.
- `--open`: Open the HTML report in the default browser automatically.

### `check`

Check if an image manifest is accessible on the registry.

```bash
regis check [OPTIONS] URL
```

## Rules Commands

Manage and evaluate rules against reports.

### `rules list`

List all available default rules provided by analyzers, and optionally merge with overrides.

```bash
regis rules list [--rules playbook.yaml]
```

### `rules show`

Show the full JSON definition of a specific rule.

```bash
regis rules show <slug> [--rules rules.yaml]
```

### `rules evaluate`

Evaluate a regis JSON report against rules.

```bash
regis rules evaluate <report.json> [--rules playbook.yaml] [--fail] [--fail-level critical] [-o output.json]
```

## Viewer Commands

Manage and serve the interactive dashboard.

### `dashboard serve`

Serve the static React viewer and preview a report locally.

```bash
regis dashboard serve [OPTIONS] [REPORT]
```

_Options:_

- `-p, --port INTEGER`: Port to listen on (default: `8000`).

### `dashboard export`

Export the viewer app alongside a target report for static hosting.

```bash
regis dashboard export [OPTIONS] [REPORT]
```

_Options:_

- `-o, --output PATH`: **(Required)** Directory to export the static site into.

## Project Bootstrapping {#bootstrap}

### `bootstrap playbook`

Bootstrap a new custom RegiS playbook from a template.

```bash
regis bootstrap playbook [OUTPUT_DIR] [--no-input]
```

### `bootstrap archive`

Bootstrap a standalone archive viewer site for browsing and filtering historical regis reports. The generated site is built with Docusaurus and Tremor, deploys to [GitHub Pages or GitLab Pages](../usage/integrations/), and exposes a PowerBI-compatible JSON endpoint.

```bash
regis bootstrap archive [OUTPUT_DIR] [OPTIONS]
```

_Options:_

| Option                        | Default                            | Description                                                                                                                                          |
| :---------------------------- | :--------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--no-input`                  | `False`                            | Skip cookiecutter prompts; use template defaults.                                                                                                    |
| `--platform [github\|gitlab]` | _(prompt)_                         | Target platform. Skips the cookiecutter platform prompt.                                                                                             |
| `--dev`                       | `False`                            | After scaffolding, run `pnpm install` and start the local dev server.                                                                                |
| `--port INTEGER`              | `3000`                             | Port for the dev server (only with `--dev`).                                                                                                         |
| `--repo`                      | `False`                            | After scaffolding, create a remote repository and enable Pages.                                                                                      |
| `--repo-name TEXT`            | project slug                       | Name of the remote repository (only with `--repo`).                                                                                                  |
| `--public / --private`        | public (GitHub) / private (GitLab) | Repository visibility (only with `--repo`).                                                                                                          |
| `--org TEXT`                  | _(current user)_                   | Organisation or GitLab group (only with `--repo`).                                                                                                   |
| `--sync-from PATH`            | —                                  | Sync UI changes from a working copy back to the cookiecutter template. See [Customizing the Archive UI](../usage/integrations/archive-customize.md). |

`--dev` and `--repo` are mutually exclusive.

**`--dev` mode** — local iteration without a remote repository:

```bash
regis bootstrap archive ./my-archive --no-input --dev
# Scaffolds, runs pnpm install, starts http://localhost:3000
```

**`--repo` mode** — full remote setup:

1. Checks that `pnpm`, `git`, and `gh` / `glab` are available and authenticated.
2. Scaffolds the archive site.
3. Runs `pnpm install`.
4. Creates an initial git commit.
5. Creates the remote repository (`gh repo create` or `glab repo create`).
6. Enables GitHub Pages in workflow mode (GitHub only; GitLab Pages activates via the `pages` job).
7. Prints the expected Pages URL and the command to add your first report.

```bash
regis bootstrap archive ./my-archive --repo --platform github --no-input
```

:::tip
If the remote repository already exists (for example after a failed first attempt), the creation step is skipped and the code is pushed to the existing repository.
:::

:::note
After a successful bootstrap, all `bootstrap` commands display **Post-install notes** from the template (and then remove the temporary `.regis-post-install.md` file). These notes contain setup instructions for GitHub/GitLab and next steps.
:::

## Utility Commands

### `github`

Commands for seamless integration with GitHub Actions.

- `github update-pr`: Post or update a Pull Request comment with analysis results, score, and report link. Applies playbook labels to the PR.

### `gitlab`

Commands for seamless integration with GitLab CI/CD.

- `gitlab create-request`: Create a Merge Request comment with analysis status.
- `gitlab update-mr`: Update Merge Request with final results and labels.

### `list`

List all available analyzers (e.g., `skopeo`, `trivy`, `hadolint`).

### `version`

Display the current version of `regis`.
