# Commands

This page provides a reference for all commands available in the `regis` tool.

## Global Options

| Option          | Description                                                                                                                                                 |
| :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-v, --verbose` | Enable verbose (DEBUG) logging for troubleshooting. Also surfaces per-analyzer timing (`analyzer X finished in 1.42s`).                                     |
| `-q, --quiet`   | Suppress non-essential output (progress banners, per-analyzer ticks, report-written confirmations). Errors and analyzer failures still print. Useful in CI. |
| `--help`        | Show the help message and exit.                                                                                                                             |

`--verbose` and `--quiet` are mutually exclusive in effect: `--quiet` clamps the log level to `ERROR` regardless of `--verbose`.

## Core Commands

### `analyze`

Analyze a Docker image and evaluate playbooks.

```bash
regis analyze [OPTIONS] URL
```

_Selection options:_

- `-a, --analyzer NAME`: Run only the specified analyzer(s). Repeatable. Default: all.
- `--skip NAME`: Exclude the specified analyzer(s) from the run. Repeatable. Run `regis list` to see available names.
- `-p, --playbook PATH`: Path or URL to custom playbook YAML/JSON file(s). Repeatable. Falls back to the built-in default playbook when omitted.
- `--auth REGISTRY=USER:PASS`: Provide registry credentials. Repeatable.
- `--platform PLATFORM`: Target platform for multi-arch images (e.g. `linux/amd64`).

_Output options:_

- `-o, --output TEMPLATE`: Output filename template (e.g. `report.{format}`).
- `-D, --output-dir TEMPLATE`: Base directory template for output files (default: `reports/{registry}/{repository}/{digest}`).
- `-s, --site`: Generate the HTML report site.
- `--html`: Generate a self-contained single-file `report.html`.
- `--sections all|summary|<slugs>`: Sections to include in the HTML report. Only applies to `--html`.
- `--markdown`: Also emit a Markdown summary report (`report.md`).
- `--base-url PATH`: Base URL for the HTML report site (useful for GitHub/GitLab Pages or artifacts).
- `--open`: Open the HTML report in the default browser automatically.
- `--pretty/--no-pretty`: Pretty-print the JSON output (default: on).

_Evaluation options:_

- `--evaluate`: Run rules evaluation after analysis and add results to report.
- `--fail`: Fail command execution if any rule is breached.
- `--fail-level [info|warning|critical]`: Minimum rule level that triggers a command failure (default: critical).

_Performance / caching:_

- `--cache`: Use existing `report.json` as cache if available.
- `--max-workers INTEGER`: Maximum number of analyzers to run in parallel (default: 4).
- `-A, --archive DIR`: Append the report to an archive directory (writes `manifest.json` and `data.json`).

_Metadata:_

- `-m, --meta KEY=VALUE`: Arbitrary metadata. Supports dot notation (`ci.job_id=123`). Repeatable.
- `--merge-meta`: Merge `--meta` into existing metadata instead of replacing (only with `--rerun`).

_Re-running a single analyzer:_

- `--rerun NAME`: Re-run a single analyzer against an existing report (requires `--report`).
- `--report DIR`: Existing report directory to update (requires `--rerun`).

_Output style:_

While running, `analyze` prints one line per analyzer with elapsed time:

```text
  Running 8 analyzer(s) with 4 worker(s)...
  ✓ skopeo        (0.8s)
  ✓ metadata      (0.9s)
  ✓ trivy         (18.3s)
```

When `--playbook` is explicitly provided, a one-line summary is printed at the end:

```text
  Playbook · validation-import  12 rules · 10 passed · 2 failed (critical)
  ✗ [trivy.no-critical-cves]   2 critical CVEs found
  ✗ [freshness.max-age-days]   Image is 120 days old (max: 90)
```

All of this is silenced under `-q`/`--quiet`.

_Environment variables:_

The most frequently repeated `analyze` flags can be set via the environment. CLI flags always take precedence.

| Variable            | Equivalent flag    |
| :------------------ | :----------------- |
| `REGIS_PLAYBOOK`    | `-p, --playbook`   |
| `REGIS_PLATFORM`    | `--platform`       |
| `REGIS_OUTPUT`      | `-o, --output`     |
| `REGIS_OUTPUT_DIR`  | `-D, --output-dir` |
| `REGIS_MAX_WORKERS` | `--max-workers`    |

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
regis rules list [OPTIONS]
```

_Options:_

- `-r, --rules PATH`: Path to an optional `rules.yaml` file to merge overrides.
- `-f, --format [text|markdown]`: Output format (default: `text`).
- `-o, --output FILE`: Write the rules list to a file instead of stdout.
- `-D, --output-dir DIR`: Write one Markdown file per rule into this directory (markdown format only).
- `--index / --no-index`: Generate an `index.md` in the output directory (default: off).
- `--filter-level [info|warning|critical]`: Keep only rules at this level.
- `--filter-provider NAME`: Keep only rules whose provider matches (e.g. `trivy`, `hadolint`). Combine with `--filter-level` to AND the filters.

### `rules show`

Show the full definition of a specific rule.

```bash
regis rules show <slug> [OPTIONS]
```

_Options:_

- `-r, --rules PATH`: Path to an optional `rules.yaml` file to merge overrides.
- `-f, --format [json|yaml]`: Output format (default: `json`). YAML is rendered via `yaml.safe_dump` and is significantly easier to read for nested JSON Logic conditions.

### `rules evaluate`

Evaluate a regis JSON report against rules.

```bash
regis rules evaluate <report.json> [--rules playbook.yaml] [--fail] [--fail-level critical] [-o output.json]
```

## Playbook Commands

### `playbook validate`

Validate a playbook YAML/JSON file (or bundle directory) against the playbook JSON Schema without running a full image analysis. Closes the feedback loop when authoring playbooks.

```bash
regis playbook validate <PATH>
```

Exit code `0` on success, `1` on validation failure. Each violation is rendered as `<location>: <message>` on stderr (no raw `jsonschema` tracebacks). The location is the dot-joined `absolute_path` reported by `jsonschema` (e.g. `rules.2.level`), or `<root>` when the error is at the document root.

```text
$ regis playbook validate my-playbook.yaml
  ✓ my-playbook.yaml is valid.

$ regis playbook validate broken-playbook.yaml
  ✗ broken-playbook.yaml is invalid:
    - rules.2.level: 'high' is not one of ['info', 'warning', 'critical']
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

### `doctor`

Check whether all required external binaries (`trivy`, `skopeo`, `hadolint`, `dockle`) are available on `PATH` and print their versions. Useful when onboarding or diagnosing CI failures.

For each tool, the command prints the first line of `tool --version` verbatim — exact prefix/format depends on the tool. Missing tools are reported as `not found in PATH`.

```text
$ regis doctor
  ✓ trivy        Version: 0.50.1
  ✓ skopeo       skopeo version 1.14.0
  ✓ hadolint     Haskell Dockerfile Linter 2.12.0
  ✗ dockle       not found in PATH
```

Exit code `0` if every tool is found, `1` if any is missing.

### `version`

Display the current version of `regis`.
