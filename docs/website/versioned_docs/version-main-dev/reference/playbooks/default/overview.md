---
sidebar_position: 2
---

# Overview

The RegiS Default Playbook is the standard security and governance profile used by `regis-cli`. It provides a comprehensive set of checks to ensure container images meet baseline security requirements and follow best practices.

## Default Tiers

The default playbook categorizes reports into one of three tiers based on the overall compliance score:

| Tier       | Condition              |
| :--------- | :--------------------- |
| **Gold**   | Compliance Score > 90% |
| **Silver** | Compliance Score > 70% |
| **Bronze** | Compliance Score > 50% |

## Default Badges

The report header displays the following dynamic status badges:

| Badge             | Logic                                                                  |
| :---------------- | :--------------------------------------------------------------------- |
| **Score**         | Displays the overall `rules_summary.score`.                            |
| **CVE: Critical** | Displayed (Error) if any critical vulnerabilities are detected.        |
| **CVE: High**     | Displayed (Warning) if any high-severity vulnerabilities are detected. |
| **Freshness**     | Displayed (Success) if the image is less than 30 days old.             |

## Compliance Levels

The playbook categorizes its security checks into two main levels: **Mandatory** and **Recommended**.

### Mandatory Requirements (Critical)

These are non-negotiable security requirements. Failing any of these checks marks the image as non-compliant.

| Rule                  | Description                                                                                | Logic (JSON Logic)                                                           |
| :-------------------- | :----------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| **No Root**           | The image must not be configured to run as the `root` user.                                | `{"!=": [{"var": "results.skopeo.platforms.0.user"}, "root"]}`               |
| **No Critical**       | No vulnerabilities with a `CRITICAL` severity level found by Trivy.                        | `{"==": [{"var": "results.trivy.critical_count"}, 0]}`                       |
| **No Fatal Policies** | No `FATAL` security issues found by Dockle.                                                | `{"==": [{"var": "results.dockle.issues_by_level.FATAL"}, 0]}`               |
| **Trusted Domain**    | The image must originate from a trusted container registry (e.g., Docker Hub, Quay, GHCR). | `{"in": [{"var": "request.registry"}, ["docker.io", "quay.io", "ghcr.io"]]}` |

### Recommended Requirements (Warning)

These rules represent security best practices. Failing these checks provides a warning but may not block promotion depending on your policy.

| Rule          | Description                                                          | Logic (JSON Logic)                                   |
| :------------ | :------------------------------------------------------------------- | :--------------------------------------------------- |
| **No High**   | No vulnerabilities with a `HIGH` severity level found by Trivy.      | `{"==": [{"var": "results.trivy.high_count"}, 0]}`   |
| **Freshness** | The image should have been built or updated within the last 30 days. | `{"<": [{"var": "results.freshness.age_days"}, 30]}` |

## Report Organization

The default playbook structures its findings into seven specialized pages to provide a clear and actionable overview.

| Page                                  | Purpose                                                                                           |
| :------------------------------------ | :------------------------------------------------------------------------------------------------ |
| **Overview** (`index`)                | High-level summary of analysis results, creation time, and "GO/NOGO" recommendation.              |
| **Compliance** (`compliance`)         | Detailed breakdown of mandatory and recommended scorecard results.                                |
| **Security** (`security`)             | Deep dive into vulnerabilities (Trivy) and image provenance.                                      |
| **Supply Chain** (`supply-chain`)     | Analysis of the Software Bill of Materials (SBOM) and OpenSSF Scorecard results.                  |
| **Best Practices** (`best-practices`) | Insights from Dockerfile linting (Hadolint), configuration checks, and security linting (Dockle). |
| **Insights** (`insights`)             | Trends in image freshness, registry popularity, and lifecycle (EndOfLife) status.                 |
| **Technical Details** (`metadata`)    | Low-level data including image layers, Skopeo inspection results, and versioning patterns.        |

## Standard Metadata

The default playbook automatically consumes "well-known" metadata fields if provided via the `--meta` flag:

- **`trigger.user`**: Displayed as the initiator of the analysis.
- **`trigger.url`**: Used to provide a direct link to the CI job or environment that triggered the analysis.

## Analysis Case Studies

These examples demonstrate how `regis-cli` adapts its recommendations based on the security posture and lifecycle of different container images.

### Case 1: The "Gold Standard" (Compliant)

**Target:** `alpine:latest` (or a specialized minimal base image)

