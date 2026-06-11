# Security

## Authentication

- GitHub App authentication is used in CI workflows
- GitLab integration likely relies on token-based access through `python-gitlab`

## Authorization

| Role        | Permissions                                 | Notes                                   |
| ----------- | ------------------------------------------- | --------------------------------------- |
| Maintainer  | Full repository and workflow access         | Assumed from normal project operations  |
| Contributor | PR-level contribution and local development | Assumed from open-source style workflow |

## Security Policies

- `pip-audit` is enforced in CI with a HIGH/CRITICAL gate
- Provenance attestation is generated for release artifacts
- SBOM artifacts are produced in release/CD workflows
- Renovate-related workflow behavior (automerge, autorebase exclusion) is handled carefully in CI

## Vulnerability Tracking

| Issue                      | Severity | Status          | Notes                   |
| -------------------------- | -------- | --------------- | ----------------------- |
| Dependency vulnerabilities | Varies   | Mitigated in CI | Enforced via audit gate |

## Secrets Management

- Secrets are stored in CI secret stores and referenced by workflow variables
- No actual secret values are recorded in the Memory Bank

## Compliance

- Supply-chain integrity practices are present
- No formal regulatory compliance program was identified in the inspected files
