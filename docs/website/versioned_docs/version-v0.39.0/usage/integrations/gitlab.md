# GitLab CI

## Reusable GitLab CI template

GitLab integration ships as a reusable CI template from its own repository,
[`trivoallan/regis-gitlab`](https://github.com/trivoallan/regis-gitlab), versioned
independently from the Regis core.

```yaml
include:
  - remote: "https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml"

variables:
  REGIS_IMAGE: ghcr.io/trivoallan/regis:latest
  REGIS_PLAYBOOK: playbook.yaml
```

:::note Migrating from the built-in commands
The `regis gitlab` commands and the `regis bootstrap gitlab-ci` scaffolder were
removed from the core. The reusable template at
[`trivoallan/regis-gitlab`](https://github.com/trivoallan/regis-gitlab) replaces
them; it posts the MR comment, labels, and checklist itself.
:::
