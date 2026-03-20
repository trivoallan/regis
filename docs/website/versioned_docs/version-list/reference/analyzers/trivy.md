# trivy

The `trivy` analyzer scans container images for vulnerabilities and secrets using the [Trivy](https://github.com/aquasecurity/trivy) CLI.

## Overview

- **Analyzer Name**: `trivy`
- **Tool Dependency**: `trivy`
- **Output Schema**: [`trivy.schema.json`](pathname:///regis-cli/schemas/analyzer/trivy.schema.json)

## Functionality

This analyzer performs the following checks:

1.  **Vulnerability Scanning**: Detects CVEs in OS packages and language-specific dependencies.
2.  **Secret Detection**: Searches for embedded secrets, credentials, and sensitive data.

## Default Rules

The following rules are provided by default:

| Slug                  | Title                                                      | Level      |
| :-------------------- | :--------------------------------------------------------- | :--------- |
| `trivy-no-critical`   | No CRITICAL vulnerabilities found by Trivy.                | `critical` |
| `trivy-no-high`       | No HIGH vulnerabilities found by Trivy.                    | `warning`  |
| `trivy-fix-available` | All vulnerabilities should be fixed if a patch exists.     | `warning`  |
| `trivy-secret-scan`   | No secrets or credentials should be embedded in the image. | `critical` |
