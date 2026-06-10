"""Report rendering and writing helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

import click
import jsonschema

logger = logging.getLogger(__name__)

REPORT_SCHEMA_VERSION = 5
"""Current report-structure contract version (see report.schema.json).

v5 removed the ``snapshot_date`` field (an editorial doc-site marker, not a
data-freshness indicator).  v4 removed the legacy
``pages``/``sections``/``scorecards``/``widgets`` rendering subsystem (and the
per-section ``levels_summary``/``tags_summary``); playbook results are now
rules-based only.
"""


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


def write_report(
    dir_tmpl: str,
    file_tmpl: str,
    report: dict[str, Any],
    fmt: str,
    rendered: str,
) -> None:
    """Write the rendered report to disk, or fallback if permissions fail."""
    out_dir = format_output_path(dir_tmpl, report, fmt)
    out_file = format_output_path(file_tmpl, report, fmt)
    out_path = (out_dir / out_file).resolve()

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        _echo_info(f"  Report ({fmt}) written to {out_path}", err=True)
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


def evaluate_playbooks(
    playbook_paths: tuple[str, ...],
    analysis_report: dict[str, Any],
    formats: list[str],
    show_rules: bool = False,
) -> list[dict[str, Any]]:
    """Load and evaluate playbooks, returning the list of results."""
    from regis.playbook.engine import evaluate, load_playbook
    from regis.playbook.loader import PlaybookVersionError

    playbook_results = []
    if not playbook_paths:
        import importlib.resources

        default_pb = importlib.resources.files("regis") / "playbooks" / "default"
        if default_pb.is_dir():
            playbook_paths = (str(default_pb),)

    if playbook_paths:
        for pb_path in playbook_paths:
            is_remote = isinstance(pb_path, str) and (
                pb_path.startswith("http://") or pb_path.startswith("https://")
            )
            action = "Downloading" if is_remote else "Evaluating"
            _echo_info(f"  {action} playbook: {pb_path}...", err=True)
            try:
                pb_def = load_playbook(pb_path)
            except PlaybookVersionError as exc:
                raise click.ClickException(
                    f"Failed to load playbook '{pb_path}': {exc}"
                ) from exc
            except jsonschema.ValidationError as exc:
                raise click.ClickException(
                    f"Playbook '{pb_path}' failed schema validation: {exc.message}"
                ) from exc
            pb_result = evaluate(
                pb_def, analysis_report, source_name=Path(pb_path).stem
            )
            playbook_results.append(pb_result)

            rs = pb_result.get("rules_summary", {})
            passed_rules = rs.get("passed", [])
            total_rules = rs.get("total", [])
            passed_count = (
                len(passed_rules) if isinstance(passed_rules, list) else passed_rules
            )
            total_count = (
                len(total_rules) if isinstance(total_rules, list) else total_rules
            )
            rules_score = rs.get("score", pb_result["score"])
            _echo_info(
                f"    ({passed_count}/{total_count} rules passed, {rules_score}%)\n",
                err=True,
            )

            if show_rules and pb_result.get("rules"):
                _echo_info("    Rules Evaluation Summary:", err=True)
                for r in pb_result["rules"]:
                    icon = "✅" if r["passed"] else "❌"
                    if r["status"] == "incomplete":
                        icon = "⚠️"
                    _echo_info(f"      {icon} [{r['slug']}] {r['message']}")
                _echo_info("", err=True)

    return playbook_results


def run_playbooks(
    playbook_paths: tuple[str, ...],
    analysis_report: dict[str, Any],
    formats: list[str],
    show_rules: bool = False,
) -> dict[str, Any]:
    """Load and evaluate playbooks against an analysis report."""
    playbook_results = evaluate_playbooks(
        playbook_paths, analysis_report, formats, show_rules
    )

    final_report = {**analysis_report}
    if playbook_results:
        final_report["playbooks"] = playbook_results
        final_report["playbook"] = playbook_results[0]

    all_links = []
    for pb_res in playbook_results:
        for link_def in pb_res.get("links", []):
            if link_def not in all_links:
                all_links.append(link_def)

    if all_links:
        final_report["links"] = all_links

    return final_report


def ensure_schema_version(report: dict[str, Any]) -> dict[str, Any]:
    """Stamp `schemaVersion` on a report if absent. Backfills legacy reports.

    Mutates `report` in place and returns it. Existing values are preserved so a
    future report carrying a higher version is never silently downgraded.
    """
    report.setdefault("schemaVersion", REPORT_SCHEMA_VERSION)
    return report


def validate_report(report: dict[str, Any]) -> None:
    """Validate a final report against its schema."""
    from referencing import Registry, Resource

    schemas_dir = resources.files("regis.schemas")
    registry = Registry()
    report_schema = None
    base_uri = "https://trivoallan.github.io/regis/schemas/"

    def _get_all_schemas(node: Any, prefix: str = "") -> list[tuple[str, Any]]:
        found = []
        for item in node.iterdir():
            rel_path = f"{prefix}/{item.name}" if prefix else item.name
            if item.is_dir():
                found.extend(_get_all_schemas(item, rel_path))
            elif item.name.endswith(".json"):
                found.append((rel_path, item))
        return found

    for rel_path, schema_file in _get_all_schemas(schemas_dir):
        schema_data = json.loads(schema_file.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema_data)

        registry = registry.with_resource(uri=rel_path, resource=resource)
        registry = registry.with_resource(uri=schema_file.name, resource=resource)
        registry = registry.with_resource(uri=base_uri + rel_path, resource=resource)
        registry = registry.with_resource(
            uri=base_uri + schema_file.name, resource=resource
        )

        if "$id" in schema_data:
            registry = registry.with_resource(uri=schema_data["$id"], resource=resource)

        if schema_file.name == "report.schema.json":
            report_schema = schema_data

    if report_schema:
        from jsonschema.validators import validator_for

        try:
            validator_cls = validator_for(report_schema)
            validator = validator_cls(report_schema, registry=registry)
            validator.validate(instance=report)
        except jsonschema.ValidationError as exc:
            raise click.ClickException(
                f"Report schema validation failed: {exc.message}"
            ) from exc


def _verdict_markdown(report: dict[str, Any]) -> list[str]:
    """Render the verdict header (tier · score, badges, failed rules) as md lines."""
    from regis.playbook.verdict import (
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
) -> None:
    """Render and save reports in requested formats."""
    for fmt in formats:
        if fmt == "html":
            from regis.report.html import render_html_single

            rendered = render_html_single(report, sections=sections)
            file_tmpl = output_template or "report.html"
            write_report(
                dir_tmpl=output_dir_template or ".",
                file_tmpl=file_tmpl,
                report=report,
                fmt=fmt,
                rendered=rendered,
            )
        elif fmt == "md":
            rendered = _render_markdown(report)
            file_tmpl = output_template or "report.md"
            write_report(
                dir_tmpl=output_dir_template or ".",
                file_tmpl=file_tmpl,
                report=report,
                fmt=fmt,
                rendered=rendered,
            )
        else:
            indent = 2 if pretty else None
            rendered = json.dumps(report, indent=indent, ensure_ascii=False)
            file_tmpl = output_template or f"report.{fmt}"
            write_report(
                dir_tmpl=output_dir_template or ".",
                file_tmpl=file_tmpl,
                report=report,
                fmt=fmt,
                rendered=rendered,
            )


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
