---
tags:
  - oci
  - analyzers
---

# oci

The `oci` analyzer fetches image metadata and platform details using the [regctl](https://github.com/regclient/regclient) CLI.

## Overview

- **Analyzer Name**: `oci`
- **Tool Dependency**: `regctl`
- **Output Schema**: [`oci.schema.json`](pathname:///regis/schemas/analyzer/oci.schema.json)

## Functionality

This analyzer provides a comprehensive view of image metadata, including:

- Raw manifest and config data.
- Per-platform details for multi-arch images (architecture, OS, size, layers).
- Exposed ports and environment variables.
- OCI labels.
- Flat list of supported platform identifiers (`platforms_supported`), e.g. `["linux/amd64", "linux/arm64"]`.

## Default Rules

The following rules are provided by default:

| Slug                      | Title                                                   | Level      |
| :------------------------ | :------------------------------------------------------ | :--------- |
| `user-blacklist`          | Image must not run as root.                             | `critical` |
| `max-size`                | Image size is within limits.                            | `warning`  |
| `layers-count`            | Image has an acceptable number of layers.               | `warning`  |
| `tag-blacklist`           | Image tag should not be 'latest'.                       | `warning`  |
| `platforms-count`         | Image should support multiple platforms.                | `info`     |
| `platforms-required`      | Image must support a required set of platforms.         | `warning`  |
| `platforms-whitelist`     | Image must only support allowed platforms.              | `warning`  |
| `platforms-blacklist`     | Image must not support forbidden platforms.             | `warning`  |
| `exposed-ports-whitelist` | Image exposes permitted ports.                          | `warning`  |
| `required-labels`         | Image must have required OCI labels.                    | `warning`  |
| `env-blacklist`           | Image must not contain forbidden environment variables. | `critical` |
