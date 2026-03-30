---
tags:
  - scorecarddev
  - analyzers
---

# scorecarddev

The `scorecarddev` analyzer fetches [OpenSSF Scorecard](https://scorecard.dev/) security assessments for the image source repository.

## Overview

- **Analyzer Name**: `scorecarddev`
- **External API**: `https://api.securityscorecards.dev`
- **Output Schema**: [`scorecarddev.schema.json`](pathname:///regis-cli/schemas/analyzer/scorecarddev.schema.json)

## Functionality

Security Scorecard evaluates the source material of a container by:

1.  **Source Repo Resolution**: Identifies the GitHub/GitLab repository from OCI labels or Docker Hub metadata.
2.  **API Integration**: Queries the OpenSSF Scorecard API for that repository.
3.  **Check Reporting**: Summarizes individual security checks such as "Binary-Artifacts", "Code-Review", "Dependency-Update-Tool", and "Signed-Releases".
