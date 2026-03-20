# sbom

The `sbom` analyzer generates a Software Bill of Materials (SBOM) for container images using [Trivy](https://github.com/aquasecurity/trivy).

## Overview

- **Analyzer Name**: `sbom`
- **Tool Dependency**: `trivy`
- **Output Schema**: [`sbom.schema.json`](pathname:///regis-cli/schemas/analyzer/sbom.schema.json)

## Functionality

This analyzer produces a standard CycloneDX JSON SBOM. It identifies:

- **OS Packages**: Version and source (e.g., APK, DPKG, RPM).
- **Application Bundles**: Language-specific libraries (e.g., NPM, Pip, Go modules).
- **Licenses**: Extracting license identifiers for each component.
- **Dependencies**: Mapping relationships between components.
