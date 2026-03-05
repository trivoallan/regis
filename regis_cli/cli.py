"""CLI entry point for regis-cli."""

from __future__ import annotations

import json
import logging
import sys
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
    "--cache",
    is_flag=True,
    help="Use existing report.json as cache if available.",
)
@click.option(
    "--platform",
    help="Target platform for multi-arch images (e.g. linux/amd64).",
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

    if final_report:
        # If we have a cached report, we skip analysis and playbook evaluation.
        # We might want to re-run playbooks eventually, but for now we follow the "cache report" intent.
        pass
    else:
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

        analysis_report: dict[str, Any] = {
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

        # Load and evaluate playbooks.
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
                        f"    {summary_str}  "
                        f"({pb_result['passed_scorecards']}/{pb_result['total_scorecards']} scorecards passed, "
                        f"{pb_result['score']}%)\n",
                        err=True,
                    )

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

    # Validate final report against its schema.
    from jsonschema.validators import validator_for
    from referencing import Registry, Resource

    schemas_dir = resources.files("regis_cli.schemas")
    registry = Registry()
    report_schema = None
    base_uri = "https://regis-cli/schemas/"

    for schema_file in schemas_dir.iterdir():
        if not schema_file.name.endswith(".json"):
            continue
        schema_data = json.loads(schema_file.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema_data)

        # Register both by filename (relative) and by $id if available.
        registry = registry.with_resource(uri=schema_file.name, resource=resource)
        registry = registry.with_resource(
            uri=base_uri + schema_file.name, resource=resource
        )
        if "$id" in schema_data:
            registry = registry.with_resource(uri=schema_data["$id"], resource=resource)

        if schema_file.name == "report.schema.json":
            report_schema = schema_data

    if report_schema:
        try:
            validator_cls = validator_for(report_schema)
            validator = validator_cls(report_schema, registry=registry)
            validator.validate(instance=final_report)
        except jsonschema.ValidationError as exc:
            raise click.ClickException(
                f"Report schema validation failed: {exc.message}"
            ) from exc

    # Format and write outputs.
    from regis_cli.report.html import render_html

    for fmt in formats:
        if fmt == "html":
            # For HTML, generate one file per playbook if playbooks exist.
            # If no playbooks, generate a single report using fallback logic.
            playbook_results = final_report.get("playbooks", [])
            if playbook_results:
                for pb in playbook_results:
                    # Pre-calculate filenames for all pages in this playbook to build navigation
                    page_navigation = []
                    for page in pb.get("pages", []):
                        pb_slug = pb.get("slug")
                        pg_slug = page.get("slug")
                        source_name = pb.get("_meta", {}).get("source_name")

                        if output_template:
                            # If a template is provided, we can't easily pre-calculate
                            # unique filenames for multiple pages unless the template
                            # includes page-specific vars. For now, assume default logic
                            # if multiple pages exist.
                            filename = output_template
                        elif pg_slug:
                            filename = f"{pg_slug}.{fmt}"
                        elif pb_slug:
                            filename = (
                                f"{pb_slug}-{page.get('title', 'page').lower()}.{fmt}"
                            )
                        elif source_name:
                            filename = f"{source_name}-{page.get('title', 'page').lower()}.{fmt}"
                        else:
                            filename = f"report_{pb.get('playbook_name', 'unnamed')}_{page.get('title', 'page').lower()}.{fmt}"

                        page_navigation.append(
                            {
                                "title": page.get("title"),
                                "url": filename,
                                "active": False,
                            }
                        )

                    for i, page in enumerate(pb.get("pages", [])):
                        # Mark current page as active in navigation
                        current_nav = [dict(n) for n in page_navigation]
                        current_nav[i]["active"] = True

                        # Render HTML focusing on this single page of the playbook.
                        single_page_report = {
                            **final_report,
                            "playbooks": [
                                {
                                    **pb,
                                    "pages": [page],
                                }
                            ],
                            "playbook": pb,
                            "page": page,
                            "navigation": current_nav,
                        }
                        rendered = render_html(single_page_report, theme=theme)

                        _write_report(
                            dir_tmpl=output_dir_template or ".",
                            file_tmpl=page_navigation[i]["url"],
                            report=single_page_report,
                            fmt=fmt,
                            rendered=rendered,
                        )
            else:
                # No playbooks, just render the base report
                rendered = render_html(final_report, theme=theme)
                file_tmpl = output_template or f"report.{fmt}"
                _write_report(
                    dir_tmpl=output_dir_template or ".",
                    file_tmpl=file_tmpl,
                    report=final_report,
                    fmt=fmt,
                    rendered=rendered,
                )
        else:
            # JSON (and other formats): Single unified report file
            indent = 2 if pretty else None
            rendered = json.dumps(final_report, indent=indent, ensure_ascii=False)
            file_tmpl = output_template or f"report.{fmt}"
            _write_report(
                dir_tmpl=output_dir_template or ".",
                file_tmpl=file_tmpl,
                report=final_report,
                fmt=fmt,
                rendered=rendered,
            )

    # Execute Cookiecutter templates for Merge Requests
    playbooks = final_report.get("playbooks", [])
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
                    out_dir = _format_output_path(dir_tmpl, final_report, "json")
                    out_dir.mkdir(parents=True, exist_ok=True)

                    kwargs = {
                        "no_input": True,
                        "extra_context": {"regis": _escape_jinja(final_report)},
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


@main.command(name="generate")
@click.argument(
    "template_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json defaults.",
)
def generate(template_path: str, output_dir: str, no_input: bool) -> None:
    """Generate a new project from a Cookiecutter template."""
    try:
        from cookiecutter.main import cookiecutter
    except ImportError:
        raise click.ClickException(
            "cookiecutter not found. Please install it with 'pip install cookiecutter'."
        ) from None

    click.echo(
        f"Generating project from {template_path} into {output_dir}...", err=True
    )
    try:
        cookiecutter(
            template_path,
            no_input=no_input,
            output_dir=output_dir,
            overwrite_if_exists=True,
        )
        click.echo("Success!", err=True)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


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
    """Display regis-cli version."""
    click.echo(f"regis-cli version {version('regis-cli')}")


if __name__ == "__main__":
    main()
