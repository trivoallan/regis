---
tags:
  - playbooks
  - analyzers
---

# Advanced Configuration

For more complex projects, `regis-cli` can be configured using a dedicated YAML file or environment variables.

## Configuration File

By default, `regis-cli` searches for a `.regis.yaml` file in the root of your project.

```yaml
# .regis.yaml example
output_dir: ./reports
template: ./custom-theme.html.j2
playbook: ./security-policies.yaml

analyzers:
  trivy:
    enabled: true
    severity: CRITICAL,HIGH
  hadolint:
    enabled: false
```

## Environment Variables

All configuration options can be overridden using environment variables prefixed with `REGIS_`.

- `REGIS_PLAYBOOK`: Path to the default playbook.
- `REGIS_OUTPUT_DIR`: Where to save reports.
- `REGIS_LOG_LEVEL`: Set to `DEBUG` for troubleshooting.

## Managing the Cache

`regis-cli` caches analyzer results to improve performance. You can control the cache behavior via:

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
