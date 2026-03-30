"""React report viewer commands for regis-cli."""

import http.server
import logging
import os
import shutil
import socketserver
import sys
import webbrowser
from pathlib import Path

import click

logger = logging.getLogger(__name__)


def get_viewer_assets_dir() -> Path:
    """Returns the path to the bundled viewer assets."""
    assets_dir = Path(__file__).parent.parent / "viewer_assets"
    if not assets_dir.exists():
        click.echo(
            f"Error: Viewer assets not found at {assets_dir}.\n"
            "This installation of regis_cli might not have been packaged with the front-end build.",
            err=True,
        )
        sys.exit(1)
    return assets_dir


@click.group()
def viewer_group() -> None:
    """Preview or export interactive security reports."""
    pass


@viewer_group.command(name="export")
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
def export_cmd(output: Path, report: Path | None = None) -> None:
    """Export the viewer app alongside the target report for static hosting."""
    assets_dir = get_viewer_assets_dir()
    output.mkdir(parents=True, exist_ok=True)

    click.echo(f"Exporting viewer assets to {output} ...")
    shutil.copytree(assets_dir, output, dirs_exist_ok=True)

    if report:
        dest_report = output / "report.json"
        shutil.copy2(report, dest_report)

    click.echo(f"Successfully exported to {output}")
    click.echo("You can now host this directory using any static web server.")


@viewer_group.command(name="serve")
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
def serve_cmd(port: int, report: Path | None = None) -> None:  # pragma: no cover
    """Serve the static React viewer and preview the report locally."""
    assets_dir = get_viewer_assets_dir()

    class ReportRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # Python 3.7+ supports the directory argument
            super().__init__(*args, directory=str(assets_dir), **kwargs)

        def translate_path(self, path: str) -> str:
            if report and path == "/report.json":
                return str(report.absolute())

            res = super().translate_path(path)
            # SPA Fallback for Docusaurus/React
            if not os.path.exists(res):
                return str(assets_dir / "index.html")
            return res

        def log_message(self, format: str, *args) -> None:
            if logger.isEnabledFor(logging.DEBUG):
                super().log_message(format, *args)

    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(("", port), ReportRequestHandler)
    except OSError as e:
        click.echo(f"Error binding to port {port}: {e}", err=True)
        sys.exit(1)

    url = f"http://localhost:{port}/"
    if report:
        click.echo(f"Serving report from {report}")
    click.echo(f"Viewer application running at {url}")

    try:
        webbrowser.open(url)
        httpd.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")
        httpd.server_close()
