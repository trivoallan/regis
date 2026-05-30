---
sidebar_label: Overview
sidebar_position: 0
---

# Analyzers Reference

RegiS CLI includes several built-in analyzers that extract specific data from container images.
Each analyzer runs independently and contributes to the unified data model evaluated by your [Playbooks](../../concepts/playbooks.md).

| Analyzer                          | Description                                                |
| :-------------------------------- | :--------------------------------------------------------- |
| [cve](./cve.md)                   | Vulnerability (CVE) scanning via grype                     |
| [dockle](./dockle.md)             | Container image linting and CIS benchmark checks           |
| [endoflife](./endoflife.md)       | OS and runtime end-of-life status                          |
| [freshness](./freshness.md)       | Image age and staleness score                              |
| [hadolint](./hadolint.md)         | Dockerfile best practice linting                           |
| [oci](./oci.md)                   | Base metadata from registry (labels, architecture, layers) |
| [popularity](./popularity.md)     | Registry pull count and popularity metrics                 |
| [provenance](./provenance.md)     | Supply chain provenance and attestations                   |
| [sbom](./sbom.md)                 | Software Bill of Materials (CycloneDX / SPDX) via syft     |
| [scorecarddev](./scorecarddev.md) | OpenSSF Scorecard checks                                   |
| [secrets](./secrets.md)           | Embedded secret detection via trufflehog                   |
| [size](./size.md)                 | Image size and layer analysis                              |
| [versioning](./versioning.md)     | Image tag and versioning policy                            |
