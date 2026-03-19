"""Trivy analyzer — scans image for vulnerabilities using Trivy CLI."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from typing import Any

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)


def _run_trivy(
    image: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Run trivy image scan and return parsed JSON."""
    trivy_path = shutil.which("trivy")
    if not trivy_path:
        raise AnalyzerError("trivy executable not found in PATH")

    # Pass registry credentials to Trivy if available
    env = os.environ.copy()

    # Priority: passed credentials > environment variables
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")

    if user and pwd:
        env["TRIVY_USERNAME"] = user
        env["TRIVY_PASSWORD"] = pwd

    cmd = [
        trivy_path,
        "image",
        "--format",
        "json",
        "--quiet",
        "--no-progress",
    ]
    if platform:
        cmd.extend(["--platform", platform])

    cmd.append(image)

    logger.debug("Running trivy: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return json.loads(result.stdout)  # type: ignore[no-any-return]
    except subprocess.CalledProcessError as exc:
        raise AnalyzerError(f"trivy failed: {exc.stderr}") from exc
    except json.JSONDecodeError as exc:
        raise AnalyzerError(f"trivy produced invalid JSON: {exc}") from exc


class TrivyAnalyzer(BaseAnalyzer):
    """Scan image for vulnerabilities using Trivy."""

    name = "trivy"
    schema_file = "trivy.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "trivy-no-critical",
                "title": "No CRITICAL vulnerabilities found by Trivy.",
                "level": "critical",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.trivy.critical_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "No critical vulnerabilities detected.",  # nosec B105
                    "fail": "Image has ${results.trivy.critical_count} critical CVEs (max allowed: ${rule.params.max_count}).",
                },
            },
            {
                "slug": "trivy-no-high",
                "title": "No HIGH vulnerabilities found by Trivy.",
                "level": "warning",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.trivy.high_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "No high vulnerabilities detected.",  # nosec B105
                    "fail": "Image has ${results.trivy.high_count} high CVEs (max allowed: ${rule.params.max_count}).",
                },
            },
            {
                "slug": "trivy-fix-available",
                "title": "All vulnerabilities should be fixed if a patch exists.",
                "level": "warning",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.trivy.fixed_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "All vulnerabilities with available fixes have been patched.",  # nosec B105
                    "fail": "Image has ${results.trivy.fixed_count} vulnerabilities with available fixes.",
                },
            },
            {
                "slug": "trivy-secret-scan",
                "title": "No secrets or credentials should be embedded in the image.",
                "level": "critical",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.trivy.secrets_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "No secrets detected in the image.",  # nosec B105
                    "fail": "Trivy detected ${results.trivy.secrets_count} secrets or credentials in the image.",
                },
            },
        ]

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Run trivy analysis."""
        # ... (rest of image string logic)
        if client.registry == "docker.io" or client.registry == "registry-1.docker.io":
            full_image = f"{repository}:{tag}"
        else:
            full_image = f"{client.registry}/{repository}:{tag}"

        try:
            data = _run_trivy(
                full_image,
                username=client.username,
                password=client.password,
                platform=platform,
            )
        except AnalyzerError as exc:
            raise exc

        # Process results
        targets = []
        counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0,
        }
        fixed_count = 0
        secrets_count = 0

        for result in data.get("Results", []):
            target_data = {
                "Target": result.get("Target"),
                "Vulnerabilities": [],
                "Secrets": [],
            }

            # Handle Vulnerabilities
            vulns = result.get("Vulnerabilities", [])
            if vulns:
                clean_vulns = []
                for v in vulns:
                    severity = v.get("Severity", "UNKNOWN")
                    counts[severity] = counts.get(severity, 0) + 1
                    if v.get("FixedVersion"):
                        fixed_count += 1

                    clean_vulns.append(
                        {
                            "VulnerabilityID": v.get("VulnerabilityID"),
                            "PkgName": v.get("PkgName"),
                            "InstalledVersion": v.get("InstalledVersion"),
                            "FixedVersion": v.get("FixedVersion", ""),
                            "Severity": severity,
                            "Title": v.get("Title", ""),
                            "Description": v.get("Description", ""),
                        }
                    )
                target_data["Vulnerabilities"] = clean_vulns
            else:
                target_data["Vulnerabilities"] = None

            # Handle Secrets
            secrets = result.get("Secrets", [])
            if secrets:
                secrets_count += len(secrets)
                target_data["Secrets"] = [
                    {
                        "RuleID": s.get("RuleID"),
                        "Title": s.get("Title"),
                        "Severity": s.get("Severity"),
                        "Match": s.get("Match"),
                    }
                    for s in secrets
                ]
            else:
                target_data["Secrets"] = None

            targets.append(target_data)

        total = sum(counts.values())

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "trivy_version": str(data.get("SchemaVersion", "unknown")),
            "vulnerability_count": total,
            "critical_count": counts["CRITICAL"],
            "high_count": counts["HIGH"],
            "medium_count": counts["MEDIUM"],
            "low_count": counts["LOW"],
            "unknown_count": counts["UNKNOWN"],
            "fixed_count": fixed_count,
            "secrets_count": secrets_count,
            "targets": targets,
        }
