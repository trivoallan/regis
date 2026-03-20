"""CLI entry point for regis-cli."""

from __future__ import annotations

import json
import logging
import sys
import webbrowser
from datetime import datetime, timezone
from importlib import resources
from importlib.metadata import entry_points, version
from pathlib import Path
from typing import Any

import click
import jsonschema

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.gitlab_cli import gitlab_cmd
from regis_cli.registry.client import RegistryClient, RegistryError
from regis_cli.registry.parser import parse_image_url

logger = logging.getLogger(__name__)


def _discover_analyzers() -> dict[str, type[BaseAnalyzer]]:
    """Discover all registered analyzers via entry_points."""
    eps = entry_points(group="regis_cli.analyzers")
    discovered: dict[str, type[BaseAnalyzer]] = {}
    for ep in eps:
        try:
            cls = ep.load()
            discovered[ep.name] = cls
        except Exception:
            logger.warning("Failed to load analyzer '%s'", ep.name, exc_info=True)
    return discovered


def _format_output_path(template: str, report: dict[str, Any], fmt: str) -> Path:
    """Format an output path template using data from the report."""
    req = report.get("request", {})
    # Provide a 'scorecard' variable if not present directly.
    scorecards = report.get("scorecards", [])
    sc = report.get("scorecard") or (scorecards[0] if scorecards else {})

    # Sanitize repository name for filesystem
    repo = req.get("repository", "unknown").replace("/", "-").replace(":", "-")

    # Format timestamp for filesystem
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

    # Sanitize characters strictly to prevent generating invalid filenames
    sanitized = resolved  # re.sub(r"[^\w\-./\\]+", "_", resolved)

    return Path(sanitized)


def _write_report(
    dir_tmpl: str,
    file_tmpl: str,
    report: dict[str, Any],
    fmt: str,
    rendered: str,
) -> None:
    """Write the rendered report to disk, or fallback if permissions fail."""
    out_dir = _format_output_path(dir_tmpl, report, fmt)
    out_file = _format_output_path(file_tmpl, report, fmt)
    out_path = (out_dir / out_file).resolve()

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        click.echo(f"  Report ({fmt}) written to {out_path}", err=True)
    except PermissionError as exc:
        # If we can't write to the template dir, try current dir as fallback
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


