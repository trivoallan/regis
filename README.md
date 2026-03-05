# regis-cli

`regis-cli` is a powerful, production-ready tool to analyze Docker image registries, evaluate security playbooks, and produce rich HTML/JSON reports. It enables deep visibility into container image metadata and security posture, allowing for automated policy enforcement in CI/CD environments.

## Documentation

Comprehensive documentation, including installation and usage guides, is available at:
**[https://trivoallan.github.io/regis-cli/](https://trivoallan.github.io/regis-cli/)**

## Key Features

- **Unified Registry Inspection** — Fast, multi-arch metadata extraction from any OCI-compliant registry using `skopeo`.
- **Pluggable Analyzer Ecosystem** — Orchestrates industry-standard tools like `Trivy`, `Skopeo`, `Hadolint`, and `Dockle` to gather comprehensive security insights.
- **Policy-as-Code Playbooks** — Define compliance and security rules (e.g., "no critical vulnerabilities", "maximum image age") using flexible `jsonLogic` evaluations.
- **Hybrid Reporting** — Simultaneously generates machine-readable JSON for automation and rich, interactive HTML dashboards for human review.
- **CI/CD Native** — Designed to integrate seamlessly into GitHub Actions or GitLab CI pipelines with first-class support for MR/PR reporting.
- **Efficient Caching** — Reuse existing analysis results to speed up repeated evaluations and report regeneration.

## Built-in Analyzers

| Analyzer     | Description                                                                            |
| ------------ | -------------------------------------------------------------------------------------- |
| `skopeo`     | Extracts multi-arch metadata, OS/Architecture labels, layers, and root user detection. |
| `trivy`      | Performs vulnerability scanning and generates Software Bill of Materials (SBOM).       |
| `provenance` | Verifies image build provenance and SLSA metadata.                                     |
| `endoflife`  | Checks for End-Of-Life (EOL) status of base images using `endoflife.date`.             |
| `freshness`  | Calculates image age and identifies potential maintenance risks.                       |
| `hadolint`   | Lints Dockerfiles for security and best practice violations.                           |
| `size`       | Analyzes image size and layer distribution for optimization.                           |
| `versioning` | Ensures semantic versioning consistency and tag validation.                            |

## License

MIT

---

## Report Preview

`regis-cli` generates high-quality, interactive HTML dashboards. Below is a preview of the different sections available in a standard report.

**[Explore the interactive Alpine example report here](https://trivoallan.github.io/regis-cli/regis-cli/0.14.0/_attachments/examples/alpine/index.html)**

```carousel
![Dashboard Overview](.github/assets/report-overview.png)
<!-- slide -->
![Compliance Analysis](.github/assets/report-compliance.png)
<!-- slide -->
![Vulnerability Security](.github/assets/report-security.png)
<!-- slide -->
![Supply Chain & Quality](.github/assets/report-supply-chain.png)
<!-- slide -->
![Best Practices](.github/assets/report-best-practices.png)
<!-- slide -->
![Insights & Lifecycle](.github/assets/report-insights.png)
<!-- slide -->
![Technical Details](.github/assets/report-technical-details.png)
```
