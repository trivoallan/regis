---
sidebar_position: 7
tags:
  - archives
  - concepts
---

# Archives

An **archive** is a versioned collection of container image analysis reports. It enables you to track security metrics over time, monitor compliance drift, detect regressions, and maintain audit trails for regulatory requirements.

## What is an Archive?

An archive stores timestamped `report.json` files for one or more container images, along with an index (`manifest.json`) that tracks all analysis runs. Each analysis produces a new entry in the archive, preserving the complete history of an image's security posture.

```text
my-app-archive/
  manifest.json                    # Index of all runs
  2024-01-15T10-30-00Z.report.json # First analysis
  2024-01-22T14-15-00Z.report.json # Second analysis
  2024-02-01T09-45-00Z.report.json # Third analysis
```

## Why Use Archives?

### Historical Comparison

Compare security metrics across multiple builds. Identify trends, regressions, or improvements in vulnerability counts, freshness scores, or compliance metrics.

### Compliance Monitoring

Maintain evidence of compliance over time. Regulatory audits often require proof that security controls were in place and enforced continuously.

### Regression Detection

Detect when a newly built image introduces new vulnerabilities or fails previously passing checks. Catch problems before they reach production.

### Audit Trails

Create immutable records of what was analyzed, when, and what the results were. Essential for security reviews and incident investigation.

## Archive Concepts

### Structure

Each archive is a self-contained directory containing:

- **`manifest.json`**: An index file listing all archived reports with timestamps, image references, and metadata.
- **`<timestamp>.report.json`** files: Individual analysis reports, one per run, named with ISO 8601 timestamps.

### Storage Modes

Regis supports multiple archive storage backends:

- **Git Repository**: Version-control your archive using `regis archive bootstrap`. Commit new reports automatically via CI/CD pipelines.
- **CI Artifacts**: Store archives in your CI system (GitHub Actions, GitLab CI, etc.) as build artifacts.
- **Local Directory**: Keep archives on disk for local development and testing.

### Multi-Archive Support

For large organizations with multiple image repositories, use `archives.json` to combine and query reports from multiple archive sources:

```json
{
  "sources": [
    { "name": "app-frontend", "path": "archives/frontend" },
    { "name": "app-backend", "path": "archives/backend" }
  ]
}
```

The dashboard can then aggregate metrics across all archives.

## Archives and Other Concepts

### Reports

An archive is a collection of [reports](./reports.md). Each report captures a complete analysis at a specific moment in time. Archives give reports historical context and enable trend analysis.

### Playbooks

Each report in an archive was evaluated against a [playbook](./playbooks.md). The same playbook rules apply across all reports in the archive, ensuring consistent evaluation over time. If you change playbook rules, you can re-evaluate older reports with the new rules to see how your policy evolution would have affected past builds.

### Scoring

[Scores](./scoring.md) are calculated fresh for each report in an archive. By tracking scores over time, you can measure improvement in security posture, identify categories where compliance is slipping, and justify investment in security improvements.

## Getting Started with Archives

To bootstrap an archive using a Git repository:

```bash
regis archive bootstrap my-app-archive --repo https://github.com/my-org/my-app-archive.git
```

See [Archive Repository Setup](../usage/integrations/archive-repo.md) for detailed configuration.

To customize archive behavior (naming, metadata, retention):

See [Customizing Archives](../usage/integrations/archive-customize.md).

For multi-archive queries and aggregation:

See [Multi-Archive Configuration](../usage/multi-archive.md).

:::tip
Archives work best in CI/CD pipelines. Each image build automatically appends a new report to the archive, creating a complete history without manual steps.
:::
