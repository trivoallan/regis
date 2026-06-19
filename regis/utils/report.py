"""Report rendering and writing helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

import click

from regis.core.domain.errors import PlaybookError
from regis.core.model.report import REPORT_SCHEMA_VERSION  # re-export for back-compat

__all__ = ["REPORT_SCHEMA_VERSION"]

logger = logging.getLogger(__name__)


def format_output_path(template: str, report: dict[str, Any], fmt: str) -> Path:
    """Format an output path template using data from the report."""
    req = report.get("request", {})
    scorecards = report.get("scorecards", [])
    sc = report.get("scorecard") or (scorecards[0] if scorecards else {})

    repo = req.get("repository", "unknown").replace("/", "-").replace(":", "-")

    ts_str = req.get("timestamp", "")
    try:
        ts = datetime.fromisoformat(ts_str)
        timestamp = ts.strftime("%Y%m%d-%H%M%S")
    except (ValueError, TypeError):
        timestamp = ts_str.replace(":", "-")

    context = {
        "repository": repo,
        "tag": req.get("tag", "latest"),
        "digest": req.get("digest", req.get("tag", "latest")),
        "registry": req.get("registry", "unknown"),
        "timestamp": timestamp,
        "format": fmt,
        "level": sc.get("level", "none"),
        "score": sc.get("score", 0),
    }

    try:
        resolved = template.format(**context)
    except KeyError as exc:
        logger.warning(f"Could not format output path '{template}': missing key {exc}")
        resolved = template

    return Path(resolved)


def _quiet() -> bool:
    """Return True when --quiet was set on the current Click context."""
    ctx = click.get_current_context(silent=True)
    return bool(ctx and ctx.obj and ctx.obj.get("quiet"))


def _echo_info(msg: str, **kwargs) -> None:
    """click.echo wrapper that respects the active --quiet flag."""
    if not _quiet():
        click.echo(msg, **kwargs)


def _echo_progress(msg: str) -> None:
    """Progress sink for the core playbook runner — echoes to stderr."""
    _echo_info(msg, err=True)


def write_report(
    dir_tmpl: str,
    file_tmpl: str,
    report: dict[str, Any],
    fmt: str,
    rendered: str,
) -> Path:
    """Write the rendered report to disk (or a cwd fallback); return the path written."""
    out_dir = format_output_path(dir_tmpl, report, fmt)
    out_file = format_output_path(file_tmpl, report, fmt)
    out_path = (out_dir / out_file).resolve()

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        _echo_info(f"  Report ({fmt}) written to {out_path}", err=True)
        return out_path
    except PermissionError as exc:
        fallback_path = Path.cwd() / f"report.{fmt}"
        # Permission warning is non-fatal but actionable — keep it visible.
        click.echo(
            f"  Warning: Failed to write to {out_path} ({exc}). Trying fallback to {fallback_path}",
            err=True,
        )
        try:
            fallback_path.write_text(rendered, encoding="utf-8")
            _echo_info(f"  Report ({fmt}) written to {fallback_path}", err=True)
            return fallback_path
        except PermissionError as inner_exc:
            raise click.ClickException(
                f"Failed to write report: Permission denied for both {out_path} and fallback."
            ) from inner_exc


def set_nested_value(d: dict[str, Any], dot_key: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation for keys."""
    keys = dot_key.split(".")
    for key in keys[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def escape_jinja(obj: Any) -> Any:
    """Recursively escape Jinja brackets in dictionary values.

    Cookiecutter recursively evaluates extra_context using Jinja2 before
    template processing. If the context contains strings like '{{ variable }}',
    it will throw UndefinedErrors unless those variables are in the global scope.
    We wrap such strings in {% raw %}...{% endraw %} so they are passed verbatim.
    """
    if isinstance(obj, dict):
        return {k: escape_jinja(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [escape_jinja(v) for v in obj]
    elif isinstance(obj, str):
        if "{{" in obj or "{%" in obj:
            return f"{{% raw %}}{obj}{{% endraw %}}"
        return obj
    return obj


def run_playbooks(
    playbook_paths: tuple[str, ...],
    analysis_report: dict[str, Any],
    formats: list[str],
    show_rules: bool = False,
) -> dict[str, Any]:
    """Load and evaluate playbooks against an analysis report.

    Delegates to the click-free core implementation and translates
    :class:`~regis.core.domain.errors.PlaybookError` into
    ``click.ClickException`` at the CLI boundary.
    """
    from regis.core.application.playbook_runner import run_playbooks as _core_run

    try:
        return _core_run(
            playbook_paths,
            analysis_report,
            show_rules=show_rules,
            on_progress=_echo_progress,
        )
    except PlaybookError as exc:
        raise click.ClickException(str(exc)) from exc


def ensure_schema_version(report: dict[str, Any]) -> dict[str, Any]:
    """Stamp `schemaVersion` on a report if absent. Backfills legacy reports.

    Mutates `report` in place and returns it. Existing values are preserved so a
    future report carrying a higher version is never silently downgraded.
    """
    report.setdefault("schemaVersion", REPORT_SCHEMA_VERSION)
    return report


def validate_report(report: dict[str, Any]) -> None:
    """Validate a final report against its schema.

    Delegates to the click-free core implementation and translates
    :class:`~regis.core.domain.errors.PlaybookError` into
    ``click.ClickException`` at the CLI boundary.
    """
    from regis.core.application.playbook_runner import validate_report as _core_validate

    try:
        _core_validate(report)
    except PlaybookError as exc:
        raise click.ClickException(str(exc)) from exc


def _verdict_markdown(report: dict[str, Any]) -> list[str]:
    """Render the verdict header (tier · score, badges, failed rules) as md lines."""
    from regis.core.domain.playbook.verdict import (
        badge_emoji,
        build_verdict,
        format_counts,
        tier_label,
    )

    v = build_verdict(report)
    if not v.evaluated:
        return []

    lines = [f"## {tier_label(v.tier, v.tier_icon)} · {v.score}/100", ""]
    lines += [f"**{format_counts(v)}**", ""]

    if v.badges:
        lines += [" · ".join(f"{badge_emoji(b.klass)} {b.label}" for b in v.badges), ""]

    if v.failures or v.incompletes:

        def _cell(value: str) -> str:
            # Rule messages are free-form interpolated text; escape pipes and
            # collapse newlines so a row never breaks the table.
            return value.replace("|", "\\|").replace("\n", " ")

        lines += ["| | Rule | Level | Result |", "| --- | --- | --- | --- |"]
        for f in v.failures:
            lines.append(
                f"| ✗ | {_cell(f.slug)} | {_cell(f.level)} | {_cell(f.message)} |"
            )
        for i in v.incompletes:
            lines.append(
                f"| ⚠ | {_cell(i.slug)} | {_cell(i.level)} | {_cell(i.message)} |"
            )
        lines.append("")

    return lines


def _render_markdown(report: dict[str, Any]) -> str:
    """Render a Markdown summary from a regis report dict."""
    request = report.get("request", {})
    image_ref = request.get("image_ref") or (
        f"{request.get('registry', '')}/{request.get('repository', '')}:{request.get('tag', '')}"
    )
    lines: list[str] = [f"# {image_ref}", ""]
    lines += _verdict_markdown(report)

    timestamp = request.get("timestamp") or report.get("timestamp")
    if timestamp:
        lines += [f"**Analysis date:** {timestamp}", ""]

    playbooks = report.get("playbooks", [])
    if playbooks:
        lines += ["## Playbook results", ""]
        lines += ["| Playbook | Verdict | Failing rules |", "| --- | --- | --- |"]
        for pb in playbooks:
            name = pb.get("name", "")
            verdict = pb.get("verdict", "")
            failing = sum(1 for r in pb.get("rules", []) if r.get("result") is False)
            lines.append(f"| {name} | {verdict} | {failing} |")
        lines.append("")

    return "\n".join(lines)


def render_and_save_reports(
    report: dict[str, Any],
    formats: list[str],
    output_template: str | None,
    output_dir_template: str | None,
    theme: str,
    pretty: bool,
    sections: str = "all",
) -> list[Path]:
    """Render and save reports in requested formats; return the written paths."""
    paths: list[Path] = []
    for fmt in formats:
        if fmt == "html":
            from regis.adapters.driven.report.html import render_html_single

            rendered = render_html_single(report, sections=sections)
            file_tmpl = output_template or "report.html"
            paths.append(
                write_report(
                    dir_tmpl=output_dir_template or ".",
                    file_tmpl=file_tmpl,
                    report=report,
                    fmt=fmt,
                    rendered=rendered,
                )
            )
        elif fmt == "md":
            rendered = _render_markdown(report)
            file_tmpl = output_template or "report.md"
            paths.append(
                write_report(
                    dir_tmpl=output_dir_template or ".",
                    file_tmpl=file_tmpl,
                    report=report,
                    fmt=fmt,
                    rendered=rendered,
                )
            )
        else:
            indent = 2 if pretty else None
            rendered = json.dumps(report, indent=indent, ensure_ascii=False)
            file_tmpl = output_template or f"report.{fmt}"
            paths.append(
                write_report(
                    dir_tmpl=output_dir_template or ".",
                    file_tmpl=file_tmpl,
                    report=report,
                    fmt=fmt,
                    rendered=rendered,
                )
            )
    return paths


def render_presentation_templates(
    report: dict[str, Any], output_dir_template: str | None
) -> None:
    """Execute Cookiecutter templates surfaced by playbook presentation directives."""
    playbooks = report.get("playbooks", [])
    valid_templates = []
    for pb in playbooks:
        for tmpl in pb.get("templates", []):
            if tmpl not in valid_templates:
                valid_templates.append(tmpl)

    if valid_templates:
        try:
            from cookiecutter.main import cookiecutter
        except ImportError:
            click.echo(
                "  Warning: cookiecutter not found. Cannot evaluate presentation templates.",
                err=True,
            )
        else:
            for tmpl_def in valid_templates:
                tmpl_url = tmpl_def.get("url")
                tmpl_pkg = tmpl_def.get("package")
                tmpl_dir = tmpl_def.get("directory")
                label = tmpl_url or tmpl_pkg
                click.echo(f"  Rendering presentation template: {label}...", err=True)
                try:
                    out_dir = format_output_path(
                        output_dir_template or ".", report, "json"
                    )
                    out_dir.mkdir(parents=True, exist_ok=True)

                    kwargs = {
                        "no_input": True,
                        "extra_context": {"regis": escape_jinja(report)},
                        "output_dir": str(out_dir),
                        "overwrite_if_exists": True,
                    }

                    if tmpl_pkg:
                        # Packaged template: resolve to a local path so Cookiecutter
                        # renders in-place (no git clone / network access).
                        base = resources.files(tmpl_pkg)
                        template_arg = str(base / tmpl_dir) if tmpl_dir else str(base)
                    else:
                        template_arg = tmpl_url
                        if tmpl_dir:
                            kwargs["directory"] = tmpl_dir

                    cookiecutter(template_arg, **kwargs)
                except Exception as exc:
                    click.echo(
                        f"  Warning: Failed to render template '{label}': {exc}",
                        err=True,
                    )
