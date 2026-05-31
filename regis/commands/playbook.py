"""playbook command group."""

from __future__ import annotations

from pathlib import Path

import click


def _format_validation_error(error) -> str:
    """Render a jsonschema ValidationError as a single human-readable line."""
    if error.absolute_path:
        location = ".".join(str(p) for p in error.absolute_path)
    else:
        location = "<root>"
    return f"{location}: {error.message}"


@click.group(name="playbook")
def playbook_group() -> None:
    """Inspect and validate playbooks."""


@playbook_group.command(name="validate")
@click.argument("path", type=click.Path(exists=True, dir_okay=True, path_type=Path))
def validate_playbook(path: Path) -> None:
    """Validate a playbook YAML/JSON file (or bundle directory) against the schema."""
    import jsonschema

    from regis.playbook.loader import PlaybookVersionError, load_playbook

    try:
        playbook = load_playbook(path)
    except PlaybookVersionError as exc:
        click.echo(f"  ✗ {path} is invalid:", err=True)
        for line in str(exc).splitlines():
            click.echo(f"    {line}", err=True)
        raise click.exceptions.Exit(1) from exc
    except jsonschema.ValidationError as exc:
        click.echo(f"  ✗ {path} is invalid:", err=True)
        click.echo(f"    - {_format_validation_error(exc)}", err=True)
        raise click.exceptions.Exit(1) from exc
    except Exception as exc:
        # YAML/JSON parse errors, missing file, etc.
        raise click.ClickException(f"Failed to load playbook: {exc}") from exc

    click.echo(
        f"  ✓ {path} is valid (schemaVersion={playbook['schemaVersion']}, "
        f"version={playbook['version']})."
    )
