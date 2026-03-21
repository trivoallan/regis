"""check and version commands."""

from __future__ import annotations

from importlib.metadata import version

import click

from regis_cli.registry.client import RegistryClient, RegistryError
from regis_cli.registry.parser import parse_image_url


@click.command(name="check")
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


@click.command(name="version")
def version_cmd() -> None:
    """Show regis-cli version and exit."""
    click.echo(f"regis-cli version {version('regis-cli')}")
