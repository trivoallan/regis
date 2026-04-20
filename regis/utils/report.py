"""Report rendering and writing helpers."""

from __future__ import annotations

import json
import logging
import webbrowser
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

import click
import jsonschema

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
        click.echo(f"  Report ({fmt}) written to {out_path}", err=True)
    except PermissionError as exc:
        fallback_path = Path.cwd() / f"report.{fmt}"
        click.echo(
            f"  Warning: Failed to write to {out_path} ({exc}). Trying fallback to {fallback_path}",
            err=True,
        )
        try:
            fallback_path.write_text(rendered, encoding="utf-8")
            click.echo(f"  Report ({fmt}) written to {fallback_path}", err=True)
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
            click.echo(f"  {action} playbook: {pb_path}...", err=True)
            pb_def = load_playbook(pb_path)
            pb_result = evaluate(
                pb_def, analysis_report, source_name=Path(pb_path).stem
            )
            playbook_results.append(pb_result)

            if "html" not in formats or len(formats) > 1:
                summary_parts = []
                for section in pb_result.get("sections", []):
                    for lv_name, stats in section.get("levels_summary", {}).items():
                        summary_parts.append(
                            f"{lv_name}: {stats['passed']}/{stats['total']}"
                        )

                summary_str = " · ".join(summary_parts)
                rs = pb_result.get("rules_summary", {})
                passed_rules = rs.get("passed", [])
                total_rules = rs.get("total", [])
                passed_count = (
                    len(passed_rules)
                    if isinstance(passed_rules, list)
                    else passed_rules
                )
                total_count = (
                    len(total_rules) if isinstance(total_rules, list) else total_rules
                )
                rules_score = rs.get("score", pb_result["score"])
                click.echo(
                    f"    {summary_str} "
                    f"({passed_count}/{total_count} rules passed, "
                    f"{rules_score}%)\n",
                    err=True,
                )

                if show_rules and pb_result.get("rules"):
                    click.echo("    Rules Evaluation Summary:", err=True)
                    for r in pb_result["rules"]:
                        icon = "✅" if r["passed"] else "❌"
                        if r["status"] == "incomplete":
                            icon = "⚠️"
                        click.echo(f"      {icon} [{r['slug']}] {r['message']}")
                    click.echo("", err=True)

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


def render_and_save_reports(
    report: dict[str, Any],
    formats: list[str],
    output_template: str | None,
    output_dir_template: str | None,
    theme: str,
    pretty: bool,
    base_url: str = "/",
    open_browser: bool = False,
) -> None:
    """Render and save reports in requested formats."""
    for fmt in formats:
        if fmt == "html":
            from regis.report.docusaurus import build_report_site

            out_dir = format_output_path(output_dir_template or ".", report, "json")

            try:
                build_report_site(
                    report=report,
                    output_dir=out_dir,
                    base_url=base_url,
                    pretty=pretty,
                )
            except RuntimeError as exc:
                raise click.ClickException(str(exc)) from exc

            click.echo(
                f"  Report site generated at {out_dir}",
                err=True,
            )

            if open_browser:
                import http.server
                import socket
                import socketserver

                index_file = out_dir / "index.html"
                if not index_file.exists():
                    click.echo(
                        f"  Warning: Could not find index.html at {out_dir}. Browser not opened.",
                        err=True,
                    )
                    return

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", 0))
                    port = s.getsockname()[1]

                url = f"http://localhost:{port}"
                click.echo(f"  Starting local server at {url}", err=True)
                click.echo("  Press Ctrl+C to stop serving.", err=True)

                class ReportHandler(http.server.SimpleHTTPRequestHandler):
                    """Serve the generated report directory over HTTP for local preview."""

                    def __init__(self, *args, directory=str(out_dir), **kwargs):
                        super().__init__(*args, directory=directory, **kwargs)

                with socketserver.TCPServer(("", port), ReportHandler) as httpd:
                    webbrowser.open(url)
                    try:
                        httpd.serve_forever()
                    except KeyboardInterrupt:
                        click.echo("\n  Stopping server...", err=True)
                        httpd.shutdown()
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


def render_mr_templates(
    report: dict[str, Any], output_dir_template: str | None
) -> None:
    """Execute Cookiecutter templates for Merge Requests."""
    playbooks = report.get("playbooks", [])
    valid_mr_templates = []
    for pb in playbooks:
        for tmpl in pb.get("mr_templates", []):
            if tmpl not in valid_mr_templates:
                valid_mr_templates.append(tmpl)

    if valid_mr_templates:
        try:
            from cookiecutter.main import cookiecutter
        except ImportError:
            click.echo(
                "  Warning: cookiecutter not found. Cannot evaluate mr_templates.",
                err=True,
            )
        else:
            for tmpl_def in valid_mr_templates:
                tmpl_url = tmpl_def.get("url")
                tmpl_dir = tmpl_def.get("directory")
                click.echo(f"  Rendering MR template: {tmpl_url}...", err=True)
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
                    if tmpl_dir:
                        kwargs["directory"] = tmpl_dir

                    cookiecutter(tmpl_url, **kwargs)
                except Exception as exc:
                    click.echo(
                        f"  Warning: Failed to render template '{tmpl_url}': {exc}",
                        err=True,
                    )
