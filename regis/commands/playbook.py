"""playbook command group."""

from __future__ import annotations

import json
from importlib.resources import files
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

    from regis.playbook.loader import load_playbook

    try:
        playbook = load_playbook(path)
    except Exception as exc:
        raise click.ClickException(f"Failed to load playbook: {exc}") from exc

    schema_pkg = files("regis.schemas.playbook")
    schema = json.loads(
        schema_pkg.joinpath("definition.schema.json").read_text(encoding="utf-8")
    )
    jsonlogic_schema = json.loads(
        schema_pkg.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
    )

    from referencing import Registry, Resource

    registry = Registry().with_resources(
        [
            (schema.get("$id", ""), Resource.from_contents(schema)),
            (jsonlogic_schema.get("$id", ""), Resource.from_contents(jsonlogic_schema)),
            # Allow $ref to bare filename (definition.schema.json references jsonlogic.schema.json relatively)
            ("jsonlogic.schema.json", Resource.from_contents(jsonlogic_schema)),
        ]
    )

    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(playbook), key=lambda e: list(e.absolute_path))

    if errors:
        click.echo(f"  ✗ {path} is invalid:", err=True)
        for err in errors:
            click.echo(f"    - {_format_validation_error(err)}", err=True)
        raise click.exceptions.Exit(1)

    click.echo(f"  ✓ {path} is valid.")
