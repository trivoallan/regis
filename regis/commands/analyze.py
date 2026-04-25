"""analyze, evaluate, and list commands."""

from __future__ import annotations

import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from regis.analyzers.base import AnalyzerError, BaseAnalyzer
from regis.analyzers.discovery import discover_analyzers
from regis.registry.client import RegistryClient, RegistryError
from regis.registry.parser import parse_image_url
from regis.utils.report import (
    format_output_path,
    render_and_save_reports,
    render_mr_templates,
    run_playbooks,
    set_nested_value,
    validate_report,
)

logger = logging.getLogger(__name__)

# Alias kept for patch compatibility in tests
_discover_analyzers = discover_analyzers


def _run_analyzer(
    analyzer_cls: type[BaseAnalyzer],
    registry: str,
    repository: str,
    tag: str,
    username: str | None,
    password: str | None,
    platform: str | None,
) -> tuple[str, dict[str, Any]]:
    """Run a single analyzer with its own registry client."""
    client = RegistryClient(
        registry=registry,
        repository=repository,
        username=username,
        password=password,
    )
    analyzer = analyzer_cls()
    report = analyzer.analyze(client, repository, tag, platform=platform)
    analyzer.validate(report)
    return analyzer.name, report


def _parse_meta(meta: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in meta:
        if "=" in item:
            k, v = item.split("=", 1)
            set_nested_value(result, k, v)
        else:
            set_nested_value(result, item, "true")
    return result


@click.command()
@click.argument("url", required=False, default="")
@click.option(
    "--rerun",
    "rerun",
    default=None,
    help="Re-run a single analyzer against an existing report (requires --report).",
)
@click.option(
    "--report",
    "report_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Existing report directory to update (requires --rerun).",
)
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
    "--html",
    "html_single",
    is_flag=True,
    default=False,
    help="Generate a self-contained single-file HTML report (report.html).",
)
@click.option(
    "--sections",
    "sections",
    default="all",
    help=(
        "Sections to include in the HTML report: 'all' (default), 'summary', "
        "or comma-separated analyzer slugs (e.g. 'trivy,hadolint'). "
        "Only applies to --html."
    ),
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
@click.option(
    "--archive",
    "-A",
    "archive_dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    help="Archive directory: persist the report and update manifest.json / data.json.",
)
@click.option(
    "--max-workers",
    default=4,
    show_default=True,
    type=click.IntRange(1, 20),
    help="Maximum number of analyzers to run in parallel. Use 1 for serial execution.",
)
@click.option(
    "--markdown",
    "markdown",
    is_flag=True,
    default=False,
    help="Also emit a Markdown summary report (report.md).",
)
@click.option(
    "--merge-meta",
    "merge_meta",
    is_flag=True,
    default=False,
    help="Merge --meta values into existing metadata instead of replacing (only with --rerun).",
)
def analyze(
    url: str,
    analyzer_names: tuple[str, ...],
    playbook_paths: tuple[str, ...],
    output_template: str | None,
    output_dir_template: str | None,
    pretty: bool,
    site: bool,
    html_single: bool,
    sections: str,
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
    archive_dir: Path | None = None,
    max_workers: int = 4,
    rerun: str | None = None,
    report_dir: Path | None = None,
    markdown: bool = False,
    merge_meta: bool = False,
) -> None:
    """Analyze a Docker image and evaluate playbooks.

    URL can be a Docker Hub URL (e.g. https://hub.docker.com/r/library/nginx),
    a bare image reference (nginx:latest), or a private registry URL.

    Runs analyzers and evaluates one or more playbooks against the results.
    """
    # --rerun / --report mutual dependency validation
    if rerun and not report_dir:
        raise click.UsageError("--rerun requires --report")
    if report_dir and not rerun:
        raise click.UsageError("--report requires --rerun")

    # --rerun: patch an existing report and replay playbook evaluation
    if rerun and report_dir:
        from regis.analyzers.metadata import MetadataAnalyzer

        if rerun != MetadataAnalyzer.name:
            all_analyzers = _discover_analyzers()
            if rerun not in all_analyzers:
                available = ", ".join(sorted(all_analyzers))
                raise click.ClickException(
                    f"Unknown analyzer '{rerun}'. Available: {available}"
                )

        report_path = (report_dir / "report.json").resolve()
        if not report_path.exists():
            raise click.ClickException(f"Report not found: {report_path}")

        existing_report = json.loads(report_path.read_text(encoding="utf-8"))

        metadata_dict = _parse_meta(meta)

        if rerun == MetadataAnalyzer.name:
            meta_analyzer = MetadataAnalyzer(metadata=metadata_dict)
            result = meta_analyzer.analyze()
        else:
            from regis.registry.auth import resolve_credentials

            ref = parse_image_url(url) if url else None
            if ref is None:
                raise click.UsageError(
                    "--rerun for non-metadata analyzers requires a URL argument"
                )
            username, password = resolve_credentials(
                ref.registry, list(auth) if auth else None
            )
            _, result = _run_analyzer(
                all_analyzers[rerun],
                ref.registry,
                ref.repository,
                ref.tag,
                username,
                password,
                platform,
            )

        existing_report.setdefault("results", {})[rerun] = result
        if metadata_dict:
            if merge_meta and existing_report.get("metadata"):
                metadata_dict = {**existing_report["metadata"], **metadata_dict}
            existing_report["metadata"] = metadata_dict
            existing_report.setdefault("request", {})["metadata"] = metadata_dict

        formats = ["json"]
        if markdown:
            formats.append("md")
        rerun_report = run_playbooks(
            playbook_paths, existing_report, formats, show_rules=evaluate
        )
        validate_report(rerun_report)

        indent = 2 if pretty else None
        report_path.write_text(
            json.dumps(rerun_report, indent=indent, ensure_ascii=False),
            encoding="utf-8",
        )
        click.echo(f"  Report updated at {report_path}", err=True)
        return

    # Normal analysis flow requires a URL
    if not url:
        raise click.UsageError("URL argument is required")

    try:
        ref = parse_image_url(url)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        f"Analyzing {ref.repository}:{ref.tag} on {ref.registry}",
        err=True,
    )

    from regis.registry.auth import resolve_credentials

    username, password = resolve_credentials(ref.registry, list(auth) if auth else None)
    client = RegistryClient(
        registry=ref.registry,
        repository=ref.repository,
        username=username,
        password=password,
    )

    try:
        raw_digest = client.get_digest(ref.tag)
        digest = raw_digest.replace(":", "-") if raw_digest else ref.tag
    except Exception as exc:
        logger.debug("Failed to fetch digest: %s", exc)
        digest = ref.tag

    if (site or html_single) and archive_dir:
        raise click.UsageError("--site/--html and --archive are mutually exclusive.")

    formats = []
    if not archive_dir:
        formats.append("json")
    if site:
        formats.append("html-site")
    if html_single:
        formats.append("html")
    if markdown:
        formats.append("md")

    if sections != "all" and not html_single:
        click.echo("  Warning: --sections has no effect without --html.", err=True)

    dir_tmpl = output_dir_template or "reports/{registry}/{repository}/{digest}"
    file_tmpl = output_template or "report.{format}"

    final_report = None
    if cache:
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
            cache_dir = format_output_path(dir_tmpl, dummy_report, "json")
            cache_file = format_output_path(file_tmpl, dummy_report, "json")
            cache_path = cache_dir / cache_file

            if cache_path.exists():
                click.echo(f"  Using cached report from {cache_path}", err=True)
                final_report = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.debug("Cache lookup failed: %s", exc)

    analysis_report = final_report

    if not analysis_report:
        all_analyzers = _discover_analyzers()
        if not all_analyzers:
            raise click.ClickException(
                "No analyzers found. Is regis installed correctly?"
            )

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

        effective_workers = min(max_workers, len(selected))
        click.echo(
            f"  Running {len(selected)} analyzer(s) with {effective_workers} worker(s)...",
            err=True,
        )
        reports: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            futures = {
                executor.submit(
                    _run_analyzer,
                    cls,
                    ref.registry,
                    ref.repository,
                    ref.tag,
                    username,
                    password,
                    platform,
                ): name
                for name, cls in selected.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    _, report = future.result()
                    reports[name] = report
                    click.echo(f"  ✓ {name}", err=True)
                except RegistryError as exc:
                    click.echo(f"  ✗ {name}: registry error — {exc}", err=True)
                    reports[name] = {
                        "analyzer": name,
                        "error": {"type": "registry", "message": str(exc)},
                    }
                except AnalyzerError as exc:
                    click.echo(f"  ✗ {name}: analysis error — {exc}", err=True)
                    reports[name] = {
                        "analyzer": name,
                        "error": {"type": "analysis", "message": str(exc)},
                    }
                except Exception as exc:
                    click.echo(f"  ✗ {name}: unexpected error — {exc}", err=True)
                    reports[name] = {
                        "analyzer": name,
                        "error": {"type": "unexpected", "message": str(exc)},
                    }

        if not reports:
            raise click.ClickException("All analyzers failed.")

        from importlib.metadata import version

        metadata_dict = _parse_meta(meta)

        analysis_report = {
            "version": version("regis"),
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

        try:
            from importlib.resources import files as _res_files

            _dates_text = (
                _res_files("regis")
                .joinpath("data/snapshot_dates.json")
                .read_text(encoding="utf-8")
            )
            _dates = json.loads(_dates_text)
            _pkg_version = version("regis")
            _entry = _dates.get(f"v{_pkg_version}") or _dates.get(_pkg_version)
            if _entry and _entry.get("date"):
                analysis_report["snapshot_date"] = _entry["date"]
        except Exception:
            pass

    if not final_report or evaluate or playbook_paths:
        final_report = run_playbooks(
            playbook_paths, analysis_report, formats, show_rules=evaluate
        )

    if evaluate and "playbooks" in final_report and final_report["playbooks"]:
        pb0 = final_report["playbooks"][0]
        final_report["rules"] = pb0.get("rules", [])
        final_report["rules_summary"] = pb0.get("rules_summary", {})
        final_report["tier"] = pb0.get("tier")
        final_report["badges"] = pb0.get("badges", [])

    validate_report(final_report)

    if final_report.get("snapshot_date"):
        click.echo(f"  Snapshot date: {final_report['snapshot_date']}", err=True)

    if archive_dir:
        from regis.archive.store import add_to_archive

        add_to_archive(final_report, archive_dir)
    else:
        render_and_save_reports(
            final_report,
            formats,
            output_template,
            output_dir_template,
            theme,
            pretty,
            base_url=base_url,
            open_browser=open_browser,
            sections=sections,
        )

    if not archive_dir:
        render_mr_templates(final_report, output_dir_template)

    if evaluate and fail:
        level_order = {"critical": 1, "warning": 2, "info": 3, "none": 4}
        threshold = level_order.get(fail_level.lower(), 1)
        breached_rules = []
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
            sys.exit(1)


@click.command(name="evaluate")
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
    "--html",
    "html_single",
    is_flag=True,
    default=False,
    help="Generate a self-contained single-file HTML report (report.html).",
)
@click.option(
    "--sections",
    "sections",
    default="all",
    help=(
        "Sections to include in the HTML report: 'all' (default), 'summary', "
        "or comma-separated analyzer slugs (e.g. 'trivy,hadolint'). "
        "Only applies to --html."
    ),
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
def evaluate_cmd(
    input_path: str,
    playbook_paths: tuple[str, ...],
    output_template: str | None,
    output_dir_template: str | None,
    pretty: bool,
    site: bool,
    theme: str,
    base_url: str = "/",
    open_browser: bool = False,
    html_single: bool = False,
    sections: str = "all",
) -> None:
    """Evaluate playbooks against an existing analysis report (dry-run).

    This command loads an existing JSON report produced by 'analyze' and
    re-runs the playbook evaluation engine against it.
    """
    try:
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(f"Failed to load input file: {exc}") from exc

    if "results" in data:
        analysis_report = data
    else:
        raise click.ClickException(
            "Input file does not appear to be a regis report (missing 'results' key)."
        )

    formats = ["json"]
    if site:
        formats.append("html-site")
    if html_single:
        formats.append("html")

    if sections != "all" and not html_single:
        click.echo("  Warning: --sections has no effect without --html.", err=True)

    final_report = run_playbooks(playbook_paths, analysis_report, formats)
    validate_report(final_report)

    render_and_save_reports(
        final_report,
        formats,
        output_template,
        output_dir_template,
        theme,
        pretty,
        base_url=base_url,
        open_browser=open_browser,
        sections=sections,
    )

    render_mr_templates(final_report, output_dir_template)


@click.command(name="list")
def list_analyzers() -> None:
    """List all available analyzers."""
    all_analyzers = _discover_analyzers()
    if not all_analyzers:
        click.echo("No analyzers found.")
        return

    for name, cls in sorted(all_analyzers.items()):
        analyzer = cls()
        click.echo(f"  {name:12s}  {analyzer.__class__.__doc__ or ''}")
