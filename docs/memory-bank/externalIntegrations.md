# External Integrations

## Third-Party APIs

| Service        | Purpose                             | Auth Method                      | Docs                                   |
| -------------- | ----------------------------------- | -------------------------------- | -------------------------------------- |
| GitLab API     | GitLab CI and MR support            | Token-based / python-gitlab      | <https://python-gitlab.readthedocs.io> |
| OCI registries | Image metadata and analysis targets | Registry auth / anonymous access | OCI-compliant registry APIs            |
| endoflife.date | Base image lifecycle checks         | None / HTTP                      | <https://endoflife.date>               |
| GitHub Actions | CI/CD workflows and artifacts       | GitHub App tokens                | GitHub workflow docs                   |

## Webhooks

| Webhook                      | Direction         | Trigger                        | Endpoint                          |
| ---------------------------- | ----------------- | ------------------------------ | --------------------------------- |
| GitLab MR-related automation | Incoming/outgoing | CI and merge request workflows | Not documented in inspected files |

## Service Contracts

- Registry and CI integrations rely on external tool behavior and API compatibility
- Some analyzers require binaries such as `grype`, `syft`, `trufflehog`, `regctl`, `hadolint`, and `dockle`

## Integration Patterns

- Mostly synchronous CLI and workflow integrations
- Tool availability is validated at runtime for some analyzers
- CI artifacts are emitted for consumption by users and downstream automation

## Environment-Specific Config

- GitHub App authentication is used in workflows
- CI secrets referenced in workflows should remain outside the Memory Bank
