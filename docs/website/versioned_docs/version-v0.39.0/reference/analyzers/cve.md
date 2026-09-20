---
tags:
  - cve
  - analyzers
---

# cve

The `cve` analyzer scans container images for vulnerabilities (CVEs) using the [grype](https://github.com/anchore/grype) CLI.

## Overview

- **Analyzer Name**: `cve`
- **Tool Dependency**: `grype`
- **Output Schema**: [`cve.schema.json`](pathname:///regis/schemas/analyzer/cve.schema.json)

## Functionality

This analyzer detects CVEs in OS packages and language-specific dependencies, grouping
findings by severity (`critical`, `high`, `medium`, `low`, `negligible`, `unknown`) and
tracking whether each vulnerability has an available fix.

## Default Rules

The following rule templates are provided by default:

| Slug            | Title                                                  | Level     |
| :-------------- | :----------------------------------------------------- | :-------- |
| `cve-count`     | Max allowed violations for a given severity level.     | `warning` |
| `fix-available` | All vulnerabilities should be fixed if a patch exists. | `warning` |

`cve-count` is a template — instantiate it once per severity level you want to enforce
(via `options.level` and `options.max_count`).
