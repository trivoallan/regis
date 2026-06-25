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
- `--html`: Generate a self-contained single-file `report.html`.
- `--sections all|summary|<slugs>`: Sections to include in the HTML report. Only applies to `--html`.
- `--markdown`: Also emit a Markdown summary report (`report.md`).
- `--sarif`: Also emit a SARIF report of playbook verdicts (`report.sarif`) for upload to GitHub Code Scanning (or any SARIF consumer). Each breached rule becomes a SARIF result anchored at the `Dockerfile`, with a `security-severity` mapped from the rule level and a `helpUri` to the criterion's docs. A clean run (rules evaluated, no breach) instead emits a single `kind: "pass"` receipt carrying the image digest, so "evaluated and clean" stays distinguishable from "never analyzed" — an empty run means the image was not governed. The receipt also carries a `ruleset_hash` — a tamper-evident `sha256` fingerprint of the resolved, enforced ruleset (thresholds included) — so a consumer can pin the expected playbook and reject a receipt produced against a loosened or swapped one.
- `--pretty/--no-pretty`: Pretty-print the JSON output (default: on).

_Evaluation options:_

- `--evaluate`: Run rules evaluation after analysis and add results to report.
- `--fail`: Fail command execution if any rule is breached.
- `--fail-level [info|warning|critical]`: Minimum rule level that triggers a command failure (default: critical).

_Performance / caching:_

- `--cache`: Use existing `report.json` as cache if available.
- `--max-workers INTEGER`: Maximum number of analyzers to run in parallel (default: 4).

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
  ✓ oci           (0.8s)
  ✓ metadata      (0.9s)
  ✓ cve           (18.3s)
```

At the end of every run, a **verdict block** summarizes the playbook evaluation — the achieved tier and score, a counts line, the resolved badges, and any failed or incomplete rules:

```text
  🥈 Silver · 78/100
  17/20 rules · 2 failed · 1 incomplete · worst: 🟧 warning
  🟥 CVE: Critical   🟧 CVE: High
  ✗ [cve-critical]    1 critical CVE (max 0)
  ✗ [cve-high]        12 high CVEs (max 10)
  ⚠ [scorecard-min]   OpenSSF Scorecard data unavailable
```

The tier headline (`🥈 Silver`) is data-driven: each tier in a playbook may declare an optional `icon`; tiers without one render with a neutral `🏷️` marker, and a run that meets no tier shows `⚪ Unrated`. Severity uses colored squares (`🟥` critical/error, `🟧` warning, `🟩`/`🟦` success/info) so they never read as tier medals. When all rules pass, the counts line collapses to `N/N rules · all pass ✓`.

The verdict block is written to stderr and shown by default. The same verdict header is prepended to the `--markdown` report and rendered as a panel at the top of the `--html` report. All of this is silenced under `-q`/`--quiet`.

_Environment variables:_

The most frequently repeated `analyze` flags can be set via the environment. CLI flags always take precedence.

| Variable            | Equivalent flag    |
| :------------------ | :----------------- |
| `REGIS_PLAYBOOK`    | `-p, --playbook`   |
| `REGIS_PLATFORM`    | `--platform`       |
| `REGIS_OUTPUT`      | `-o, --output`     |
| `REGIS_OUTPUT_DIR`  | `-D, --output-dir` |
| `REGIS_MAX_WORKERS` | `--max-workers`    |

### `evaluate`

Evaluate playbooks against an existing analysis report (dry-run).

```bash
regis evaluate [OPTIONS] INPUT_PATH
```

_Options:_

- `-p, --playbook PATH`: Path or URL to custom playbook YAML/JSON file(s).
- `--html`: Generate a self-contained single-file `report.html`.
- `--sarif`: Also emit a SARIF report of playbook verdicts (`report.sarif`).

### `check`

Check if an image manifest is accessible on the registry.

```bash
regis check [OPTIONS] URL
```

## Rules Commands

Manage and evaluate rules against reports.

### `rules list`

List the available criteria catalogue (the reusable criterion templates you can bind from a playbook), and optionally merge with overrides.

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
- `--filter-provider NAME`: Keep only rules whose provider matches (e.g. `cve`, `hadolint`). Combine with `--filter-level` to AND the filters.

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

## Project Bootstrapping {#bootstrap}

### `bootstrap playbook`

Bootstrap a new custom RegiS playbook from a template.

```bash
regis bootstrap playbook [OUTPUT_DIR] [--no-input]
```

### `bootstrap tools`

Pre-warm the local analyzer-tools cache by fetching the scanner binaries pinned in the manifest (`grype`, `syft`, `trufflehog`, `regctl`, `dockle`, `hadolint`). Each download is verified against its pinned sha256 (and cosign signature when available) before being moved into the cache.

```bash
regis bootstrap tools [--check]
```

Use `--check` to print the cache state without fetching anything — handy in CI to decide whether to restore a cache key.

```text
$ regis bootstrap tools --check
  ⏩ grype        0.112.0    not cached (will fetch on first use)
  ⏩ syft         1.44.0     not cached (will fetch on first use)
  ⏩ trufflehog   3.95.3     not cached (will fetch on first use)
  ⏩ regctl       0.11.5     not cached (will fetch on first use)
  ⏩ dockle       0.4.15     not cached (will fetch on first use)
  ⏩ hadolint     2.12.0     not cached (will fetch on first use)

$ regis bootstrap tools
  ✓ grype        -> /home/regis/.cache/regis/tools/grype/0.112.0/linux-amd64/grype
  ✓ syft         -> /home/regis/.cache/regis/tools/syft/1.44.0/linux-amd64/syft
  ...
```

See [Managing Analyzer Tools](../usage/tools-management.md) for cache location, mirror configuration, air-gapped workflows, and signature verification.

:::note
After a successful bootstrap, all `bootstrap` commands display **Post-install notes** from the template (and then remove the temporary `.regis-post-install.md` file). These notes contain setup instructions and next steps.
:::

## Utility Commands

### `list`

List all available analyzers (e.g., `oci`, `cve`, `hadolint`).

### `doctor`

Check whether all required external binaries (`grype`, `syft`, `trufflehog`, `regctl`, `hadolint`, `dockle`) are available on `PATH` and print their versions. Useful when onboarding or diagnosing CI failures.

For each tool, the command prints the first line of `tool --version` verbatim — exact prefix/format depends on the tool. Missing tools are reported as `not found in PATH`.

```text
$ regis doctor
  ✓ grype        grype 0.74.0
  ✓ syft         syft 1.0.0
  ✓ trufflehog   trufflehog 3.63.0
  ✓ regctl       regctl version v0.7.1
  ✓ hadolint     Haskell Dockerfile Linter 2.12.0
  ✗ dockle       not found in PATH
```

Exit code `0` if every tool is found, `1` if any is missing.

A second **Tools (manifest)** section then reports the state of each scanner in the local cache populated by `regis bootstrap tools`:

```text
  Tools (manifest)
  ✓ grype        0.112.0    cached
  ⏩ syft         1.44.0     not cached (will fetch on first use)
  ✗ trufflehog   3.95.3     sha mismatch — re-run `regis bootstrap tools`
```

See [Managing Analyzer Tools](../usage/tools-management.md) for details on the cache layout and how to pre-warm it.

### `version`

Display the current version of `regis`.
