"""archive command group."""

from __future__ import annotations

import json
from pathlib import Path

import click


@click.group()
def archive():
    """Manage the report archive."""


@archive.command("add")
@click.argument(
    "report_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--archive-dir",
    "-A",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    required=True,
    help="Archive directory to add the report to.",
)
def archive_add(report_file: Path, archive_dir: Path):
    """Add an existing report JSON file to the archive."""
    from regis_cli.archive.store import add_to_archive

    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise click.ClickException(f"Could not read {report_file}: {exc}") from exc

    dest = add_to_archive(report, archive_dir)
    click.echo(f"Archived to {dest}")
    click.echo(f"Manifest updated: {archive_dir / 'manifest.json'}")
