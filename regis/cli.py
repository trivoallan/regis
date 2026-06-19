"""CLI entry point for regis."""

from __future__ import annotations

import logging
import sys

import click

from regis.commands.analyze import analyze, evaluate_cmd, list_analyzers
from regis.commands.bootstrap import bootstrap
from regis.commands.check import check, version_cmd
from regis.commands.doctor import doctor
from regis.commands.playbook import playbook_group
from regis.commands.rules import rules_group
from regis.core.domain.analyzers.discovery import discover_analyzers
from regis.utils.process import require_tool, run_cmd
from regis.utils.report import (
    escape_jinja,
    format_output_path,
    render_and_save_reports,
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


@click.group()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose (DEBUG) logging.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress non-essential output. Errors and explicit results still print.",
)
@click.pass_context
def main(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """Regis — Registry Scores CLI."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet
    ctx.obj["verbose"] = verbose


main.add_command(analyze)
main.add_command(evaluate_cmd, name="evaluate")
main.add_command(list_analyzers, name="list")
main.add_command(bootstrap)
main.add_command(check)
main.add_command(version_cmd, name="version")
main.add_command(rules_group, name="rules")
main.add_command(doctor)
main.add_command(playbook_group, name="playbook")


if __name__ == "__main__":
    main()