def _set_nested_value(d: dict[str, Any], dot_key: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation for keys."""
    keys = dot_key.split(".")
    for key in keys[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def _escape_jinja(obj: Any) -> Any:
    """Recursively escape Jinja brackets in dictionary values.

    Cookiecutter recursively evaluates extra_context using Jinja2 before
    template processing. If the context contains strings like '{{ variable }}',
    it will throw UndefinedErrors unless those variables are in the global scope.
    We wrap such strings in {% raw %}...{% endraw %} so they are passed verbatim.
    """
    if isinstance(obj, dict):
        return {k: _escape_jinja(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_escape_jinja(v) for v in obj]
    elif isinstance(obj, str):
        if "{{" in obj or "{%" in obj:
            return f"{{% raw %}}{obj}{{% endraw %}}"
        return obj
    return obj


@click.group()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose (DEBUG) logging.",
)
def main(verbose: bool) -> None:
    """regis-cli — Docker Registry Analysis CLI."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


# Register subcommands
main.add_command(gitlab_cmd, name="gitlab")


def _run_playbooks(
    playbook_paths: tuple[str, ...],
    analysis_report: dict[str, Any],
    formats: list[str],
    show_rules: bool = False,
) -> dict[str, Any]:
    """Load and evaluate playbooks against an analysis report."""
    from regis_cli.playbook.engine import evaluate, load_playbook

    playbook_results = []
    if not playbook_paths:
        import importlib.resources

        default_pb = (
            importlib.resources.files("regis_cli") / "playbooks" / "default.yaml"
        )
        if default_pb.is_file():
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

            # Print summary for EACH playbook if in CLI mode
            if "html" not in formats or len(formats) > 1:
                summary_parts = []
                for section in pb_result.get("sections", []):
                    for lv_name, stats in section.get("levels_summary", {}).items():
                        summary_parts.append(
                            f"{lv_name}: {stats['passed']}/{stats['total']}"
                        )

                summary_str = " · ".join(summary_parts)
                click.echo(
                    f"    {summary_str} "
                    f"({pb_result['passed_scorecards']}/{pb_result['total_scorecards']} scorecards passed, "
                    f"{pb_result['score']}%)\n",
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

    # Build the final report.
    final_report = {
        **analysis_report,
    }
    if playbook_results:
        final_report["playbooks"] = playbook_results
        # For backward compatibility (or simplicity), keep 'playbook' pointing to the first result.
        final_report["playbook"] = playbook_results[0]

    # Extract evaluated links from playbooks
    all_links = []
    for pb_res in playbook_results:
        for link_def in pb_res.get("links", []):
            if link_def not in all_links:
                all_links.append(link_def)

    if all_links:
        final_report["links"] = all_links

    return final_report


def _validate_report(report: dict[str, Any]) -> None:
    """Validate a final report against its schema."""
    from referencing import Registry, Resource

    schemas_dir = resources.files("regis_cli.schemas")
    registry = Registry()
    report_schema = None
    base_uri = "https://trivoallan.github.io/regis-cli/schemas/"

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

        # Register both by relative path and by $id if available.
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


def _render_and_save_reports(
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
            from regis_cli.report.docusaurus import build_report_site

            out_dir = _format_output_path(output_dir_template or ".", report, "json")

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

                # Find a free port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", 0))
                    port = s.getsockname()[1]

                url = f"http://localhost:{port}"
                click.echo(f"  Starting local server at {url}", err=True)
                click.echo("  Press Ctrl+C to stop serving.", err=True)

                class ReportHandler(http.server.SimpleHTTPRequestHandler):
                    def __init__(self, *args, directory=str(out_dir), **kwargs):
                        super().__init__(*args, directory=directory, **kwargs)

                # Use a small timeout to allow for periodic checks if needed,
                # though serve_forever is typical for this use case.
                with socketserver.TCPServer(("", port), ReportHandler) as httpd:
                    webbrowser.open(url)
                    try:
                        httpd.serve_forever()
                    except KeyboardInterrupt:
                        click.echo("\n  Stopping server...", err=True)
                        httpd.shutdown()
        else:
            # JSON (and other formats): Single unified report file
            indent = 2 if pretty else None
            rendered = json.dumps(report, indent=indent, ensure_ascii=False)
            file_tmpl = output_template or f"report.{fmt}"
            _write_report(
                dir_tmpl=output_dir_template or ".",
                file_tmpl=file_tmpl,
                report=report,
                fmt=fmt,
                rendered=rendered,
            )


def _render_mr_templates(
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
                    out_dir = _format_output_path(
                        output_dir_template or ".", report, "json"
                    )
                    out_dir.mkdir(parents=True, exist_ok=True)

                    kwargs = {
                        "no_input": True,
                        "extra_context": {"regis": _escape_jinja(report)},
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


@main.command()
@click.argument("url")
@click.option(
    "-a",
    "--analyzer",
    "analyzer_names",
    multiple=True,
    help="Run only the specified analyzer(s). Can be repeated. Default: all.",
)
@click.option(
    "-p",
    "--playbook",
    "playbook_paths",
    multiple=True,
    help="Path or URL to custom playbook YAML/JSON file(s). Can be repeated. Default: built-in playbook.",
)
@click.option(
    "-o",
    "--output",
    "output_template",
    help="Output filename template (e.g. 'report.{format}'). If not provided and one format requested, outputs to stdout.",
)
@click.option(
    "-D",
    "--output-dir",
    "output_dir_template",
    help="Base directory template for output files (e.g. 'reports/{repository}').",
    default="reports/{registry}/{repository}/{digest}",
)
@click.option(
    "--pretty/--no-pretty",
    default=True,
    help="Pretty-print the JSON output (default: on).",
)
@click.option(
    "-m",
    "--meta",
    "meta",
    multiple=True,
    help="Arbitrary metadata in key=value format. Can be repeated. Supports dot notation (e.g. ci.job_id=123).",
)
@click.option(
    "-s",
    "--site",
    is_flag=True,
    default=False,
    help="Generate HTML report site.",
)
@click.option(
    "--theme",
    default="default",
    type=click.Choice(["default"], case_sensitive=False),
    help="Theme to use for HTML report (default: default).",
)
@click.option(
    "--auth",
    "auth",
    multiple=True,
    help="Credentials in registry.domain=user:pass format. Can be repeated.",
)
@click.option(
    "--platform",
    help="Target platform for multi-arch images (e.g. linux/amd64).",
)
@click.option(
    "--cache",
    is_flag=True,
    help="Use existing report.json as cache if available.",
)
@click.option(
    "--evaluate",
    is_flag=True,
    default=False,
    help="Run rules evaluation after analysis and add results to report.",
)
@click.option(
    "--fail",
    is_flag=True,
    default=False,
    help="Fail command execution if any rule is breached.",
)
@click.option(
    "--fail-level",
    default="critical",
    type=click.Choice(["info", "warning", "critical"], case_sensitive=False),
    help="Minimum rule level that triggers a command failure (default: critical).",
)
@click.option(
    "--base-url",
    default="/",
    help="Base URL for the HTML report site (useful for GitHub/GitLab Pages or artifacts).",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    default=False,
    help="Open the HTML report in the default browser.",
)
def analyze(
    url: str,
    analyzer_names: tuple[str, ...],
    playbook_paths: tuple[str, ...],
    output_template: str | None,
    output_dir_template: str | None,
    pretty: bool,
    site: bool,
    theme: str,
    meta: tuple[str, ...],
    auth: tuple[str, ...],
    cache: bool,
    platform: str | None = None,
    evaluate: bool = False,
    fail: bool = False,
    fail_level: str = "critical",
    base_url: str = "/",
    open_browser: bool = False,
) -> None:
    """Analyze a Docker image and evaluate playbooks.

    URL can be a Docker Hub URL (e.g. https://hub.docker.com/r/library/nginx),
    a bare image reference (nginx:latest), or a private registry URL.

    Runs analyzers and evaluates one or more playbooks against the results.
    """
    # Parse the image URL.
    try:
        ref = parse_image_url(url)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        f"Analyzing {ref.repository}:{ref.tag} on {ref.registry}",
        err=True,
    )

    from regis_cli.registry.auth import resolve_credentials

    # Create the registry client early to fetch the digest.
    username, password = resolve_credentials(ref.registry, list(auth) if auth else None)
    client = RegistryClient(
        registry=ref.registry,
        repository=ref.repository,
        username=username,
        password=password,
    )

    try:
        raw_digest = client.get_digest(ref.tag)
        # Sanitize the digest for filesystem safety
        digest = raw_digest.replace(":", "-") if raw_digest else ref.tag
    except Exception as exc:
        logger.debug("Failed to fetch digest: %s", exc)
        digest = ref.tag

    # Select output formats.
    # JSON is always generated. HTML if --site is active.
    formats = ["json"]
    if site:
        formats.append("html")

    dir_tmpl = output_dir_template or "reports/{registry}/{repository}/{digest}"
    file_tmpl = output_template or "report.{format}"

    # 1. Check for cache if requested.
    final_report = None
    if cache:
        # Construct the expected path for a JSON report to see if it exists.
        # We use a dummy report to get the path.
        dummy_report = {
            "request": {
                "registry": ref.registry,
                "repository": ref.repository,
                "tag": ref.tag,
                "digest": digest,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        try:
            cache_dir = _format_output_path(dir_tmpl, dummy_report, "json")
            cache_file = _format_output_path(file_tmpl, dummy_report, "json")
            cache_path = cache_dir / cache_file

            if cache_path.exists():
                click.echo(f"  Using cached report from {cache_path}", err=True)
                final_report = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.debug("Cache lookup failed: %s", exc)

    analysis_report = final_report

    if not analysis_report:
        # Discover analyzers.
        all_analyzers = _discover_analyzers()
        if not all_analyzers:
            raise click.ClickException(
                "No analyzers found. Is regis-cli installed correctly?"
            )

        # Select which analyzers to run.
        if analyzer_names:
            selected: dict[str, type[BaseAnalyzer]] = {}
            for name in analyzer_names:
                if name not in all_analyzers:
                    available = ", ".join(sorted(all_analyzers))
                    raise click.ClickException(
                        f"Unknown analyzer '{name}'. Available: {available}"
                    )
                selected[name] = all_analyzers[name]
        else:
            selected = all_analyzers

        # Run each analyzer.
        reports: dict[str, Any] = {}
        for name, analyzer_cls in sorted(selected.items()):
            click.echo(f"  Running analyzer: {name}...", err=True)
            analyzer = analyzer_cls()
            try:
                report = analyzer.analyze(
                    client, ref.repository, ref.tag, platform=platform
                )
                analyzer.validate(report)
                reports[name] = report
            except RegistryError as exc:
                click.echo(f"  ✗ {name}: registry error — {exc}", err=True)
                reports[name] = {
                    "analyzer": name,
                    "error": {"type": "registry", "message": str(exc)},
                }
            except AnalyzerError as exc:
                click.echo(f"  ✗ {name}: validation error — {exc}", err=True)
                reports[name] = {
                    "analyzer": name,
                    "error": {"type": "validation", "message": str(exc)},
                }
            except Exception as exc:
                click.echo(f"  ✗ {name}: unexpected error — {exc}", err=True)
                reports[name] = {
                    "analyzer": name,
                    "error": {"type": "unexpected", "message": str(exc)},
                }

        if not reports:
            raise click.ClickException("All analyzers failed.")

        # Build the analysis report.
        metadata_dict: dict[str, Any] = {}
        for item in meta:
            if "=" in item:
                k, v = item.split("=", 1)
                _set_nested_value(metadata_dict, k, v)
            else:
                _set_nested_value(metadata_dict, item, "true")

        analysis_report = {
            "version": version("regis-cli"),
            "request": {
                "url": url,
                "registry": ref.registry,
                "repository": ref.repository,
                "tag": ref.tag,
                "digest": digest,
                "analyzers": sorted(reports.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "results": reports,
        }
        if metadata_dict:
            analysis_report["metadata"] = metadata_dict
            analysis_report["request"]["metadata"] = metadata_dict

    # 2. Run playbooks (always re-run if --evaluate or custom playbooks requested, or if not yet run)
    if not final_report or evaluate or playbook_paths:
        final_report = _run_playbooks(
            playbook_paths, analysis_report, formats, show_rules=evaluate
        )

    if evaluate and "playbooks" in final_report and final_report["playbooks"]:
        # Promote rules from the first playbook to the top level for visibility
        pb0 = final_report["playbooks"][0]
        final_report["rules"] = pb0.get("rules", [])
        final_report["rules_summary"] = pb0.get("rules_summary", {})
        final_report["tier"] = pb0.get("tier")
        final_report["badges"] = pb0.get("badges", [])

    # 3. Validate final report
    _validate_report(final_report)

    # 4. Format and write outputs
    _render_and_save_reports(
        final_report,
        formats,
        output_template,
        output_dir_template,
        theme,
        pretty,
        base_url=base_url,
        open_browser=open_browser,
    )

    # 5. Execute MR templates
    _render_mr_templates(final_report, output_dir_template)

    # 6. Check for failures if requested
    if evaluate and fail:
        level_order = {"critical": 1, "warning": 2, "info": 3, "none": 4}
        threshold = level_order.get(fail_level.lower(), 1)
        breached_rules = []
        # Rules from the final_report (either promoted or from previous analysis)
        rules = final_report.get("rules", [])
        for r in rules:
            if not r.get("passed", False):
                lvl = r.get("level", "info").lower()
                if level_order.get(lvl, 3) <= threshold:
                    breached_rules.append(r.get("slug", "unknown"))

        if breached_rules:
            click.echo(
                f"\nError: Analysis failed due to {len(breached_rules)} rule breaches at level '{fail_level}' or above.",
                err=True,
            )
            import sys

            sys.exit(1)


@main.command(name="evaluate")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-p",
    "--playbook",
    "playbook_paths",
    multiple=True,
    help="Path or URL to custom playbook YAML/JSON file(s).",
)
@click.option(
    "-o",
    "--output",
    "output_template",
    help="Output filename template (e.g. 'report.{format}').",
)
@click.option(
    "-D",
    "--output-dir",
    "output_dir_template",
    help="Base directory template for output files.",
    default="reports/dry-run/{timestamp}",
)
@click.option(
    "--pretty/--no-pretty",
    default=True,
    help="Pretty-print the JSON output (default: on).",
)
@click.option(
    "-s",
    "--site",
    is_flag=True,
    default=False,
    help="Generate HTML report site.",
)
@click.option(
    "--theme",
    default="default",
    type=click.Choice(["default"], case_sensitive=False),
    help="Theme to use for HTML report (default: default).",
)
@click.option(
    "--base-url",
    default="/",
    help="Base URL for the HTML report site.",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    default=False,
    help="Open the HTML report in the default browser.",
)
def evaluate(
    input_path: str,
    playbook_paths: tuple[str, ...],
    output_template: str | None,
    output_dir_template: str | None,
    pretty: bool,
    site: bool,
    theme: str,
    base_url: str = "/",
    open_browser: bool = False,
) -> None:
    """Evaluate playbooks against an existing analysis report (dry-run).

    This command loads an existing JSON report produced by 'analyze' and
    re-runs the playbook evaluation engine against it.
    """
    try:
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(f"Failed to load input file: {exc}") from exc

    # Reconstruct analysis report if it was a final report (contains results)
    # or just use it if it's already an analysis report.
    if "results" in data:
        analysis_report = data
    else:
        raise click.ClickException(
            "Input file does not appear to be a regis-cli report (missing 'results' key)."
        )

    # Select output formats.
    formats = ["json"]
    if site:
        formats.append("html")

    # Run playbooks
    final_report = _run_playbooks(playbook_paths, analysis_report, formats)

    # Validate final report
    _validate_report(final_report)

    # Format and write outputs
    _render_and_save_reports(
        final_report,
        formats,
        output_template,
        output_dir_template,
        theme,
        pretty,
        base_url=base_url,
        open_browser=open_browser,
    )

    # Execute MR templates
    _render_mr_templates(final_report, output_dir_template)


@main.command(name="list")
def list_analyzers() -> None:
    """List all available analyzers."""
    all_analyzers = _discover_analyzers()
    if not all_analyzers:
        click.echo("No analyzers found.")
        return

    for name, cls in sorted(all_analyzers.items()):
        analyzer = cls()
        click.echo(f"  {name:12s}  {analyzer.__class__.__doc__ or ''}")


@main.group(name="bootstrap")
def bootstrap():
    """Bootstrap a new project or playbook."""
    pass


@bootstrap.command(name="repository")
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json defaults.",
)
def bootstrap_repository(output_dir: str, no_input: bool) -> None:
    """Bootstrap a new RegiS analysis repository."""
    try:
        from importlib import resources

        from cookiecutter.main import cookiecutter
    except ImportError as exc:
        raise click.ClickException(
            f"cookiecutter not found or failed to import: {exc}. Please install it with 'pip install cookiecutter'."
        ) from None

    template_path = resources.files("regis_cli") / "cookiecutters" / "repository"

    click.echo(f"Bootstrapping repository into {output_dir}...", err=True)
    try:
        project_dir = cookiecutter(
            str(template_path),
            no_input=no_input,
            output_dir=output_dir,
        )
        click.echo("  ✓ Repository bootstrapped successfully.", err=True)

        # Handle post-install notes
        notes_file = Path(project_dir) / ".regis-post-install.md"
        if notes_file.exists():
            click.echo("\n" + "=" * 40, err=True)
            click.echo("POST-INSTALL NOTES:", err=True)
            click.echo("=" * 40, err=True)
            click.echo(notes_file.read_text(encoding="utf-8"), err=True)
            click.echo("=" * 40 + "\n", err=True)
            notes_file.unlink()

    except Exception as exc:
        raise click.ClickException(f"Failed to bootstrap repository: {exc}") from exc


@bootstrap.command(name="playbook")
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json defaults.",
)
def bootstrap_playbook(output_dir: str, no_input: bool) -> None:
    """Bootstrap a new RegiS playbook."""
    try:
        from importlib import resources

        from cookiecutter.main import cookiecutter
    except ImportError as exc:
        raise click.ClickException(
            f"cookiecutter not found or failed to import: {exc}. Please install it with 'pip install cookiecutter'."
        ) from None

    template_path = resources.files("regis_cli") / "cookiecutters" / "playbook"

    click.echo(f"Bootstrapping playbook into {output_dir}...", err=True)
    try:
        project_dir = cookiecutter(
            str(template_path),
            no_input=no_input,
            output_dir=output_dir,
        )
        click.echo("  ✓ Playbook bootstrapped successfully.", err=True)

        # Handle post-install notes
        notes_file = Path(project_dir) / ".regis-post-install.md"
        if notes_file.exists():
            click.echo("\n" + "=" * 40, err=True)
            click.echo("POST-INSTALL NOTES:", err=True)
            click.echo("=" * 40, err=True)
            click.echo(notes_file.read_text(encoding="utf-8"), err=True)
            click.echo("=" * 40 + "\n", err=True)
            notes_file.unlink()

    except Exception as exc:
        raise click.ClickException(f"Failed to bootstrap playbook: {exc}") from exc


@main.command(name="check")
@click.argument("url")
@click.option(
    "--auth",
    "auth",
    multiple=True,
    help="Credentials in registry.domain=user:pass format. Can be repeated.",
)
def check(url: str, auth: tuple[str, ...]) -> None:
    """Check if an image manifest is accessible.

    URL can be a Docker Hub URL, a bare image reference, or a private registry URL.
    Exits with 0 if the manifest can be fetched. Otherwise, exits with a non-zero code.
    """
    try:
        ref = parse_image_url(url)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    from regis_cli.registry.auth import resolve_credentials

    username, password = resolve_credentials(ref.registry, list(auth) if auth else None)
    client = RegistryClient(
        registry=ref.registry,
        repository=ref.repository,
        username=username,
        password=password,
    )

    click.echo(
        f"Checking manifest availability for {ref.repository}:{ref.tag} on {ref.registry}...",
        err=True,
    )
    try:
        manifest = client.get_manifest(ref.tag)
        if not manifest:
            raise click.ClickException("Received empty manifest.")
        click.echo("Success! Manifest is accessible.", err=True)
    except RegistryError as exc:
        raise click.ClickException(f"Registry error: {exc}") from exc
    except Exception as exc:
        raise click.ClickException(f"Unexpected error: {exc}") from exc


@main.command(name="version")
def version_cmd() -> None:
    """Show regis-cli version and exit."""
    click.echo(f"regis-cli version {version('regis-cli')}")


@main.group(name="rules")
def rules_group():
    """Manage and evaluate rules."""
    pass


def _render_rule_markdown(rule: dict[str, Any]) -> str:
    """Render a single rule as a detailed Markdown document matching the documentation template."""
    slug = rule.get("slug", "unknown")
    description = rule.get("description", "n/a")
    provider = rule.get("provider", "custom")
    level = rule.get("level", "info")
    tags = rule.get("tags", [])
    params = rule.get("params", {})
    condition = rule.get("condition", {})
    messages = rule.get("messages", {})

    # 1. YAML Frontmatter
    frontmatter = ["---"]
    if tags:
        frontmatter.append("tags:")
        for tag in tags:
            frontmatter.append(f"  - {tag}")
    frontmatter.append("  - rules")
    frontmatter.append("---\n")

    # 2. Header and Description
    lines = [
        f"# {slug}",
        "",
        description,
        "",
        # 3. Metadata Table
        "| Provider | Level | Tags |",
        "| :--- | :--- | :--- |",
        f"| {provider} | {level.capitalize()} | {', '.join(tags)} |",
        "",
    ]

    # 4. Parameters Table
    if params:
        lines.append("## Parameters")
        lines.append("")
        lines.append("| Name | Default Value | Description |")
        lines.append("| :--- | :--- | :--- |")
        for k, v in params.items():
            # For dynamic templates, we use a simple representation
            lines.append(f"| `{k}` | `{v}` | n/a |")
        lines.append("")

    # 5. Messages Table
    if messages:
        lines.append("## Messages")
        lines.append("")
        lines.append("| Type | Message |")
        lines.append("| :--- | :--- |")
        if "pass" in messages:
            lines.append(f"| **Pass** | {messages['pass']} |")
        if "fail" in messages:
            lines.append(f"| **Fail** | {messages['fail']} |")
        lines.append("")

    # 6. Playbook Example
    lines.append("## Playbook Example")
    lines.append("")
    lines.append("```yaml")
    lines.append("rules:")
    lines.append(f"  - provider: {provider}")

    # Extract rule name from slug if it contains the provider
    rule_name = slug
    if "." in slug:
        rule_name = slug.split(".", 1)[1]

    lines.append(f"    rule: {rule_name}")

    if params:
        lines.append("    options:")
        import yaml

        # Render params as YAML indented
        params_yaml = yaml.dump(params, default_flow_style=False).strip()
        for p_line in params_yaml.splitlines():
            lines.append(f"      {p_line}")

    lines.append("```")
    lines.append("")

    # 7. Condition
    if condition:
        lines.append("## Condition")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(condition, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(frontmatter + lines)


@rules_group.command(name="list")
@click.option(
    "-r",
    "--rules",
    "rules_path",
    help="Path to an optional rules.yaml file to merge overrides.",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["text", "markdown"], case_sensitive=False),
    default="text",
    help="Output format (default: text).",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    help="Output filename for the rules list.",
)
@click.option(
    "-D",
    "--output-dir",
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="Directory to write individual rule markdown files (markdown format only).",
)
@click.option(
    "--index/--no-index",
    "generate_index",
    default=False,
    help="Generate an index.md file in the output directory (default: off).",
)
def list_rules(
    rules_path: str | None,
    output_format: str,
    output_file: str | None,
    output_dir: str | None = None,
    generate_index: bool = False,
) -> None:
    """List all available default rules and any overrides."""
    import yaml

    from regis_cli.cli import _discover_analyzers
    from regis_cli.rules.evaluator import get_default_rules, merge_rules

    analyzers = _discover_analyzers()
    defaults = get_default_rules(list(analyzers.keys()))

    custom = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("rules", [])

    final_rules = merge_rules(defaults, custom)
    final_rules.sort(key=lambda r: r.get("slug", ""))

    if not final_rules:
        click.echo("No rules found.")
        return

    if output_format.lower() == "markdown":
        if output_dir:
            out_root = Path(output_dir)
            out_root.mkdir(parents=True, exist_ok=True)

            for rule in final_rules:
                provider = rule.get("provider", "custom")
                slug = rule.get("slug", "unknown")

                rule_dir = out_root / provider
                rule_dir.mkdir(parents=True, exist_ok=True)

                rule_content = _render_rule_markdown(rule)
                (rule_dir / f"{slug}.md").write_text(rule_content, encoding="utf-8")

            click.echo(
                f"  ✓ {len(final_rules)} rule files written to {output_dir}", err=True
            )

            if generate_index:
                index_lines = []
                index_lines.append(
                    "| Provider | Slug | Description | Level | Tags | Parameters |"
                )
                index_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
                for rule in final_rules:
                    provider = rule.get("provider", "custom")
                    slug = rule.get("slug", "n/a")
                    description = rule.get("description", "n/a")
                    level = rule.get("level", "info")
                    tags = ", ".join(rule.get("tags", []))
                    params = rule.get("params", {})
                    params_str = ", ".join(f"`{k}={v}`" for k, v in params.items())

                    # Relative link to the rule file: ./provider/slug.md
                    link = f"./{provider}/{slug}.md"
                    index_lines.append(
                        f"| {provider} | [`{slug}`]({link}) | {description} | {level} | {tags} | {params_str} |"
                    )
                index_content = "\n".join(index_lines) + "\n"
                (out_root / "index.md").write_text(index_content, encoding="utf-8")
                click.echo(f"  ✓ Index file written to {output_dir}/index.md", err=True)
            return

        lines = []
        lines.append("| Provider | Slug | Description | Level | Tags | Parameters |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

        for rule in final_rules:
            provider = rule.get("provider", "custom")
            slug = rule.get("slug", "n/a")
            description = rule.get("description", "n/a")
            level = rule.get("level", "info")
            tags = ", ".join(rule.get("tags", []))
            params = rule.get("params", {})
            params_str = ""
            if params:
                params_str = ", ".join(f"`{k}={v}`" for k, v in params.items())
            lines.append(
                f"| {provider} | `{slug}` | {description} | {level} | {tags} | {params_str} |"
            )
        content = "\n".join(lines) + "\n"
    else:
        # Default text format
        lines = []
        for rule in final_rules:
            enabled = rule.get("enable", True)
            enabled_mark = "[x]" if enabled else "[ ]"
            params = rule.get("params", {})
            params_str = ""
            if params:
                params_str = f" ({', '.join(f'{k}={v}' for k, v in params.items())})"
            lines.append(
                f"  {enabled_mark} {rule.get('slug', 'unnamed'):25s} {rule.get('level', 'info'):8s} {rule.get('description', '')}{params_str}"
            )
        content = "\n".join(lines) + "\n"

    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        click.echo(f"  Rules list written to {output_file}", err=True)
    else:
        click.echo(content)


@rules_group.command(name="show")
@click.argument("slug")
@click.option(
    "-r",
    "--rules",
    "rules_path",
    help="Path to an optional rules.yaml file to merge overrides.",
)
def show_rule(slug: str, rules_path: str | None) -> None:
    """Display the full definition of a specific rule."""
    import json

    import yaml

    from regis_cli.cli import _discover_analyzers
    from regis_cli.rules.evaluator import get_default_rules, merge_rules

    analyzers = _discover_analyzers()
    defaults = get_default_rules(list(analyzers.keys()))

    custom = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("rules", [])

    final_rules = merge_rules(defaults, custom)
    matching_rule = next((r for r in final_rules if r.get("slug") == slug), None)

    if not matching_rule:
        raise click.ClickException(f"Rule '{slug}' not found.")

    click.echo(json.dumps(matching_rule, indent=2))


@rules_group.command(name="evaluate")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-r",
    "--rules",
    "rules_path",
    help="Path to custom rules.yaml file.",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    help="Output filename for the evaluation result (JSON format).",
)
@click.option(
    "--fail",
    is_flag=True,
    default=False,
    help="Fail command execution if any rule is breached.",
)
@click.option(
    "--fail-level",
    default="critical",
    type=click.Choice(["info", "warning", "critical"], case_sensitive=False),
    help="Minimum rule level that triggers a command failure (default: critical).",
)
def eval_rules(
    input_path: str,
    rules_path: str | None,
    output_file: str | None,
    fail: bool,
    fail_level: str,
) -> None:
    """Evaluate a regis-cli JSON report against rules."""
    import json

    import yaml

    from regis_cli.rules.evaluator import evaluate_rules

    try:
        report_data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(f"Failed to load report file: {exc}") from exc

    rules_def = None
    if rules_path:
        try:
            rules_def = yaml.safe_load(Path(rules_path).read_text(encoding="utf-8"))
        except Exception as exc:
            raise click.ClickException(f"Failed to load rules file: {exc}") from exc

    result = evaluate_rules(report_data, rules_def)

    if output_file:
        Path(output_file).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        click.echo(f"Evaluation report written to {output_file}", err=True)
    else:
        # Default text output if no JSON output is requested
        score = result["score"]
        click.echo(
            f"\nRules Evaluation Score: {score}% ({result['passed_rules']}/{result['total_rules']})"
        )
        click.echo("-" * 40)
        for r in result["rules"]:
            icon = "✅" if r["passed"] else "❌"
            if r["status"] == "incomplete":
                icon = "⚠️"
            click.echo(f"{icon} [{r['slug']}] {r['message']}")

    if fail:
        # Same level order as in evaluator.py
        level_order = {"critical": 1, "warning": 2, "info": 3, "none": 4}
        threshold = level_order.get(fail_level.lower(), 1)

        breaches = []
        for r in result["rules"]:
            if not r["passed"]:
                rule_level = r.get("level", "info").lower()
                if level_order.get(rule_level, 3) <= threshold:
                    breaches.append(r["slug"])

        if breaches:
            click.echo(
                f"\nError: Evaluation failed due to {len(breaches)} rule breaches at level '{fail_level}' or above.",
                err=True,
            )
            # Use sys.exit(1) for shell scripts/CI
            sys.exit(1)


if __name__ == "__main__":
    main()
