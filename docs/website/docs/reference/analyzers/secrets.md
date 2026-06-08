---
tags:
  - secrets
  - analyzers
---

# secrets

The `secrets` analyzer scans container images for embedded secrets and credentials using the [TruffleHog](https://github.com/trufflesecurity/trufflehog) CLI.

## Overview

- **Analyzer Name**: `secrets`
- **Tool Dependency**: `trufflehog`
- **Output Schema**: [`secrets.schema.json`](pathname:///regis/schemas/analyzer/secrets.schema.json)

## Functionality

This analyzer searches image layers for embedded secrets, credentials, and tokens. It
reports the total number of findings (`secrets_count`) and how many were verified as live
(`verified_count`).

## Default Rules

The following rules are provided by default:

| Slug               | Title                                                       | Level      |
| :----------------- | :---------------------------------------------------------- | :--------- |
| `verified-secrets` | No verified, active credentials should be embedded in the image. | `critical` |
| `secret-scan`      | No secrets or credentials should be embedded in the image.  | `warning`  |
