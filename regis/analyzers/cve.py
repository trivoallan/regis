"""CVE analyzer — scans images for vulnerabilities using grype."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from regis.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext

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
    def default_criteria(cls) -> list[dict[str, Any]]:
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
                        {"var": "criterion.params.max_count"},
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
                                {"cat": [{"var": "criterion.params.level"}, "_count"]},
                            ]
                        },
                        {"var": "criterion.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Number of ${criterion.params.level} vulnerabilities is within limits.",  # nosec B105
                    "fail": "Image has ${results.cve.${criterion.params.level}_count} ${criterion.params.level} CVEs (max allowed: ${criterion.params.max_count}).",
                },
            },
        ]

    @staticmethod
    def _source_from_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
        """Build the source freshness block from grype's descriptor.db.status."""
        status = (descriptor.get("db") or {}).get("status") or {}
        source: dict[str, Any] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        if status.get("built"):
            source["built_at"] = status["built"]
        if status.get("schemaVersion"):
            source["version"] = status["schemaVersion"]
        frm = status.get("from") or ""
        if frm:
            checksum = parse_qs(urlparse(frm).query).get("checksum", [None])[0]
            if checksum:
                source["checksum"] = unquote(checksum)
        return source

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:
        """Run grype analysis and return a report dict."""
        data = ctx.tools.scan_vulnerabilities(ctx.image)
        repository = ctx.image.repository
        tag = ctx.image.tag

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
                    "Severity": severity.upper(),
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
            "source": self._source_from_descriptor(data.get("descriptor", {})),
        }
