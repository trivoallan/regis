"""CLI entry point for regis."""

from __future__ import annotations

import logging
import sys

import click

from regis.analyzers.discovery import discover_analyzers
from regis.commands.analyze import analyze, evaluate_cmd, list_analyzers
from regis.commands.archive import archive
from regis.commands.bootstrap import bootstrap
from regis.commands.check import check, version_cmd
from regis.commands.dashboard import dashboard_group
from regis.commands.rules import rules_group
from regis.github_cli import github_cmd
from regis.gitlab_cli import gitlab_cmd
from regis.utils.process import require_tool, run_cmd
from regis.utils.report import (
    escape_jinja,
    format_output_path,
    render_and_save_reports,
    render_mr_templates,
    run_playbooks,
    set_nested_value,
    validate_report,
    write_report,
)

# Aliases kept for backward compatibility (tests patch these names)
_discover_analyzers = discover_analyzers
_run_cmd = run_cmd
_require_tool = require_tool
_format_output_path = format_output_path
_write_report = write_report
_set_nested_value = set_nested_value
_escape_jinja = escape_jinja
_run_playbooks = run_playbooks
_validate_report = validate_report
_render_and_save_reports = render_and_save_reports
_render_mr_templates = render_mr_templates


@click.group()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose (DEBUG) logging.",
)
def main(verbose: bool) -> None:
    """Regis — Registry Scores CLI."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


main.add_command(github_cmd, name="github")
main.add_command(gitlab_cmd, name="gitlab")
main.add_command(analyze)
main.add_command(evaluate_cmd, name="evaluate")
main.add_command(list_analyzers, name="list")
main.add_command(bootstrap)
main.add_command(archive)
main.add_command(check)
main.add_command(version_cmd, name="version")
main.add_command(rules_group, name="rules")
main.add_command(dashboard_group, name="dashboard")


if __name__ == "__main__":
    main()
