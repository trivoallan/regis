"""analyze, evaluate, and list commands."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import click

from regis.adapters.driven.analyzers.entry_point_provider import (
    EntryPointAnalyzerProvider,
)
from regis.adapters.driven.registry.client import RegistryClient
from regis.adapters.driven.registry.parser import parse_image_url
from regis.adapters.driven.report.file_report_sink import FileReportSink
from regis.adapters.driven.report.presentation_renderer import (
    CookiecutterPresentationRenderer,
)
from regis.adapters.driving.cli.composition import build_analyze_image, build_evaluate
from regis.analyzers.base import BaseAnalyzer
from regis.core.application.analyze_image import AnalyzerOutcome
from regis.core.model.image_reference import ImageReference
from regis.core.model.report import Report
from regis.utils.report import (
    ensure_schema_version,
    format_output_path,
    run_playbooks,
    set_nested_value,
    validate_report,
)

logger = logging.getLogger(__name__)

# Analyzer discovery goes through the AnalyzerProvider port. The module-level
# instance + the `_discover_analyzers` binding are kept as the test patch seam
# (`regis.commands.analyze._discover_analyzers`).
_analyzer_provider = EntryPointAnalyzerProvider()
_discover_analyzers = _analyzer_provider.available

#: Maps an AnalyzerOutcome.error_type to its human-readable CLI label.
_ERROR_LABEL: dict[str, str] = {
    "registry": "registry error",
    "analysis": "analysis error",
    "tool": "tool error",
    "unexpected": "unexpected error",
}


def _info(msg: str, *, quiet: bool, err: bool = True) -> None:
    """Print informational output to stderr unless quiet mode is active."""
    if not quiet:
        click.echo(msg, err=err)


def _render_verdict_block(final_report: dict[str, Any], *, quiet: bool) -> None:
    """Print the evaluation verdict (tier · score, badges, failed rules) to stderr.

    Multi-line block, click-coloured. Suppressed under --quiet. Prints nothing
    when no playbook was evaluated.
    """
    if quiet:
        return

    from regis.playbook.verdict import (
        LEVEL_STYLE,
        badge_emoji,
        build_verdict,
        format_counts,
        level_emoji,
        tier_label,
    )

    v = build_verdict(final_report)
    if not v.evaluated:
        return

    # Headline: "🥈 Silver · 78/100"
    headline = f"{tier_label(v.tier, v.tier_icon)} · {v.score}/100"
    click.echo(f"  {click.style(headline, bold=True)}", err=True)

    # Counts line (shared across surfaces)
    click.echo(f"  {format_counts(v)}", err=True)

    # Badges line
    if v.badges:
        chips = "   ".join(f"{badge_emoji(b.klass)} {b.label}" for b in v.badges)
        click.echo(f"  {chips}", err=True)

    # Failed and incomplete rules — pad the severity and [slug] columns so the
    # messages all line up. Each line reads: "<glyph> <emoji> <level>  [slug]  <msg>".
    rules = (*v.failures, *v.incompletes)
    tag_width = max((len(r.slug) + 2 for r in rules), default=0)
    level_width = max((len(r.level) for r in rules), default=0)
    for f in v.failures:
        colour = LEVEL_STYLE.get(f.level, None)
        severity = f"{level_emoji(f.level) or '⬜'} {f.level:<{level_width}}"
        line = f"  ✗ {severity}  {f'[{f.slug}]':<{tag_width}}   {f.message}"
        click.echo(click.style(line, fg=colour) if colour else line, err=True)
    for i in v.incompletes:
        severity = f"{level_emoji(i.level) or '⬜'} {i.level:<{level_width}}"
        click.echo(
            f"  ⚠ {severity}  {f'[{i.slug}]':<{tag_width}}   {i.message}", err=True
        )


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
    "--skip",
    "skip_analyzers",
    multiple=True,
    help=(
        "Exclude the specified analyzer(s) from the run. Can be repeated. "
        "Run `regis list` to see available analyzer names."
    ),
)
@click.option(
    "-p",
    "--playbook",
    "playbook_paths",
    multiple=True,
    envvar="REGIS_PLAYBOOK",
    show_envvar=True,
    help="Path or URL to custom playbook YAML/JSON file(s). Can be repeated. Default: built-in playbook.",
)
@click.option(
    "-o",
    "--output",
    "output_template",
    envvar="REGIS_OUTPUT",
    show_envvar=True,
    help="Output filename template (e.g. 'report.{format}'). If not provided and one format requested, outputs to stdout.",
)
@click.option(
    "-D",
    "--output-dir",
    "output_dir_template",
    envvar="REGIS_OUTPUT_DIR",
    show_envvar=True,
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
        "or comma-separated analyzer slugs (e.g. 'cve,hadolint'). "
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
    envvar="REGIS_PLATFORM",
    show_envvar=True,
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
    "--max-workers",
    default=4,
    show_default=True,
    type=click.IntRange(1, 20),
    envvar="REGIS_MAX_WORKERS",
    show_envvar=True,
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
@click.pass_context
def analyze(
    ctx: click.Context,
    url: str,
    analyzer_names: tuple[str, ...],
    skip_analyzers: tuple[str, ...],
    playbook_paths: tuple[str, ...],
    output_template: str | None,
    output_dir_template: str | None,
    pretty: bool,
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
    quiet = bool(ctx.obj and ctx.obj.get("quiet"))
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
            from regis.adapters.driven.registry.auth import resolve_credentials

            ref = parse_image_url(url) if url else None
            if ref is None:
                raise click.UsageError(
                    "--rerun for non-metadata analyzers requires a URL argument"
                )
            username, password = resolve_credentials(
                ref.registry, list(auth) if auth else None
            )
            image = ImageReference(
                registry=ref.registry,
                repository=ref.repository,
                tag=ref.tag,
                platform=platform,
            )
            use_case = build_analyze_image(username, password)
            result = use_case.run_one(image, all_analyzers[rerun])

        existing_report.setdefault("results", {})[rerun] = result
        if metadata_dict:
            if merge_meta and existing_report.get("metadata"):
                metadata_dict = {**existing_report["metadata"], **metadata_dict}
            existing_report["metadata"] = metadata_dict

        formats = ["json"]
        if markdown:
            formats.append("md")
        rerun_report = run_playbooks(
            playbook_paths, existing_report, formats, show_rules=evaluate
        )
        ensure_schema_version(rerun_report)
        validate_report(rerun_report)

        indent = 2 if pretty else None
        report_path.write_text(
            json.dumps(rerun_report, indent=indent, ensure_ascii=False),
            encoding="utf-8",
        )
        _info(f"  Report updated at {report_path}", quiet=quiet)
        return

    # Normal analysis flow requires a URL
    if not url:
        raise click.UsageError("URL argument is required")

    try:
        ref = parse_image_url(url)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    _info(
        f"Analyzing {ref.repository}:{ref.tag} on {ref.registry}",
        quiet=quiet,
    )

    from regis.adapters.driven.registry.auth import resolve_credentials

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

    formats = ["json"]
    if html_single:
        formats.append("html")
    if markdown:
        formats.append("md")

    if sections != "all" and not html_single:
        _info("  Warning: --sections has no effect without --html.", quiet=quiet)

    dir_tmpl = output_dir_template or "reports/{registry}/{repository}/{digest}"
    file_tmpl = output_template or "report.{format}"

    final_report: dict[str, Any] | None = None
    if cache:
        try:
            dummy_report: dict[str, Any] = {
                "request": {
                    "registry": ref.registry,
                    "repository": ref.repository,
                    "tag": ref.tag,
                    "digest": digest,
                }
            }
            cache_dir = format_output_path(dir_tmpl, dummy_report, "json")
            cache_file = format_output_path(file_tmpl, dummy_report, "json")
            cache_path = cache_dir / cache_file

            if cache_path.exists():
                _info(f"  Using cached report from {cache_path}", quiet=quiet)
                final_report = json.loads(cache_path.read_text(encoding="utf-8"))
                ensure_schema_version(final_report)
        except Exception as exc:
            logger.debug("Cache lookup failed: %s", exc)

    if final_report is not None:
        if evaluate or playbook_paths:
            final_report = run_playbooks(
                playbook_paths, final_report, formats, show_rules=evaluate
            )
            if evaluate and final_report.get("playbooks"):
                pb0 = final_report["playbooks"][0]
                final_report["rules"] = pb0.get("rules", [])
                final_report["rules_summary"] = pb0.get("rules_summary", {})
                final_report["tier"] = pb0.get("tier")
                final_report["badges"] = pb0.get("badges", [])
            validate_report(final_report)

        FileReportSink(
            output_dir_template=dir_tmpl,
            output_template=output_template,
            theme=theme,
            pretty=pretty,
            sections=sections,
        ).emit(Report(final_report), formats=formats)
        CookiecutterPresentationRenderer(output_dir_template=dir_tmpl).render(
            Report(final_report)
        )
        _render_verdict_block(final_report, quiet=quiet)
        if evaluate and fail:
            level_order = {"critical": 1, "warning": 2, "info": 3}
            threshold = level_order.get(fail_level.lower())
            breached = (
                [
                    r.get("slug", "unknown")
                    for r in final_report.get("rules", [])
                    if not r.get("passed", False)
                    and level_order.get(r.get("level", "info").lower(), 3) <= threshold
                ]
                if threshold is not None
                else []
            )
            if breached:
                click.echo(
                    f"\nError: Analysis failed due to {len(breached)} rule breaches "
                    f"at level '{fail_level}' or above.",
                    err=True,
                )
                sys.exit(1)
        return

    all_analyzers = _discover_analyzers()
    if not all_analyzers:
        raise click.ClickException("No analyzers found. Is regis installed correctly?")

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
        selected = dict(all_analyzers)

    for skip_name in skip_analyzers:
        if skip_name not in all_analyzers:
            click.echo(
                f"  Warning: --skip references unknown analyzer '{skip_name}'",
                err=True,
            )
            continue
        selected.pop(skip_name, None)

    if not selected:
        raise click.ClickException("All analyzers were skipped — nothing to run.")

    effective_workers = min(max_workers, len(selected))
    _info(
        f"  Running {len(selected)} analyzer(s) with {effective_workers} worker(s)...",
        quiet=quiet,
    )
    name_width = max((len(n) for n in selected), default=12)

    def _on_progress(outcome: AnalyzerOutcome) -> None:
        timing = f"({outcome.elapsed:.1f}s)"
        if outcome.error_type is None:
            _info(f"  ✓ {outcome.name:<{name_width}}  {timing}", quiet=quiet)
            return
        label = _ERROR_LABEL.get(outcome.error_type, "error")
        click.echo(
            click.style(
                f"  ✗ {outcome.name:<{name_width}}  {timing}  {label} — {outcome.error_message}",
                fg="red",
            ),
            err=True,
        )

    image = ImageReference(
        registry=ref.registry,
        repository=ref.repository,
        tag=ref.tag,
        platform=platform,
    )

    use_case = build_analyze_image(
        username,
        password,
        output_dir_template=dir_tmpl,
        output_template=output_template,
        theme=theme,
        pretty=pretty,
        sections=sections,
    )

    def _on_playbook_progress(msg: str) -> None:
        _info(msg, quiet=quiet, err=True)

    from regis.core.application.analyze_image import AnalysisResult
    from regis.core.domain.errors import AnalyzerError, PlaybookError

    analysis: AnalysisResult
    try:
        analysis = use_case.run_and_evaluate(
            image,
            selected,
            url=url,
            digest=digest,
            formats=formats,
            metadata=_parse_meta(meta) or None,
            playbook_paths=playbook_paths,
            show_rules=evaluate,
            on_playbook_progress=_on_playbook_progress,
            fail_level=fail_level,
            max_workers=effective_workers,
            on_progress=_on_progress,
        )
    except (AnalyzerError, PlaybookError) as exc:
        raise click.ClickException(str(exc)) from exc

    _render_verdict_block(analysis.report, quiet=quiet)
    if evaluate and fail and analysis.has_breaches:
        click.echo(
            f"\nError: Analysis failed due to {analysis.breach_count} rule breaches "
            f"at level '{fail_level}' or above.",
            err=True,
        )
        sys.exit(1)
    return


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
        "or comma-separated analyzer slugs (e.g. 'cve,hadolint'). "
        "Only applies to --html."
    ),
)
@click.option(
    "--theme",
    default="default",
    type=click.Choice(["default"], case_sensitive=False),
    help="Theme to use for HTML report (default: default).",
)
def evaluate_cmd(
    input_path: str,
    playbook_paths: tuple[str, ...],
    output_template: str | None,
    output_dir_template: str | None,
    pretty: bool,
    theme: str,
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
        ensure_schema_version(analysis_report)
    else:
        raise click.ClickException(
            "Input file does not appear to be a regis report (missing 'results' key)."
        )

    formats = ["json"]
    if html_single:
        formats.append("html")

    if sections != "all" and not html_single:
        click.echo("  Warning: --sections has no effect without --html.", err=True)

    from regis.core.domain.errors import PlaybookError
    from regis.utils.report import _echo_progress

    try:
        build_evaluate(
            output_dir_template=output_dir_template or "reports/dry-run/{timestamp}",
            output_template=output_template,
            theme=theme,
            pretty=pretty,
            sections=sections,
        ).run(
            analysis_report,
            formats=formats,
            playbook_paths=playbook_paths,
            on_playbook_progress=_echo_progress,
        )
    except PlaybookError as exc:
        raise click.ClickException(str(exc)) from exc


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
