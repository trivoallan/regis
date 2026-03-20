# skopeo

The `skopeo` analyzer fetches image metadata and platform details using the [Skopeo](https://github.com/containers/skopeo) CLI.

## Overview

- **Analyzer Name**: `skopeo`
- **Tool Dependency**: `skopeo`
- **Output Schema**: [`skopeo.schema.json`](pathname:///regis-cli/schemas/analyzer/skopeo.schema.json)

## Functionality

This analyzer provides a comprehensive view of image metadata, including:

- Raw `inspect` data.
- Per-platform details for multi-arch images (architecture, OS, size, layers).
- Exposed ports and environment variables.
- OCI labels.

## Default Rules

The following rules are provided by default:

| Slug                     | Title                                                   | Level      |
| :----------------------- | :------------------------------------------------------ | :--------- |
| `skopeo-no-root`         | Image must not run as root.                             | `critical` |
| `skopeo-max-size`        | Image size is within limits.                            | `warning`  |
| `skopeo-max-layers`      | Image has an acceptable number of layers.               | `warning`  |
| `skopeo-tag-not-latest`  | Image tag should not be 'latest'.                       | `warning`  |
| `skopeo-multi-arch`      | Image should support multiple platforms.                | `info`     |
| `skopeo-exposed-ports`   | Image exposes permitted ports.                          | `warning`  |
| `skopeo-required-labels` | Image must have required OCI labels.                    | `warning`  |
| `skopeo-forbidden-env`   | Image must not contain forbidden environment variables. | `critical` |
