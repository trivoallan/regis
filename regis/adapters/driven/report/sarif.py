"""Render playbook verdicts as SARIF 2.1.0 for GitHub Code Scanning et al.

Maps playbook *rule outcomes* (verdicts), not raw analyzer findings: each
evaluated rule becomes a reportingDescriptor, each breach a result. Regis'
three severity levels map to SARIF ``level`` plus a numeric ``security-severity``
(0-10) that GitHub reads to bucket Critical/High/Low.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

DOCS_BASE = "https://trivoallan.github.io/regis/docs/reference/rules"

# Regis level -> (SARIF level, security-severity). security-severity buckets in
# GitHub: >=9.0 Critical, 7.0-8.9 High, 4.0-6.9 Medium, <4.0 Low.
_LEVEL_MAP: dict[str, tuple[str, str]] = {
    "critical": ("error", "9.0"),
    "warning": ("warning", "7.0"),
    "info": ("note", "2.0"),
}
_DEFAULT_LEVEL = ("note", "2.0")


def _sarif_level(regis_level: Any) -> tuple[str, str]:
    return _LEVEL_MAP.get(str(regis_level).lower(), _DEFAULT_LEVEL)


def _help_uri(rule: dict[str, Any]) -> str | None:
    criterion = rule.get("criterion")
    if not criterion:
        return None
    analyzers = rule.get("analyzers") or []
    category = analyzers[0] if analyzers else "core"
    return f"{DOCS_BASE}/{category}/{criterion}"


def _fingerprint(slug: str, req: dict[str, Any]) -> str:
    # Stable across rebuilds: keyed on (rule, repo:tag), never the digest.
    key = f"{slug}|{req.get('registry')}/{req.get('repository')}:{req.get('tag')}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def build_sarif(
    report: dict[str, Any],
    *,
    report_url: str = "",
    dockerfile: str | None = "Dockerfile",
) -> dict[str, Any]:
    """Build the SARIF document (dict) from an evaluated report."""
    req = report.get("request", {})
    rules = report.get("rules", []) or []

    descriptors: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    for r in rules:
        slug = r.get("slug", "")
        index[slug] = len(descriptors)
        level, sev = _sarif_level(r.get("level", "info"))
        descriptor: dict[str, Any] = {
            "id": slug,
            "name": "".join(p.capitalize() for p in slug.split("-")),
            "shortDescription": {"text": r.get("description") or slug},
            "defaultConfiguration": {"level": level},
            "properties": {
                "tags": r.get("tags", []),
                "security-severity": sev,
                "regis-level": r.get("level"),
            },
        }
        uri = _help_uri(r)
        if uri:
            descriptor["helpUri"] = uri
        descriptors.append(descriptor)

    results: list[dict[str, Any]] = []
    for r in rules:
        if r.get("status") != "failed":  # breaches only (skip pass + incomplete)
            continue
        slug = r.get("slug", "")
        level, sev = _sarif_level(r.get("level", "info"))
        text = r.get("message") or slug
        markdown = text + (
            f"  \n[Full Regis report]({report_url})" if report_url else ""
        )
        result: dict[str, Any] = {
            "ruleId": slug,
            "ruleIndex": index[slug],
            # kind="fail" marks this as a governance verdict, not a vulnerability:
            # houba keys on result.kind to bucket it under policy.* instead of
            # vuln.*. ponytail: only breaches are emitted, so no "pass" branch
            # (add kind="pass" + level="none" if passing checks ever become results).
            "kind": "fail",
            "level": level,
            "message": {"text": text, "markdown": markdown},
            "partialFingerprints": {"regisRuleRepo/v1": _fingerprint(slug, req)},
            "properties": {
                "security-severity": sev,
                "regis-level": r.get("level"),
                "image": req.get("url"),
            },
        }
        # GitHub Code Scanning rejects results without a location, so every
        # result is anchored at the Dockerfile (the artifact the image was built
        # from) by default. Pass dockerfile=None only for a consumer that
        # tolerates location-less results.
        if dockerfile:
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": dockerfile},
                        "region": {"startLine": 1},
                    }
                }
            ]
        results.append(result)

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Regis",
                        "informationUri": "https://github.com/trivoallan/regis",
                        "version": str(report.get("version", "")),
                        "rules": descriptors,
                    }
                },
                "automationDetails": {"id": f"regis/{req.get('repository')}"},
                "results": results,
            }
        ],
    }


def render_sarif(
    report: dict[str, Any],
    *,
    report_url: str = "",
    dockerfile: str | None = "Dockerfile",
) -> str:
    """Render the report as a SARIF 2.1.0 JSON string."""
    return json.dumps(
        build_sarif(report, report_url=report_url, dockerfile=dockerfile),
        indent=2,
        ensure_ascii=False,
    )
