"""React report viewer commands for regis-cli."""

import http.server
import json
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
    """Export the viewer app alongside the target report for static hosting."""
    assets_dir = get_viewer_assets_dir()
    output.mkdir(parents=True, exist_ok=True)

    click.echo(f"Exporting viewer assets to {output} ...")
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
@click.option(
    "-a",
    "--archive",
    "archives",
    multiple=True,
    help='Named archive to include, format "Name:path-or-url". Repeatable.',
)
def serve_cmd(  # pragma: no cover
    port: int, report: Path | None = None, archives: tuple[str, ...] = ()
) -> None:
    """Serve the static React viewer and preview the report locally."""
    assets_dir = get_viewer_assets_dir()

    archives_payload: bytes | None = None
    if archives:
        parsed = _parse_archives(archives)
        archives_payload = json.dumps({"archives": parsed}, indent=2).encode()

    class ReportRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            # Python 3.7+ supports the directory argument
            super().__init__(*args, directory=str(assets_dir), **kwargs)

        def do_GET(self) -> None:
            if (
                archives_payload is not None
                and self.path.split("?")[0] == "/archives.json"
            ):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(archives_payload)))
                self.end_headers()
                self.wfile.write(archives_payload)
                return
            super().do_GET()

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
