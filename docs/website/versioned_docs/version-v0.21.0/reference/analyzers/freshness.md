---
tags:
  - freshness
  - analyzers
---

# freshness

The `freshness` analyzer tracks the age of a container image and compares it to the `latest` version.

## Overview

- **Analyzer Name**: `freshness`
- **Tool Dependency**: `skopeo` (to fetch creation dates)
- **Output Schema**: [`freshness.schema.json`](pathname:///regis-cli/schemas/analyzer/freshness.schema.json)

## Functionality

This analyzer extracts the creation date of the analyzed tag and the `latest` tag from the registry. It calculates:

- **Age**: The number of days since the analyzed tag was created.
- **Behind Latest**: The number of days the analyzed tag is behind the `latest` tag's creation date.
- **Is Latest**: A boolean indicating if the target tag is effectively the most recent one.

## Default Rules

The following rules are provided by default:

| Slug            | Title                                        | Level     |
| :-------------- | :------------------------------------------- | :-------- |
| `freshness-age` | Image should be less than expected days old. | `warning` |
