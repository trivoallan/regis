---
tags:
  - endoflife
  - analyzers
---

# endoflife

The `endoflife` analyzer checks the support status of the software in the image using the [endoflife.date](https://endoflife.date) API.

## Overview

- **Analyzer Name**: `endoflife`
- **External API**: `https://endoflife.date/api`
- **Output Schema**: [`endoflife.schema.json`](pathname:///regis-cli/schemas/analyzer/endoflife.schema.json)

## Functionality

This analyzer identifies the "product" (e.g., `python`, `node`, `nginx`) from the image repository name and fetches its lifecycle data. It then matches the image tag against available release cycles to determine:

- Whether the version is officially supported.
- The End-of-Life (EOL) date.
- The latest available version in that release cycle.

## Mappings

RegiS includes a built-in mapping for many popular official images to their corresponding `endoflife.date` product slugs. For example:

- `python` -> `python`
- `postgres` -> `postgresql`
- `node` -> `nodejs`
- `golang` -> `go`
