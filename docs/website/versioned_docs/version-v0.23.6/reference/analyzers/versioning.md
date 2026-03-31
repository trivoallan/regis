---
tags:
  - versioning
  - analyzers
---

# versioning

The `versioning` analyzer detects and classifies the tag naming patterns used by a repository.

## Overview

- **Analyzer Name**: `versioning`
- **Tool Dependency**: `skopeo`
- **Output Schema**: [`versioning.schema.json`](pathname:///regis/schemas/analyzer/versioning.schema.json)

## Functionality

Versioning helps ensure that images follow predictable release cycles. The analyzer classifies every tag into one of the following patterns:

| Pattern             | Description                                            | Examples                                             |
| ------------------- | ------------------------------------------------------ | ---------------------------------------------------- |
| `semver`            | Strict semantic versioning (`MAJOR.MINOR.PATCH`)       | `1.2.3`, `v2.0.0`                                    |
| `semver-variant`    | Semver with an OS, distro, or runtime suffix           | `1.2.3-alpine`, `1.2.3-glibc`, `1.2.3-slim-bookworm` |
| `semver-prerelease` | Semver with an `-alpha`, `-beta`, or `-rc` suffix only | `1.0.0-alpha`, `2.0.0-rc.1`                          |
| `numeric`           | Abbreviated version alias pointing to a semver release | `1`, `1.2`, `8`                                      |
| `numeric-variant`   | Abbreviated version alias with a variant suffix        | `1-alpine`, `1-glibc`, `1.2-musl`                    |
| `calver`            | Calendar-based versioning                              | `2024.12.01`                                         |
| `hash`              | Git commit hash                                        | `a1b2c3d`                                            |
| `named`             | Human-readable label                                   | `latest`, `stable`, `edge`                           |

The **SemVer Compliance Percentage** counts `semver`, `semver-variant`, `semver-prerelease`, `numeric`, and `numeric-variant` tags as semver-aligned, since `numeric` and `numeric-variant` tags are floating aliases that always resolve to a specific semver release.
