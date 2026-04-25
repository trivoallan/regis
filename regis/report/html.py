"""Single-file HTML report renderer."""

from __future__ import annotations

import importlib.metadata
import json
from datetime import datetime, timezone
from importlib import resources
from typing import Any

import click
from jinja2 import BaseLoader, Environment


def render_html_single(report: dict[str, Any], sections: str = "all") -> str:
    """Render a self-contained single-file HTML report.

    Args:
        report: Full regis report dict.
        sections: "all" (default), "summary", or comma-separated analyzer slugs.

    Returns:
        Complete HTML string with inlined CSS, no external resources.
    """
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

    # Load template from package resources
    tmpl_path = resources.files("regis") / "templates" / "html" / "report.html.j2"
    tmpl_content = tmpl_path.read_text(encoding="utf-8")

    env = Environment(autoescape=True, loader=BaseLoader())

    template = env.from_string(tmpl_content)

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

    return template.render(
        report=report,
        image_ref=image_ref,
        show_details=show_details,
        filter_slugs=filter_slugs,
        regis_version=regis_version,
        generated_at=generated_at,
    )
