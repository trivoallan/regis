"""Click-free core playbook runner and report validator.

This module is part of the hexagonal core (``core.application`` layer) and
must never import ``click``.  The driving CLI adapter in
``regis.utils.report`` wraps these functions and translates
:class:`~regis.core.domain.errors.PlaybookError` into
``click.ClickException`` at the process boundary.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema

from regis.core.domain.errors import PlaybookError


def run_playbooks(
    playbook_paths: tuple[str, ...],
    analysis_report: dict[str, Any],
    *,
    show_rules: bool = False,
    on_progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Load and evaluate playbooks, returning the merged final report dict.

    Args:
        playbook_paths: Paths (local or remote URLs) to playbook files/dirs.
            When empty, the built-in default playbook is used.
        analysis_report: The analyzer output envelope to evaluate against.
        show_rules: When ``True``, progress messages include per-rule icons.
        on_progress: Optional callback invoked with a progress message string
            for each notable step (playbook load, score summary, rule listing).
            Replaces click echoes — callers provide their own sink.

    Returns:
        A copy of ``analysis_report`` merged with ``playbooks``, ``playbook``,
        and ``links`` keys populated from evaluation results.

    Raises:
        PlaybookError: When a playbook cannot be loaded, fails schema
            validation, or the path does not exist.
    """
    from regis.core.domain.playbook.engine import evaluate, load_playbook
    from regis.core.domain.playbook.loader import PlaybookVersionError

    def _progress(msg: str) -> None:
        if on_progress is not None:
            on_progress(msg)

    resolved_paths: tuple[str, ...] = playbook_paths
    if not resolved_paths:
        default_pb = resources.files("regis") / "playbooks" / "default"
        if default_pb.is_dir():
            resolved_paths = (str(default_pb),)

    playbook_results: list[dict[str, Any]] = []

    for pb_path in resolved_paths:
        is_remote = isinstance(pb_path, str) and (
            pb_path.startswith("http://") or pb_path.startswith("https://")
        )
        action = "Downloading" if is_remote else "Evaluating"
        _progress(f"  {action} playbook: {pb_path}...")

        try:
            pb_def = load_playbook(pb_path)
        except PlaybookVersionError as exc:
            raise PlaybookError(f"Failed to load playbook '{pb_path}': {exc}") from exc
        except jsonschema.ValidationError as exc:
            raise PlaybookError(
                f"Playbook '{pb_path}' failed schema validation: {exc.message}"
            ) from exc
        except OSError as exc:
            raise PlaybookError(f"Failed to read playbook '{pb_path}': {exc}") from exc

        pb_result = evaluate(pb_def, analysis_report, source_name=Path(pb_path).stem)
        playbook_results.append(pb_result)

        rs = pb_result.get("rules_summary", {})
        passed_rules = rs.get("passed", [])
        total_rules = rs.get("total", [])
        passed_count = (
            len(passed_rules) if isinstance(passed_rules, list) else passed_rules
        )
        total_count = len(total_rules) if isinstance(total_rules, list) else total_rules
        rules_score = rs.get("score", pb_result.get("score", 0))
        _progress(f"    ({passed_count}/{total_count} rules passed, {rules_score}%)\n")

        if show_rules and pb_result.get("rules"):
            _progress("    Rules Evaluation Summary:")
            for r in pb_result["rules"]:
                icon = "✅" if r["passed"] else "❌"
                if r["status"] == "incomplete":
                    icon = "⚠️"
                _progress(f"      {icon} [{r['slug']}] {r['message']}")
            _progress("")

    final_report = {**analysis_report}
    if playbook_results:
        final_report["playbooks"] = playbook_results
        final_report["playbook"] = playbook_results[0]

    all_links: list[dict[str, Any]] = []
    for pb_res in playbook_results:
        for link_def in pb_res.get("links", []):
            if link_def not in all_links:
                all_links.append(link_def)

    if all_links:
        final_report["links"] = all_links

    return final_report


def validate_report(report: dict[str, Any]) -> None:
    """Validate a final report against the regis JSON Schema.

    Args:
        report: The report dict to validate.

    Raises:
        PlaybookError: When the report fails schema validation.
    """
    from referencing import Registry, Resource

    schemas_dir = resources.files("regis.schemas")
    registry: Any = Registry()
    report_schema = None
    base_uri = "https://trivoallan.github.io/regis/schemas/"

    def _get_all_schemas(node: Any, prefix: str = "") -> list[tuple[str, Any]]:
        found = []
        for item in node.iterdir():
            rel_path = f"{prefix}/{item.name}" if prefix else item.name
            if item.is_dir():
                found.extend(_get_all_schemas(item, rel_path))
            elif item.name.endswith(".json"):
                found.append((rel_path, item))
        return found

    for rel_path, schema_file in _get_all_schemas(schemas_dir):
        schema_data = json.loads(schema_file.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema_data)

        registry = registry.with_resource(uri=rel_path, resource=resource)
        registry = registry.with_resource(uri=schema_file.name, resource=resource)
        registry = registry.with_resource(uri=base_uri + rel_path, resource=resource)
        registry = registry.with_resource(
            uri=base_uri + schema_file.name, resource=resource
        )

        if "$id" in schema_data:
            registry = registry.with_resource(uri=schema_data["$id"], resource=resource)

        if schema_file.name == "report.schema.json":
            report_schema = schema_data

    if report_schema:
        from jsonschema.validators import validator_for

        try:
            validator_cls = validator_for(report_schema)
            validator = validator_cls(report_schema, registry=registry)
            validator.validate(instance=report)
        except jsonschema.ValidationError as exc:
            raise PlaybookError(
                f"Report schema validation failed: {exc.message}"
            ) from exc
