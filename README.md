# Regis

> **Registry Scores** — Container Security & Policy-as-Code Orchestration

![Coverage](./coverage-badge.svg)

Regis provides unified container analysis, custom playbooks, and highly customizable interactive reports for production-ready CI/CD.

## Documentation

Comprehensive documentation, including installation and usage guides, is available at:
**[https://trivoallan.github.io/regis/](https://trivoallan.github.io/regis/)**

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

---

## Report Preview

`regis` generates high-quality, interactive HTML dashboards.
Below is a preview of the different sections available in a standard report.

**[Explore the interactive Alpine example report here](https://trivoallan.github.io/regis/regis/0.14.0/_attachments/examples/alpine/index.html)**

<details>
<summary>📈 Dashboard Overview</summary>
<br>
<img src=".github/assets/report-overview.png" alt="Dashboard Overview" width="100%">
</details>

<details>
<summary>✅ Compliance Analysis</summary>
<br>
<img src=".github/assets/report-compliance.png" alt="Compliance Analysis" width="100%">
</details>

<details>
<summary>🛡️ Vulnerability & Security</summary>
<br>
<img src=".github/assets/report-security.png" alt="Vulnerability Security" width="100%">
</details>

<details>
<summary>🔗 Supply Chain & Quality</summary>
<br>
<img src=".github/assets/report-supply-chain.png" alt="Supply Chain & Quality" width="100%">
</details>

<details>
<summary>✨ Best Practices</summary>
<br>
<img src=".github/assets/report-best-practices.png" alt="Best Practices" width="100%">
</details>

<details>
<summary>💡 Insights & Lifecycle</summary>
<br>
<img src=".github/assets/report-insights.png" alt="Insights & Lifecycle" width="100%">
</details>

<details>
<summary>⚙️ Technical Details</summary>
<br>
<img src=".github/assets/report-technical-details.png" alt="Technical Details" width="100%">
</details>

---

## CI/CD Security & Supply Chain Integrity

The GitHub Actions pipelines enforce layered security controls:

- **Dependency auditing gate (`pip-audit`)** in CI with a fail threshold at **HIGH/CRITICAL** severity.
- **Release SBOM generation** in both **CycloneDX JSON** and **SPDX JSON** formats (via `syft`/Anchore action).
- **Provenance attestation** for published container images using GitHub Artifact Attestations (`actions/attest-build-provenance`).

These artifacts are uploaded by the release workflow so consumers can inspect composition and verify origin before deployment.

---

## License

MIT
