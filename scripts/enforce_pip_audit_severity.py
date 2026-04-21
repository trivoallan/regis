#!/usr/bin/env python3
"""Fail CI when pip-audit findings include HIGH/CRITICAL vulnerabilities."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

OSV_VULN_URL = "https://api.osv.dev/v1/vulns/"
SEVERITY_RANK = {"LOW": 1, "MODERATE": 2, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass
class Finding:
    package: str
    version: str
    vuln_id: str
    severity: str


def _extract_cvss_score(severity_entries: list[dict]) -> float | None:
    for severity in severity_entries:
        score = severity.get("score", "")
        if isinstance(score, str) and score.startswith("CVSS"):
            try:
                return float(score.rsplit("/", 1)[-1])
            except ValueError:
                continue
        if isinstance(score, (int, float)):
            return float(score)
    return None


def _score_to_level(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


def _fetch_severity(vuln_id: str, cache: dict[str, str | None]) -> str | None:
    if vuln_id in cache:
        return cache[vuln_id]

    request = urllib.request.Request(f"{OSV_VULN_URL}{vuln_id}", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        cache[vuln_id] = None
        return None

    score = _extract_cvss_score(payload.get("severity", []))
    if score is None:
        database_specific = payload.get("database_specific", {})
        normalized = str(database_specific.get("severity", "")).upper()
        if normalized in SEVERITY_RANK:
            cache[vuln_id] = normalized
            return normalized
        cache[vuln_id] = None
        return None

    level = _score_to_level(score)
    cache[vuln_id] = level
    return level


def _iter_findings(report: dict) -> list[Finding]:
    findings: list[Finding] = []
    cache: dict[str, str | None] = {}

    for dependency in report.get("dependencies", []):
        package = dependency.get("name", "unknown")
        version = dependency.get("version", "unknown")

        for vuln in dependency.get("vulns", []):
            candidate_ids = [vuln.get("id", "")]
            candidate_ids.extend(vuln.get("aliases", []))

            severity: str | None = None
            resolved_id = vuln.get("id", "unknown")
            for candidate_id in candidate_ids:
                if not candidate_id:
                    continue
                severity = _fetch_severity(candidate_id, cache)
                if severity:
                    resolved_id = candidate_id
                    break

            if severity is None:
                continue

            findings.append(
                Finding(
                    package=package,
                    version=version,
                    vuln_id=resolved_id,
                    severity=severity,
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, help="Path to pip-audit JSON report")
    parser.add_argument(
        "--min-severity",
        default="HIGH",
        choices=["LOW", "MEDIUM", "MODERATE", "HIGH", "CRITICAL"],
        help="Minimum severity threshold to fail on",
    )
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    findings = _iter_findings(report)

    min_rank = SEVERITY_RANK[args.min_severity]
    blocking = [finding for finding in findings if SEVERITY_RANK[finding.severity] >= min_rank]

    if not blocking:
        print("No pip-audit findings met the configured severity threshold.")
        return 0

    print(f"Found {len(blocking)} vulnerabilities at or above {args.min_severity}:")
    for finding in blocking:
        print(
            f"- {finding.package}=={finding.version}: {finding.vuln_id} ({finding.severity})"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
