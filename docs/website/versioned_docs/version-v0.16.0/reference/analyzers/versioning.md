# versioning

The `versioning` analyzer detects and classifies the tag naming patterns used by a repository.

## Overview

- **Analyzer Name**: `versioning`
- **Tool Dependency**: `skopeo`
- **Output Schema**: [`versioning.schema.json`](pathname:///regis-cli/schemas/analyzer/versioning.schema.json)

## Functionality

Versioning helps ensure that images follow predictable release cycles. The analyzer classifies every tag into one of the following patterns:

- **semver**: Strict semantic versioning (e.g., `1.2.3`).
- **semver-prerelease**: Semver with tags like `-alpha` or `-beta`.
- **semver-variant**: Semver with OS suffixes (e.g., `1.2.3-alpine`).
- **calver**: Calendar-based versioning (e.g., `2024.12.01`).
- **numeric**: Simple numbers (e.g., `8`, `1.2`).
- **hash**: Git commit hashes.
- **named**: Common labels like `latest` or `stable`.

It also provides a **SemVer Compliance Percentage** for the repository as a whole.
