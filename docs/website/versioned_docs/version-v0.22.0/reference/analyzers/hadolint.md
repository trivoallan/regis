---
tags:
  - hadolint
  - analyzers
---

# hadolint

The `hadolint` analyzer lints a "pseudo-Dockerfile" reverse-engineered from the image history using [Hadolint](https://github.com/hadolint/hadolint).

## Overview

- **Analyzer Name**: `hadolint`
- **Tool Dependencies**: `hadolint`, `skopeo`
- **Output Schema**: [`hadolint.schema.json`](pathname:///regis/schemas/analyzer/hadolint.schema.json)

## Functionality

Since many images are uploaded without their original `Dockerfile`, RegiS reverse-engineers a pseudo-Dockerfile from the image's layer history. Hadolint then scans this pseudo-Dockerfile for security issues and style violations.

This is particularly useful for identifying:

- Inefficient `RUN` instructions.
- Insecure practices like using `sudo` or absolute paths.
- Missing labels or health checks.
