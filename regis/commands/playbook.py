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
    """Convert a legacy flat playbook into the apiVersion/kind/metadata/spec envelope.

    Idempotent: if the document already declares an ``apiVersion`` it is left
    untouched. Deprecated ``pages``/``sections``/``sidebar`` are dropped.
    """
    import re

    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(path, encoding="utf-8") as f:
        data = yaml.load(f)

    if data is None:
        raise click.ClickException(
            f"{path}: file is empty or not a valid YAML document."
        )

    if "apiVersion" in data:
        click.echo(
            f"  {path}: already uses the apiVersion/kind envelope, nothing to do."
        )
        return

    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
        return slug or "playbook"

    display_name = data.get("name")
    slug = _slugify(data.get("slug") or display_name or "playbook")
    version = data.get("version") or "1.0.0"

    metadata = CommentedMap()
    metadata["name"] = slug
    if display_name:
        metadata["title"] = display_name
    if data.get("description"):
        metadata["description"] = data["description"]
    labels = CommentedMap()
    labels["app.kubernetes.io/version"] = version
    metadata["labels"] = labels

    spec = CommentedMap()
    for key in ("tiers", "rules", "badges", "integrations", "links"):
        if key in data:
            spec[key] = data[key]

    dropped = [k for k in ("pages", "sections", "sidebar") if k in data]

    new_doc = CommentedMap()
    new_doc["apiVersion"] = "regis.trivoallan.dev/v1alpha1"
    new_doc["kind"] = "Playbook"
    new_doc["metadata"] = metadata
    new_doc["spec"] = spec

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(new_doc, f)

    msg = f"  Upgraded {path} to the apiVersion/kind envelope."
    if dropped:
        msg += f" Dropped deprecated: {', '.join(dropped)}."
    msg += f" Run `regis playbook validate {path}` to verify."
    click.echo(msg)
