#!/usr/bin/env python3
"""Fail CI when pip-audit findings include HIGH/CRITICAL vulnerabilities."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

OSV_QUERY_BATCH_URL = "https://api.osv.dev/v1/querybatch"
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
        if isinstance(score, str):
            try:
                if score.startswith("CVSS:"):
                    return float(score.rsplit("/", 1)[-1])
                return float(score)
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


def _payload_to_severity(payload: dict) -> str | None:
    score = _extract_cvss_score(payload.get("severity", []))
    if score is not None:
        return _score_to_level(score)
    database_specific = payload.get("database_specific", {})
    normalized = str(database_specific.get("severity", "")).upper()
    if normalized in SEVERITY_RANK:
        return normalized
    return None


def _fetch_severities(vuln_ids: Iterable[str], cache: dict[str, str | None]) -> None:
    ids = [vuln_id for vuln_id in vuln_ids if vuln_id and vuln_id not in cache]
    if not ids:
        return

    body = json.dumps({"queries": [{"id": vuln_id} for vuln_id in ids]}).encode("utf-8")
    request = urllib.request.Request(
        OSV_QUERY_BATCH_URL,
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        for vuln_id in ids:
            cache[vuln_id] = None
        return

    results = payload.get("results", [])
    for index, vuln_id in enumerate(ids):
        severity: str | None = None
        result = results[index] if index < len(results) else {}
        vulns = []
        if isinstance(result, dict):
            if isinstance(result.get("vulns"), list):
                vulns = result.get("vulns", [])
            elif isinstance(result.get("vuln"), dict):
                vulns = [result.get("vuln")]

        for vuln_payload in vulns:
            if not isinstance(vuln_payload, dict):
                continue
            severity = _payload_to_severity(vuln_payload)
            if severity:
                break
        cache[vuln_id] = severity


def _iter_findings(report: dict) -> list[Finding]:
    findings: list[Finding] = []
    cache: dict[str, str | None] = {}
    candidate_ids: set[str] = set()

    for dependency in report.get("dependencies", []):
        for vuln in dependency.get("vulns", []):
            vuln_id = vuln.get("id", "")
            if vuln_id:
                candidate_ids.add(vuln_id)
            for alias in vuln.get("aliases", []):
                if alias:
                    candidate_ids.add(alias)

    _fetch_severities(candidate_ids, cache)

    for dependency in report.get("dependencies", []):
        package = dependency.get("name", "unknown")
        version = dependency.get("version", "unknown")

        for vuln in dependency.get("vulns", []):
            candidate_ids = [vuln.get("id", "")]
            candidate_ids.extend(vuln.get("aliases", []))

            severity: str | None = None
            resolved_id = vuln.get("id") or "UNKNOWN_ID"
            for candidate_id in candidate_ids:
                if not candidate_id:
                    continue
                severity = cache.get(candidate_id)
                if severity:
                    resolved_id = candidate_id
                    break

            if severity is None:
                findings.append(
                    Finding(
                        package=package,
                        version=version,
                        vuln_id=resolved_id,
                        severity="UNKNOWN",
                    )
                )
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
    blocking = [
        finding
        for finding in findings
        if finding.severity in SEVERITY_RANK
        and SEVERITY_RANK[finding.severity] >= min_rank
    ]
    unknown = [finding for finding in findings if finding.severity == "UNKNOWN"]

    if not blocking and not unknown:
        print("No pip-audit findings met the configured severity threshold.")
        return 0

    if blocking:
        print(f"Found {len(blocking)} vulnerabilities at or above {args.min_severity}:")
    for finding in blocking:
        print(
            f"- {finding.package}=={finding.version}: {finding.vuln_id} ({finding.severity})"
        )

    if unknown:
        print(
            f"Found {len(unknown)} vulnerabilities with unknown severity; "
            "failing closed to avoid bypassing the security gate:"
        )
        for finding in unknown:
            print(
                f"- {finding.package}=={finding.version}: {finding.vuln_id} (UNKNOWN)"
            )

    return 1


if __name__ == "__main__":
    sys.exit(main())
