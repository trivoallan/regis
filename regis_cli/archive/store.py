"""Archive store — persists reports to a structured directory and maintains
manifest.json (index) and data.json (PowerBI-ready JSON array).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Keys extracted into the flat summary written to manifest.json / data.json
_SUMMARY_KEYS = [
    "id",
    "timestamp",
    "registry",
    "repository",
    "tag",
    "digest",
    "score",
    "tier",
    "rules_passed",
    "rules_total",
    "cve_critical",
    "cve_high",
    "cve_medium",
    "cve_low",
    "age_days",
    "sbom_component_count",
    "scorecard_score",
    "path",
]


def _make_summary(report: dict[str, Any], path: str) -> dict[str, Any]:
    """Extract a flat summary row from a full report dict."""
    req = report.get("request", {})
    registry = req.get("registry", "unknown")
    repository = req.get("repository", "unknown")
    tag = req.get("tag", "unknown")
    timestamp = req.get("timestamp") or datetime.now(timezone.utc).isoformat()

    # Normalise timestamp to a safe filesystem string for the id
    ts_safe = timestamp.replace(":", "-").replace("+", "").split(".")[0]
    entry_id = f"{registry}/{repository}/{tag}/{ts_safe}"

    # Rules summary — handle both list and int representations
    rs = report.get("rules_summary", {})
    passed_raw = rs.get("passed", 0)
    total_raw = rs.get("total", 0)
    rules_passed = (
        len(passed_raw) if isinstance(passed_raw, list) else int(passed_raw or 0)
    )
    rules_total = len(total_raw) if isinstance(total_raw, list) else int(total_raw or 0)
    score = int(rs.get("score", 0))

    # Tier — from top-level or playbook
    pb = report.get("playbook") or (report.get("playbooks") or [{}])[0]
    tier = report.get("tier") or (pb.get("tier") if isinstance(pb, dict) else None)

    # Trivy
    trivy = (report.get("results") or {}).get("trivy") or {}
    # Freshness
    freshness = (report.get("results") or {}).get("freshness") or {}
    # SBOM
    sbom = (report.get("results") or {}).get("sbom") or {}
    # Scorecard
    scorecard = (report.get("results") or {}).get("scorecarddev") or {}

    return {
        "id": entry_id,
        "timestamp": timestamp,
        "registry": registry,
        "repository": repository,
        "tag": tag,
        "digest": req.get("digest"),
        "score": score,
        "tier": tier,
        "rules_passed": rules_passed,
        "rules_total": rules_total,
        "cve_critical": trivy.get("critical_count"),
        "cve_high": trivy.get("high_count"),
        "cve_medium": trivy.get("medium_count"),
        "cve_low": trivy.get("low_count"),
        "age_days": freshness.get("age_days"),
        "sbom_component_count": sbom.get("component_count"),
        "scorecard_score": scorecard.get("score"),
        "path": path,
    }


def add_to_archive(
    report: dict[str, Any],
    archive_dir: Path,
    *,
    pretty: bool = True,
) -> Path:
    """Persist *report* into *archive_dir* and update manifest/data files.

    Directory layout::

        archive_dir/
          manifest.json          ← JSON array of summary objects (index)
          data.json              ← same content, PowerBI-ready JSON array
          {registry}/
            {repository}/
              {tag}/
                {timestamp}/
                  report.json

    Returns the path to the written report.json.
    """
    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    req = report.get("request", {})
    registry = _safe_segment(req.get("registry", "unknown"))
    repository = _safe_segment(req.get("repository", "unknown"))
    tag = _safe_segment(req.get("tag", "unknown"))
    timestamp = req.get("timestamp") or datetime.now(timezone.utc).isoformat()
    ts_safe = timestamp.replace(":", "-").replace("+", "").split(".")[0] + "Z"

    # Build directory path
    report_dir = archive_dir / registry / repository / tag / ts_safe
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.json"

    # Write full report
    indent = 2 if pretty else None
    report_path.write_text(
        json.dumps(report, indent=indent, default=str), encoding="utf-8"
    )
    logger.info("Archived report to %s", report_path)

    # Compute relative path for manifest
    relative_path = report_path.relative_to(archive_dir).as_posix()
    summary = _make_summary(report, relative_path)

    # Update manifest.json
    manifest_path = archive_dir / "manifest.json"
    manifest = _load_json_array(manifest_path)
    # Replace existing entry with same id, or append
    manifest = [e for e in manifest if e.get("id") != summary["id"]]
    manifest.append(summary)
    # Sort by timestamp descending (most recent first)
    manifest.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=indent, default=str), encoding="utf-8"
    )

    # data.json is identical to manifest.json (PowerBI reads JSON arrays natively)
    data_path = archive_dir / "data.json"
    data_path.write_text(
        json.dumps(manifest, indent=indent, default=str), encoding="utf-8"
    )

    return report_path


def _safe_segment(value: str) -> str:
    """Replace characters unsafe for directory names."""
    return value.replace("/", "_").replace("\\", "_").replace(":", "_")


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array from *path*, returning [] if missing or invalid."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read %s: %s — starting fresh", path, exc)
    return []
