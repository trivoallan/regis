---
tags:
  - dockle
  - analyzers
---

# dockle

The `dockle` analyzer is a container image linter that checks for security issues and best practices using [Dockle](https://github.com/goodwithtech/dockle).

## Overview

- **Analyzer Name**: `dockle`
- **Tool Dependency**: `dockle`
- **Output Schema**: [`dockle.schema.json`](pathname:///regis-cli/schemas/analyzer/dockle.schema.json)

## Functionality

Dockle helps to build "best practice" Docker images by checking for:

- Security vulnerabilities in the image configuration.
- Compliance with CIS Docker Benchmarks.
- Unnecessary files or instructions that increase image size or security risk.

## Default Rules

The following rules are provided by default:

| Slug                  | Title                            | Level      |
| :-------------------- | :------------------------------- | :--------- |
| `dockle-no-fatal`     | No FATAL issues found by Dockle. | `critical` |
| `dockle-max-warnings` | Too many Dockle warnings found.  | `warning`  |
