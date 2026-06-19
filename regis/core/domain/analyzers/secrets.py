"""Secrets analyzer — detects embedded credentials using trufflehog."""

from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404
from typing import Any

from regis.core.domain.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext

logger = logging.getLogger(__name__)


def _scanner_version() -> str:
    """Best-effort trufflehog version via ``trufflehog --version`` (stderr)."""
    path = shutil.which("trufflehog")
    if not path:
        return "unknown"
    try:
        result = subprocess.run(  # nosec B603
            [path, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    out = (result.stderr or result.stdout).strip()
    return out.splitlines()[0] if out else "unknown"


def _layer(finding: dict[str, Any]) -> str:
    """Extract the Docker layer digest from a trufflehog finding, if present."""
    docker = finding.get("SourceMetadata", {}).get("Data", {}).get("Docker", {})
    return str(docker.get("layer", ""))


class SecretsAnalyzer(BaseAnalyzer):
    """Scan an image for embedded secrets using trufflehog."""

    name = "secrets"
    schema_file = "analyzer/secrets.schema.json"

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "verified-secrets",
                "description": (
                    "No verified, active credentials should be embedded in the image."
                ),
                "level": "critical",
                "tags": ["security"],
                "condition": {"==": [{"var": "results.secrets.verified_count"}, 0]},
                "messages": {
                    "pass": "No verified secrets detected in the image.",  # nosec B105
                    "fail": (
                        "TruffleHog verified ${results.secrets.verified_count} "
                        "active credential(s) in the image."
                    ),
                },
            },
            {
                "slug": "secret-scan",
                "description": (
                    "No secrets or credentials should be embedded in the image."
                ),
                "level": "warning",
                "tags": ["security"],
                "condition": {"==": [{"var": "results.secrets.secrets_count"}, 0]},
                "messages": {
                    "pass": "No secrets detected in the image.",  # nosec B105
                    "fail": (
                        "TruffleHog detected ${results.secrets.secrets_count} "
                        "secret(s) in the image."
                    ),
                },
            },
        ]

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:
        """Run trufflehog analysis and return a report dict."""
        raw = ctx.tools.scan_secrets(ctx.image)
        repository = ctx.image.repository
        tag = ctx.image.tag

        findings = [
            {
                "DetectorName": f.get("DetectorName", ""),
                "Verified": bool(f.get("Verified", False)),
                "Redacted": f.get("Redacted", ""),
                "layer": _layer(f),
            }
            for f in raw
        ]
        verified_count = sum(1 for f in findings if f["Verified"])

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "scanner_version": _scanner_version(),
            "secrets_count": len(findings),
            "verified_count": verified_count,
            "findings": findings,
        }
