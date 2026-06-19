"""Single-file HTML report renderer."""

from __future__ import annotations

import importlib.metadata
from datetime import datetime, timezone
from importlib import resources
from typing import Any

import click
from jinja2 import BaseLoader, Environment

_BADGE_CSS = {"error": "failed", "warning": "warning", "success": "passed"}

# CVE severity strip: (display label / css class, source count key)
_SEVERITY_SPEC = [
    ("critical", "critical_count"),
    ("high", "high_count"),
    ("medium", "medium_count"),
    ("low", "low_count"),
]


def _build_context(report: dict[str, Any], sections: str) -> dict[str, Any]:
    """Build the full template context for a report (pure: no template I/O)."""
    # Parse sections directive
    if sections == "all":
        show_details = True
        filter_slugs: set[str] | None = None
    elif sections == "summary":
        show_details = False
        filter_slugs = None
    else:
        show_details = True
        filter_slugs = {s.strip() for s in sections.split(",") if s.strip()}
        available = set(report.get("results", {}).keys())
        for slug in sorted(filter_slugs - available):
            click.echo(f"  Warning: unknown section '{slug}' (ignored)", err=True)

    # Build image_ref string
    req = report.get("request", {})
    image_ref = req.get("image_ref") or (
        f"{req.get('registry', '')}/{req.get('repository', '')}:{req.get('tag', '')}"
    )

    try:
        regis_version = importlib.metadata.version("regis")
    except importlib.metadata.PackageNotFoundError:
        regis_version = "dev"

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    from regis.core.domain.playbook.verdict import (
        badge_emoji,
        build_verdict,
        format_counts,
        tier_label,
    )

    _v = build_verdict(report)
    verdict_view = None
    if _v.evaluated:
        verdict_view = {
            "headline": f"{tier_label(_v.tier, _v.tier_icon)} · {_v.score}/100",
            "score": _v.score,
            "counts": format_counts(_v),
            "badges": [
                {
                    "label": b.label,
                    "emoji": badge_emoji(b.klass),
                    "css": _BADGE_CSS.get(b.klass, "none"),
                }
                for b in _v.badges
            ],
            "failures": [
                {"slug": f.slug, "level": f.level, "message": f.message}
                for f in _v.failures
            ],
            "incompletes": [
                {"slug": i.slug, "level": i.level, "message": i.message}
                for i in _v.incompletes
            ],
        }

    triage = None
    if verdict_view is not None:
        triage = {
            "failures": verdict_view["failures"],
            "incompletes": verdict_view["incompletes"],
            "clear": not verdict_view["failures"] and not verdict_view["incompletes"],
        }

    failing_analyzers: set[str] = {a for f in _v.failures for a in f.analyzers}

    toc = [
        {
            "slug": name,
            "label": name,
            "status": "fail" if name in failing_analyzers else "pass",
        }
        for name in report.get("results", {})
        if filter_slugs is None or name in filter_slugs
    ]

    cve_result = report.get("results", {}).get("cve")
    severity = None
    if cve_result is not None:
        severity = [
            {"label": label, "css": label, "count": cve_result.get(key, 0)}
            for label, key in _SEVERITY_SPEC
        ]

    return {
        "report": report,
        "image_ref": image_ref,
        "show_details": show_details,
        "filter_slugs": filter_slugs,
        "regis_version": regis_version,
        "generated_at": generated_at,
        "verdict": verdict_view,
        "triage": triage,
        "toc": toc,
        "failing_analyzers": failing_analyzers,
        "severity": severity,
    }


def render_html_single(report: dict[str, Any], sections: str = "all") -> str:
    """Render a self-contained single-file HTML report.

    Args:
        report: Full regis report dict.
        sections: "all" (default), "summary", or comma-separated analyzer slugs.

    Returns:
        Complete HTML string with inlined CSS, no external resources.
    """
    context = _build_context(report, sections)

    tmpl_path = resources.files("regis") / "templates" / "html" / "report.html.j2"
    tmpl_content = tmpl_path.read_text(encoding="utf-8")

    env = Environment(autoescape=True, loader=BaseLoader())
    template = env.from_string(tmpl_content)

    return template.render(**context)
