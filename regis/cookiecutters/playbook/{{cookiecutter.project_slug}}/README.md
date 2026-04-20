# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Metadata

This playbook accepts metadata via `--meta` flags. Edit `meta.schema.json` to define required and optional fields.

### Well-known fields

| Field          | Type                  | Description            |
| -------------- | --------------------- | ---------------------- |
| `ci.platform`  | `github` or `gitlab`  | CI platform            |
| `ci.job.id`    | string                | CI job identifier      |
| `ci.job.url`   | URI                   | URL to the CI job run  |

### Usage

```bash
# Full analysis
regis analyze myimage:latest --playbook ./ -m ci.platform=github

# Re-run metadata validation after adding project metadata
regis analyze --rerun metadata --report ./reports/ -m PROJECT_ID=PROJ-42
```

## Rules

See `playbook.yaml` for rule definitions.
