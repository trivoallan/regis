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
        f"  ✓ {path} is valid (apiVersion={playbook['apiVersion']}, "
        f"kind={playbook['kind']}, version={playbook.get('version')})."
    )


@playbook_group.command(name="upgrade")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def upgrade_playbook(path: Path) -> None:
    """Inject schemaVersion and version into a legacy playbook file.

    Preserves comments and formatting via ruamel.yaml. Idempotent: if both
    fields are already present, the file is left untouched.
    """
    from ruamel.yaml import YAML
    from ruamel.yaml.scalarstring import DoubleQuotedScalarString

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(path, encoding="utf-8") as f:
        data = yaml.load(f)

    if data is None:
        raise click.ClickException(
            f"{path}: file is empty or not a valid YAML document."
        )

    changes: list[str] = []
    if "schemaVersion" not in data:
        data.insert(0, "schemaVersion", 1)
        changes.append("schemaVersion")
    if "version" not in data:
        # Insert after schemaVersion (which is now guaranteed to exist).
        position = list(data.keys()).index("schemaVersion") + 1
        data.insert(position, "version", DoubleQuotedScalarString("1.0.0"))
        changes.append("version")

    if changes:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        click.echo(f"  Upgraded {path}: added {', '.join(changes)}.")
    else:
        click.echo(f"  {path}: already at schemaVersion 1, nothing to do.")
