# regis-cli

`regis-cli` is a powerful tool to analyze Docker image registries, evaluate security playbooks, and produce rich HTML/JSON reports.

## Features

- **Consolidated Analysis** — Uses `skopeo` for fast, multi-arch registry inspection.
- **Playbook Engine** — Evaluate custom rules and policies against image metadata.
- **Multi-Format Output** — Generate both JSON (for automation) and HTML (for humans) in a single run.
- **Template-Based Paths** — Dynamic output directory and filename based on image metadata (registry, repository, tag).
- **Report Caching** — Reuse existing analysis results to speed up report regeneration.
- **Pluggable Architecture** — Easily add new analyzers and playbook rules.

## Built-in Analyzers

| Analyzer       | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `skopeo`       | **Unified** inspection (multi-arch, OS, labels, layers, and root detection). |
| `versioning`   | Checks for semantic versioning consistency and tag patterns.                |
| `freshness`    | Calculates image age and identifies the creation date.                       |
| `trivy`        | Integrates vulnerability scanning results.                                   |
| `endoflife`    | Checks for EOL status of base images via `endoflife.date`.                  |
| `hadolint`     | Lints Dockerfiles for best practices (if reconstructed).                    |
| `dockle`       | Container image linter for security and best practices.                     |
| `sbom`         | Generates/Retrieves Software Bill of Materials (SBOM).                      |
| `provenance`   | Verifies image build provenance and SLSA metadata.                          |
| `size`         | Analyzes image size and layer distribution.                                 |
| `popularity`   | Fetches popularity metrics (stars, pulls) from Docker Hub.                  |
| `playbookdev` | Integration with OpenSSF Playbook for registry-level security.             |

## Installation

```bash
pipenv install
```

## Usage

### Basic Analysis
```bash
# Analyze an image and output to stdout (JSON)
regis-cli analyze nginx:latest
```

### Advanced Reporting
```bash
# Generate both JSON and HTML reports
regis-cli analyze nginx:latest --site
```

### Report Caching
```bash
# Faster HTML generation by reusing previous analysis
regis-cli analyze nginx:latest --site --cache
```

### Dynamic Output Paths
By default, reports are written to `reports/{registry}/{repository}/{digest}/report.{format}`. You can override this using:
```bash
regis-cli analyze nginx:latest -o "my-custom-report.{format}" -D "results/{repository}"
```

## Playbooks

Playbooks allow you to define rules using JSON logic. Use them to verify compliance:
- **No critical vulnerabilities**
- **No root user**
- **Maximum image age**
- **Semantic versioning enforced**

See `examples/` for sample playbook definitions.

## Development

```bash
# Run tests
pipenv run pytest -v

# Run with verbose logging
regis-cli -v analyze nginx:latest
```

## Adding a New Analyzer

1. Create a module in `regis_cli/analyzers/` inheriting from `BaseAnalyzer`
2. Create a JSON Schema in `regis_cli/schemas/`
3. Register the entry point in `pyproject.toml`
4. Reinstall: `pipenv install`

## Documentation

Comprehensive documentation is available in the `docs/` directory (Antora).

## Cookiecutter Template

You can quickly bootstrap a new repository for image analysis using our Cookiecutter template:

```bash
pipenv run cookiecutter cookiecutter/
```

## License

MIT
