# Default Regis Playbook

The built-in playbook applied automatically when no `--playbook` flag is provided.

## Metadata

No metadata is required by default. To add project-specific metadata requirements, copy this bundle and extend `meta.schema.json`.

### Well-known fields

| Field         | Type                 | Description           |
| ------------- | -------------------- | --------------------- |
| `ci.platform` | `github` \| `gitlab` | CI platform           |
| `ci.job.id`   | string               | CI job identifier     |
| `ci.job.url`  | URI                  | URL to the CI job run |
