"""CVE analyzer — scans images for vulnerabilities using grype."""

from __future__ import annotations

import logging
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.registry.client import RegistryClient
from regis.utils.grype import run_grype

logger = logging.getLogger(__name__)

#: Maps grype severity strings to the report's count field.
_SEVERITY_FIELD = {
    "Critical": "critical_count",
    "High": "high_count",
    "Medium": "medium_count",
    "Low": "low_count",
    "Negligible": "negligible_count",
    "Unknown": "unknown_count",
}


class CveAnalyzer(BaseAnalyzer):
    """Scan an image for vulnerabilities using grype."""

    name = "cve"
    schema_file = "analyzer/cve.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "fix-available",
                "description": "All vulnerabilities should be fixed if a patch exists.",
                "level": "warning",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.cve.fixed_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "All vulnerabilities with available fixes have been patched.",  # nosec B105
                    "fail": "Image has ${results.cve.fixed_count} vulnerabilities with available fixes.",
                },
            },
            {
                "slug": "cve-count",
                "description": "Max allowed violations for a given severity level.",
                "level": "warning",
                "tags": ["security"],
                "params": {"level": "critical", "max_count": 0},
                "condition": {
                    "<=": [
                        {
                            "get": [
                                {"var": "results.cve"},
                                {"cat": [{"var": "rule.params.level"}, "_count"]},
                            ]
                        },
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Number of ${rule.params.level} vulnerabilities is within limits.",  # nosec B105
                    "fail": "Image has ${results.cve.${rule.params.level}_count} ${rule.params.level} CVEs (max allowed: ${rule.params.max_count}).",
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
        """Run grype analysis and return a report dict."""
        if client.registry in ("docker.io", "registry-1.docker.io"):
            full_image = f"{repository}:{tag}"
        else:
            full_image = f"{client.registry}/{repository}:{tag}"

        data = run_grype(
            full_image,
            username=client.username,
            password=client.password,
            platform=platform,
        )

        counts = {field: 0 for field in _SEVERITY_FIELD.values()}
        fixed_count = 0
        grouped: dict[str, list[dict[str, Any]]] = {}

        for match in data.get("matches", []):
            vuln = match.get("vulnerability", {})
            artifact = match.get("artifact", {})
            severity = vuln.get("severity", "Unknown")
            counts[_SEVERITY_FIELD.get(severity, "unknown_count")] += 1

            fix = vuln.get("fix", {})
            if fix.get("state") == "fixed":
                fixed_count += 1
            fixed_versions = fix.get("versions") or []

            atype = artifact.get("type", "unknown")
            grouped.setdefault(atype, []).append(
                {
                    "VulnerabilityID": vuln.get("id", ""),
                    "PkgName": artifact.get("name", ""),
                    "InstalledVersion": artifact.get("version", ""),
                    "FixedVersion": fixed_versions[0] if fixed_versions else "",
                    "Severity": severity,
                    "Title": vuln.get("id", ""),
                    "Description": vuln.get("description", ""),
                }
            )

        targets = [
            {"Target": atype, "Vulnerabilities": vulns}
            for atype, vulns in sorted(grouped.items())
        ]

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "scanner_version": str(
                data.get("descriptor", {}).get("version", "unknown")
            ),
            "vulnerability_count": sum(counts.values()),
            **counts,
            "fixed_count": fixed_count,
            "targets": targets,
        }
