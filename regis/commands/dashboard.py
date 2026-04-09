"""Dashboard commands for regis."""

import json
import logging
import shutil
import sys
import webbrowser
from pathlib import Path

import click

logger = logging.getLogger(__name__)


def get_dashboard_assets_dir() -> Path:
    """Returns the path to the bundled dashboard assets."""
    assets_dir = Path(__file__).parent.parent / "dashboard_assets"
    if not assets_dir.exists():
        click.echo(
            f"Error: Dashboard assets not found at {assets_dir}.\n"
            "This installation of regis might not have been packaged with the front-end build.",
            err=True,
        )
        sys.exit(1)
    return assets_dir


def _parse_archives(archives: tuple[str, ...]) -> list[dict[str, str]]:
    """Parses archive entries from CLI format into a list of dicts.

    Args:
        archives: Tuple of strings in "Name:path-or-url" format.

    Returns:
        List of {"name": ..., "path": ...} dicts.

    Raises:
        click.BadParameter: If any entry does not contain a colon separator.
    """
    result = []
    for entry in archives:
        if ":" not in entry:
            raise click.BadParameter(
                f'Invalid archive format {entry!r}. Expected "Name:path-or-url".',
                param_hint="'--archive'",
            )
        name, path = entry.split(":", 1)
        if not name.strip() or not path.strip():
            raise click.BadParameter(
                f'Invalid archive format {entry!r}. Expected "Name:path-or-url".',
                param_hint="'--archive'",
            )
        result.append({"name": name, "path": path})
    return result


@click.group()
def dashboard_group() -> None:
    """Preview or export interactive security reports."""
    pass


@dashboard_group.command(name="export")
@click.argument(
    "report",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory to export the static site into.",
)
@click.option(
    "-a",
    "--archive",
    "archives",
    multiple=True,
    help='Named archive to include, format "Name:path-or-url". Repeatable.',
)
def export_cmd(
    output: Path, report: Path | None = None, archives: tuple[str, ...] = ()
) -> None:
    """Export the dashboard app alongside the target report for static hosting."""
    assets_dir = get_dashboard_assets_dir()
    output.mkdir(parents=True, exist_ok=True)

    click.echo(f"Exporting dashboard assets to {output} ...")
    shutil.copytree(assets_dir, output, dirs_exist_ok=True)

    if report:
        dest_report = output / "report.json"
        shutil.copy2(report, dest_report)

    if archives:
        parsed = _parse_archives(archives)
        archives_path = output / "archives.json"
        archives_path.write_text(
            json.dumps({"archives": parsed}, indent=2), encoding="utf-8"
        )
        click.echo(f"Archives config written: {archives_path}")

    click.echo(f"Successfully exported to {output}")
    click.echo("You can now host this directory using any static web server.")


@dashboard_group.command(name="serve")
@click.argument(
    "report",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=8000,
    help="Port to listen on (default: 8000).",
)
@click.option(
    "-a",
    "--archive",
    "archives",
    multiple=True,
    help='Named archive to include, format "Name:path-or-url". Repeatable.',
)
@click.option(
    "--gitlab-url",
    envvar="GITLAB_URL",
    default=None,
    help="GitLab instance URL (e.g. https://gitlab.com). Env: GITLAB_URL.",
)
@click.option(
    "--gitlab-token",
    envvar="GITLAB_TOKEN",
    default=None,
    help="GitLab private token. Env: GITLAB_TOKEN.",
)
@click.option(
    "--gitlab-project",
    envvar="GITLAB_PROJECT",
    default=None,
    help="GitLab project ID or path. Env: GITLAB_PROJECT.",
)
@click.option(
    "--webhook-secret",
    envvar="REGIS_WEBHOOK_SECRET",
    default=None,
    help="Secret token to validate incoming webhooks. Env: REGIS_WEBHOOK_SECRET.",
)
def serve_cmd(  # pragma: no cover
    port: int,
    report: Path | None = None,
    archives: tuple[str, ...] = (),
    gitlab_url: str | None = None,
    gitlab_token: str | None = None,
    gitlab_project: str | None = None,
    webhook_secret: str | None = None,
) -> None:
    """Serve the interactive dashboard and preview the report locally."""
    import uvicorn

    from regis.server.app import create_app

    assets_dir = get_dashboard_assets_dir()

    parsed_archives = _parse_archives(archives) if archives else None

    app = create_app(
        assets_dir=assets_dir,
        report=report.absolute() if report else None,
        archives=parsed_archives,
        gitlab_url=gitlab_url,
        gitlab_token=gitlab_token,
        gitlab_project=gitlab_project,
        webhook_secret=webhook_secret,
    )

    url = f"http://localhost:{port}/"
    if report:
        click.echo(f"Serving report from {report}")
    click.echo(f"Dashboard application running at {url}")

    webbrowser.open(url)

    log_level = "debug" if logger.isEnabledFor(logging.DEBUG) else "warning"
    uvicorn.run(app, host="127.0.0.1", port=port, log_level=log_level)  # noqa: S104