| Aspect         | Status                                                                                                                                                                                           |
| :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Verdict**    | **GO**                                                                                                                                                                                           |
| **Compliance** | 100%                                                                                                                                                                                             |
| **Security**   | 0 Critical, 0 High vulnerabilities.                                                                                                                                                              |
| **Findings**   | Image is lightweight, runs as a non-root user (if configured), and uses a trusted registry. View the [Live Security Report](pathname:///regis-cli/examples/playbooks/default/alpine/index.html). |

```bash
regis-cli analyze alpine:latest -s -D docs/website/static/examples/alpine
```

:::info
**Why it passes:** Minimal images significantly reduce the attack surface. By maintaining zero high-severity vulnerabilities and a small footprint, they represent the ideal state for production deployments.
:::

### Case 2: The "At-Risk" Image (Vulnerable)

**Target:** `old-web-app:v1` (High-vulnerability legacy image)

| Aspect         | Status                                                                                                            |
| :------------- | :---------------------------------------------------------------------------------------------------------------- |
| **Verdict**    | **NOGO**                                                                                                          |
| **Compliance** | 45%                                                                                                               |
| **Security**   | 12 Critical, 45 High vulnerabilities.                                                                             |
| **Findings**   | Heavy base image (e.g., full Ubuntu/Debian), running as `root`, and containing multiple unpatched security flaws. |

:::danger
This image fails the **Mandatory Requirements** and should be blocked from reaching production environments until the base image is updated and security patches are applied.
:::

### Case 3: The "Legacy" Image (Outdated)

**Target:** `stable-api:v2.4` (Secure but unmaintained)

| Aspect         | Status                                                                                                                |
| :------------- | :-------------------------------------------------------------------------------------------------------------------- |
| **Verdict**    | **GO (with Warnings)**                                                                                                |
| **Compliance** | 85%                                                                                                                   |
| **Security**   | 0 Critical, 5 High vulnerabilities.                                                                                   |
| **Findings**   | No critical flaws, but the image is >180 days old and the underlying OS version is nearing its **End of Life (EOL)**. |

:::info
**Insight:** Even if an image is currently "secure" at the vulnerability level, lifecycle checks flag it as a maintenance risk. The playbook recommends a rebuild to ensure continued support and freshness.
:::

### Benchmark: `regis-cli`

Finally, we analyze [regis-cli](https://github.com/trivoallan/regis-cli) itself. As a tool designed to enforce security, its own image is built following all the "Gold Standard" practices: minimal base image, no vulnerabilities, and full provenance.

:::tip
You can view the live result of this analysis here:
[**Live `regis-cli:latest` Benchmark Report**](pathname:///regis-cli/examples/playbooks/default/regis-cli/index.html)

```bash
regis-cli analyze ghcr.io/trivoallan/regis-cli:latest -s -D docs/website/static/examples/regis-cli
```

:::

- **100% Mandatory Compliance**: Passes all critical checks (No Root, No Critical, Trusted Registry).
- **Minimal Attack Surface**: Built on a slim Python/Alpine base.
- **Full Supply Chain Evidence**: Provides both SBOM (CycloneDX) and Provenance indicators.
- **Active Maintenance**: Regularly rebuilt to maintain a "Fresh" status (< 30 days).

## GitLab Integrations

The default playbook includes pre-configured GitLab integrations to automate MR management.

### Badge Synchronization

The default playbook synchronizes the following status badges as GitLab labels:

| Badge Slug     | Label Result                              |
| :------------- | :---------------------------------------- |
| `score`        | `Score: [value]` (Information)            |
| `freshness`    | `Freshness: Fresh !` (Success) if passed. |
| `cve-critical` | `CVE: Critical` (Error) if failed.        |
| `cve-high`     | `CVE: High` (Warning) if failed.          |

### MR Description Checklist

The following items are appended as checkboxes to the Merge Request description. They can be dynamically shown and pre-checked based on the analysis results:

| Item                                   | Show Condition (`show_if`)                                                 | Check Condition (`check_if`)                                               |
| :------------------------------------- | :------------------------------------------------------------------------- | :------------------------------------------------------------------------- |
| Revue de sécurité réalisée             | Always included                                                            | Never pre-checked                                                          |
| Aucune vulnérabilité CRITIQUE détectée | `results.trivy.critical_count == 0`                                        | `results.trivy.critical_count == 0`                                        |
| Image issue d'un registre de confiance | `request.registry` ∈ \{docker.io, registry-1.docker.io, quay.io, ghcr.io\} | `request.registry` ∈ \{docker.io, registry-1.docker.io, quay.io, ghcr.io\} |

### MR Templates

The default playbook automatically generates a security evidence document for Merge Requests.

| Template                                                                               | Condition                                                                                                   |
| :------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `https://github.com/trivoallan/regis-cli` (dir: `regis_cli/cookiecutters/mr-evidence`) | Always generated (no condition). Outputs a `SECURITY_EVIDENCE.md` file in the `.regis-evidence/` directory. |

:::tip
For more information on how to define your own compliance rules, see the [Understand Playbooks](../../../../overview/playbooks) guide.
:::
