---
sidebar_position: 2
---

# default

The RegiS Default Playbook is the standard security and governance profile used by `regis`. It provides a comprehensive set of checks to ensure container images meet baseline security requirements and follow best practices.

## Default Tiers

The default playbook categorizes reports into one of three tiers based on the overall compliance score:

| Tier       | Condition              |
| :--------- | :--------------------- |
| **Gold**   | Compliance Score > 90% |
| **Silver** | Compliance Score > 70% |
| **Bronze** | Compliance Score > 50% |

## Default Rules

Rules are evaluated automatically based on which analyzers are present in the report. Custom rule instances can override defaults or add new checks.

### Critical

Failing any critical rule blocks the image from reaching a Gold or Silver tier.

| Slug                        | Provider | Description                                                                          |
| :-------------------------- | :------- | :----------------------------------------------------------------------------------- |
| `registry-domain-whitelist` | `core`   | Image must originate from a trusted registry (docker.io, quay.io, ghcr.io, ghcr.io). |
| `no-root`                   | `skopeo` | Image must not be configured to run as the `root` user.                              |
| `cve-critical`              | `trivy`  | No `CRITICAL` CVEs allowed (max: 0).                                                 |

### Warning

Warning-level failures reduce the compliance score but do not block promotion on their own.

| Slug            | Provider       | Description                                      |
| :-------------- | :------------- | :----------------------------------------------- |
| `cve-high`      | `trivy`        | No more than 10 `HIGH` CVEs.                     |
| `cve-fixable`   | `trivy`        | No unpatched CVEs with an available fix.         |
| `has-sbom`      | `sbom`         | Image must provide a Software Bill of Materials. |
| `scorecard-min` | `scorecarddev` | OpenSSF Scorecard score must be ≥ 5.0.           |

### Info

Informational checks that surface hygiene issues without impacting the tier.

| Slug        | Provider    | Description                            |
| :---------- | :---------- | :------------------------------------- |
| `age`       | `freshness` | Image should be less than 90 days old. |
| `no-latest` | `skopeo`    | Image tag must not be `latest`.        |

## Default Badges

The report header displays the following dynamic status badges:

| Badge                | Logic                                       |
| :------------------- | :------------------------------------------ |
| **CVE: Critical**    | Shown (Error) if `cve-critical` rule fails. |
| **CVE: High**        | Shown (Warning) if `cve-high` rule fails.   |
| **Freshness: Fresh** | Shown (Success) if `age` rule passes.       |
| **Freshness: Stale** | Shown (Warning) if `age` rule fails.        |

## Analysis Case Studies

These examples demonstrate how `regis` adapts its recommendations based on the security posture and lifecycle of different container images.

### Case 1: The "Gold Standard" (Compliant)

**Target:** `alpine:latest` (or a specialized minimal base image)

| Aspect         | Status                                                                                      |
| :------------- | :------------------------------------------------------------------------------------------ |
| **Verdict**    | **GO**                                                                                      |
| **Compliance** | 100%                                                                                        |
| **Security**   | 0 Critical, 0 High vulnerabilities.                                                         |
| **Findings**   | Image is lightweight, runs as a non-root user (if configured), and uses a trusted registry. |

```bash
regis analyze alpine:latest -s -D docs/website/static/examples/alpine
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
This image fails the **Critical** rules and should be blocked from reaching production environments until the base image is updated and security patches are applied.
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

### Benchmark: `regis`

Finally, we analyze [regis](https://github.com/trivoallan/regis) itself. As a tool designed to enforce security, its own image is built following all the "Gold Standard" practices: minimal base image, no vulnerabilities, and full provenance.

:::tip
You can view the live result of this analysis here:
[**Live `regis:latest` Benchmark Report**](pathname:///regis/examples/playbooks/default/regis/index.html)

```bash
regis analyze ghcr.io/trivoallan/regis:latest -s -D docs/website/static/examples/regis
```

:::

- **100% Mandatory Compliance**: Passes all critical checks (`no-root`, `cve-critical`, `registry-domain-whitelist`).
- **Minimal Attack Surface**: Built on a slim Python/Alpine base.
- **Full Supply Chain Evidence**: Provides both SBOM (CycloneDX) and Provenance indicators.
- **Active Maintenance**: Regularly rebuilt to maintain a "Fresh" status (< 90 days).

## GitLab Integrations

The default playbook includes pre-configured GitLab integrations to automate MR management.

### Badge Synchronization

The default playbook synchronizes the following status badges as GitLab labels:

| Badge Slug     | Label Result                            |
| :------------- | :-------------------------------------- |
| `score`        | `Score: [value]` (Information)          |
| `freshness`    | `Freshness: Fresh` (Success) if passed. |
| `cve-critical` | `CVE: Critical` (Error) if failed.      |
| `cve-high`     | `CVE: High` (Warning) if failed.        |

### MR Description Checklist

The following items are appended as checkboxes to the Merge Request description. They can be dynamically shown and pre-checked based on the analysis results:

| Item                                   | Show Condition (`show_if`)               | Check Condition (`check_if`)                     |
| :------------------------------------- | :--------------------------------------- | :----------------------------------------------- |
| Revue de sécurité réalisée             | Always included                          | Never pre-checked                                |
| Aucune vulnérabilité CRITIQUE détectée | `rules.cve-critical` exists              | `rules.cve-critical.passed == true`              |
| Image issue d'un registre de confiance | `rules.registry-domain-whitelist` exists | `rules.registry-domain-whitelist.passed == true` |
| Image ne tourne pas en root            | `rules.no-root` exists                   | `rules.no-root.passed == true`                   |

### MR Templates

The default playbook automatically generates a security evidence document for Merge Requests.

| Template                                                                       | Condition                                                                                                   |
| :----------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `https://github.com/trivoallan/regis` (dir: `regis/cookiecutters/mr-evidence`) | Always generated (no condition). Outputs a `SECURITY_EVIDENCE.md` file in the `.regis-evidence/` directory. |

:::tip
For more information on how to define your own compliance rules, see the [Playbooks](../../../concepts/playbooks.md) guide.
:::
