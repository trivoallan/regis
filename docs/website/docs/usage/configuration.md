---
sidebar_position: 3
tags:
  - playbooks
  - analyzers
---

# Advanced Configuration

For more complex projects, `regis` can be configured using a dedicated YAML file or environment variables. Configuration lets you customize which [analyzers](../concepts/analyzers.md) to run and which [playbook](../concepts/playbooks.md) to evaluate.

## Configuration File

By default, `regis` searches for a `.regis.yaml` file in the root of your project.

```yaml
# .regis.yaml example
output_dir: ./reports
template: ./custom-theme.html.j2
playbook: ./security-policies.yaml

analyzers:
  cve:
    enabled: true
    severity: CRITICAL,HIGH
  hadolint:
    enabled: false
```

## Environment Variables

The most frequently repeated `regis analyze` flags can be set via the environment. CLI flags always take precedence over environment variables.

| Variable            | Equivalent flag                                                            |
| :------------------ | :------------------------------------------------------------------------- |
| `REGIS_PLAYBOOK`    | `-p, --playbook` — path or URL to a custom playbook.                       |
| `REGIS_PLATFORM`    | `--platform` — target platform for multi-arch images (e.g. `linux/amd64`). |
| `REGIS_OUTPUT`      | `-o, --output` — output filename template.                                 |
| `REGIS_OUTPUT_DIR`  | `-D, --output-dir` — base directory template for output files.             |
| `REGIS_MAX_WORKERS` | `--max-workers` — maximum number of analyzers to run in parallel.          |

## Managing the Cache

`regis` caches analyzer results to improve performance. You can control the cache behavior via:

```bash
regis analyze my-image --clear-cache
```

## Custom Output Paths

You can dynamically set the output filename using variables:

```bash
regis analyze my-image --output-path report-${DATE}.html
```

> [!TIP]
> Use `regis config --show` to see the currently active configuration, including all overrides.
