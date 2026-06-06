"""playbook command group."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import click

# Token matched only as the *prefix* of a dotted path (e.g. ``rule.params.x``),
# never inside another identifier such as ``rules_summary`` or ``ruler``.
_LEGACY_VAR_PREFIX = "rule."
_NEW_VAR_PREFIX = "criterion."

# Matches an innermost ``${...}`` interpolation span (no nested braces/dollars),
# mirroring the evaluator's multi-pass resolution of nested patterns. Rewriting
# only the innermost spans makes nested interpolation like
# ``${results.cve.${rule.params.level}_count}`` safe: the inner ``${rule.…}`` is
# rewritten without ever capturing the outer ``${results.…}`` braces.
_INTERPOLATION_RE = re.compile(r"\$\{([^${}]+)\}")


def _migrate_var_path(path: str) -> str:
    """Rewrite a JSON-Logic ``var`` path from the ``rule.`` namespace.

    Only a path that *starts* with ``rule.`` is rewritten; ``results.*`` and
    unrelated identifiers (``rules_summary``, ``ruler``) are left untouched.
    Idempotent: an already-``criterion.`` path is returned unchanged.
    """
    if path == "rule":
        # Bare operand: ``{"var": "rule"}`` binds the whole criterion object via
        # the engine's dual-bind. It must become ``criterion`` (no trailing dot),
        # otherwise ``{"var": "criterion."}`` resolves to ``None`` and migration
        # would change evaluation.
        return "criterion"
    if path.startswith(_LEGACY_VAR_PREFIX):
        return _NEW_VAR_PREFIX + path[len(_LEGACY_VAR_PREFIX) :]
    return path


def _migrate_condition_tree(node: Any) -> Any:
    """Recursively rewrite ``rule.`` references in a JSON-Logic condition tree.

    Performs a structured walk of the dict/list tree. For any ``{"var": "..."}``
    operand whose string path starts with ``rule.`` the path is rewritten to the
    ``criterion.`` namespace. ``results.*`` metric paths are preserved. The walk
    is non-mutating and idempotent.
    """
    if isinstance(node, dict):
        out: dict[Any, Any] = {}
        for key, value in node.items():
            if key == "var" and isinstance(value, str):
                out[key] = _migrate_var_path(value)
            elif key == "var" and isinstance(value, list) and value:
                # `var` may take the form ["path", default]; rewrite the path.
                new_value = list(value)
                if isinstance(new_value[0], str):
                    new_value[0] = _migrate_var_path(new_value[0])
                else:
                    new_value[0] = _migrate_condition_tree(new_value[0])
                new_value[1:] = [_migrate_condition_tree(v) for v in new_value[1:]]
                out[key] = new_value
            else:
                out[key] = _migrate_condition_tree(value)
        return out
    if isinstance(node, list):
        return [_migrate_condition_tree(item) for item in node]
    return node


def _migrate_message(template: str) -> str:
    """Rewrite ``${rule.…}`` interpolations in a message template.

    Only the token inside an *innermost* ``${...}`` span is considered, so a
    nested interpolation such as ``${results.cve.${rule.params.level}_count}``
    has its inner ``${rule.…}`` rewritten while the surrounding ``${results.…}``
    span is left untouched. Idempotent.
    """
    if not template:
        return template

    def _repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        stripped = inner.strip()
        if stripped == "rule" or stripped.startswith(_LEGACY_VAR_PREFIX):
            inner = inner.replace("rule", "criterion", 1)
        return "${" + inner + "}"

    # Loop until stable so an inner span exposed after rewriting an outer one is
    # also handled (mirrors the evaluator's nested-interpolation resolution).
    while True:
        new_template = _INTERPOLATION_RE.sub(_repl, template)
        if new_template == template:
            return template
        template = new_template


def _migrate_rule_entry(entry: Any) -> None:
    """Migrate a single playbook rule entry in place.

    Renames the legacy template-reference key ``rule:`` → ``criterion:`` and
    rewrites ``rule.`` references inside ``condition`` and ``messages``.
    """
    if not isinstance(entry, dict):
        return

    # 1. Template-reference key: rule -> criterion (preserve insertion order).
    if "rule" in entry and "criterion" not in entry:
        # ruamel's CommentedMap supports insert(pos, key, value) to keep order.
        # Known limitation: a trailing INLINE comment on the renamed ``rule:`` key
        # itself is dropped, because that comment is anchored to the old key and
        # the insert+del swap does not carry it over. Block comments and other
        # inline comments ARE preserved, and key order IS preserved.
        if hasattr(entry, "insert"):
            keys = list(entry.keys())
            pos = keys.index("rule")
            value = entry["rule"]
            entry.insert(pos, "criterion", value)
            del entry["rule"]
        else:
            rebuilt = {("criterion" if k == "rule" else k): v for k, v in entry.items()}
            entry.clear()
            entry.update(rebuilt)

    # 2. Condition tree.
    if "condition" in entry:
        entry["condition"] = _migrate_condition_tree(entry["condition"])

    # 3. Messages.
    messages = entry.get("messages")
    if isinstance(messages, dict):
        for key, value in list(messages.items()):
            if isinstance(value, str):
                messages[key] = _migrate_message(value)


def _migrate_integrations_to_presentation(container: Any) -> None:
    """Move ``integrations.gitlab.{badges,checklist,checklists,templates}`` to a
    platform-neutral ``presentation`` block on the same container. Idempotent.

    Folds the deprecated singular ``checklist`` into ``checklists``.
    """
    if not isinstance(container, dict):
        return
    integrations = container.get("integrations")
    if not isinstance(integrations, dict):
        return
    gitlab = integrations.get("gitlab")
    if not isinstance(gitlab, dict):
        return

    presentation = container.get("presentation")
    if not isinstance(presentation, dict):
        presentation = {}

    if "badges" in gitlab and "badges" not in presentation:
        presentation["badges"] = gitlab["badges"]
    if "templates" in gitlab and "templates" not in presentation:
        presentation["templates"] = gitlab["templates"]

    checklists = gitlab.get("checklists")
    if not checklists and gitlab.get("checklist"):
        # fold the deprecated singular `checklist` into the `checklists` shape
        checklists = [{"items": gitlab["checklist"]}]
    if checklists and "checklists" not in presentation:
        presentation["checklists"] = checklists

    if presentation:
        container["presentation"] = presentation

    # remove the now-migrated gitlab integration; drop `integrations` if empty
    integrations.pop("gitlab", None)
    if not integrations:
        container.pop("integrations", None)


def _migrate_playbook_data(data: Any) -> None:
    """Migrate a parsed playbook document in place (``rule`` → ``criterion``).

    Handles both the ``apiVersion``/``spec`` envelope (rule entries under
    ``spec.rules``) and a legacy flat document (top-level ``rules``).
    """
    if not isinstance(data, dict):
        return
    spec = data.get("spec")
    rules = None
    if isinstance(spec, dict) and isinstance(spec.get("rules"), list):
        rules = spec["rules"]
    elif isinstance(data.get("rules"), list):
        rules = data["rules"]
    if rules is None:
        return
    for entry in rules:
        _migrate_rule_entry(entry)

    # presentation migration (integrations.gitlab -> presentation)
    if isinstance(spec, dict):
        _migrate_integrations_to_presentation(spec)
    else:
        _migrate_integrations_to_presentation(data)


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
    for key in ("tiers", "rules", "badges", "integrations", "presentation", "links"):
        if key in data:
            spec[key] = data[key]

    dropped = [k for k in ("pages", "sections", "sidebar") if k in data]

    new_doc = CommentedMap()
    new_doc["apiVersion"] = "regis.io/v1alpha1"
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


@playbook_group.command(name="migrate")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-i",
    "--in-place",
    "in_place",
    is_flag=True,
    default=False,
    help="Overwrite the file in place instead of writing the result to stdout.",
)
def migrate_playbook(path: Path, in_place: bool) -> None:
    """Migrate a playbook from the legacy ``rule`` vocabulary to ``criterion``.

    Rewrites two surfaces of the playbook:

    1. each rule entry's template-reference key ``rule:`` → ``criterion:``;
    2. ``rule.`` references in JSON-Logic ``condition`` trees and ``${rule.…}``
       interpolations in ``messages`` → ``criterion`` (``results.*`` metric
       paths are left untouched).
    3. ``spec.integrations.gitlab`` → platform-neutral ``spec.presentation``
       (folding the deprecated singular ``checklist`` into ``checklists``).

    Comments and formatting are preserved via round-trip YAML. The codemod is
    idempotent: running it on an already-migrated playbook is a no-op. By
    default the migrated content is written to stdout; pass ``--in-place`` to
    overwrite the file.
    """
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.load(f)
    except Exception as exc:
        raise click.ClickException(f"Failed to load playbook: {exc}") from exc

    if data is None:
        raise click.ClickException(
            f"{path}: file is empty or not a valid YAML document."
        )

    _migrate_playbook_data(data)

    if in_place:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        click.echo(
            f"  Migrated {path} (rule -> criterion). "
            f"Run `regis playbook validate {path}` to verify.",
            err=True,
        )
    else:
        import sys

        yaml.dump(data, sys.stdout)
