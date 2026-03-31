"""rules command group."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from regis.analyzers.discovery import discover_analyzers


def _render_rule_markdown(rule: dict[str, Any]) -> str:
    """Render a single rule as a detailed Markdown document matching the documentation template."""
    slug = rule.get("slug", "unknown")
    description = rule.get("description", "n/a")
    provider = rule.get("provider", "custom")
    level = rule.get("level", "info")
    tags = rule.get("tags", [])
    params = rule.get("params", {})
    condition = rule.get("condition", {})
    messages = rule.get("messages", {})

    frontmatter = ["---"]
    if tags:
        frontmatter.append("tags:")
        for tag in tags:
            frontmatter.append(f"  - {tag}")
    frontmatter.append("  - rules")
    frontmatter.append("---\n")

    lines = [
        f"# {slug}",
        "",
        description,
        "",
        "| Provider | Level | Tags |",
        "| :--- | :--- | :--- |",
        f"| {provider} | {level.capitalize()} | {', '.join(tags)} |",
        "",
    ]

    if params:
        lines.append("## Parameters")
        lines.append("")
        lines.append("| Name | Default Value | Description |")
        lines.append("| :--- | :--- | :--- |")
        for k, v in params.items():
            lines.append(f"| `{k}` | `{v}` | n/a |")
        lines.append("")

    if messages:
        lines.append("## Messages")
        lines.append("")
        lines.append("| Type | Message |")
        lines.append("| :--- | :--- |")
        if "pass" in messages:
            lines.append(f"| **Pass** | {messages['pass']} |")
        if "fail" in messages:
            lines.append(f"| **Fail** | {messages['fail']} |")
        lines.append("")

    lines.append("## Playbook Example")
    lines.append("")
    lines.append("```yaml")
    lines.append("rules:")
    lines.append(f"  - provider: {provider}")

    rule_name = slug
    if "." in slug:
        rule_name = slug.split(".", 1)[1]

    lines.append(f"    rule: {rule_name}")

    if params:
        lines.append("    options:")
        import yaml

        params_yaml = yaml.dump(params, default_flow_style=False).strip()
        for p_line in params_yaml.splitlines():
            lines.append(f"      {p_line}")

    lines.append("```")
    lines.append("")

    if condition:
        lines.append("## Condition")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(condition, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(frontmatter + lines)


@click.group(name="rules")
def rules_group():
    """Manage and evaluate rules."""
    pass


@rules_group.command(name="list")
@click.option(
    "-r",
    "--rules",
    "rules_path",
    help="Path to an optional rules.yaml file to merge overrides.",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["text", "markdown"], case_sensitive=False),
    default="text",
    help="Output format (default: text).",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    help="Output filename for the rules list.",
)
@click.option(
    "-D",
    "--output-dir",
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="Directory to write individual rule markdown files (markdown format only).",
)
@click.option(
    "--index/--no-index",
    "generate_index",
    default=False,
    help="Generate an index.md file in the output directory (default: off).",
)
def list_rules(
    rules_path: str | None,
    output_format: str,
    output_file: str | None,
    output_dir: str | None = None,
    generate_index: bool = False,
) -> None:
    """List all available default rules and any overrides."""
    import yaml

    from regis.rules.evaluator import get_default_rules, merge_rules

    analyzers = discover_analyzers()
    defaults = get_default_rules(list(analyzers.keys()))

    custom = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("rules", [])

    final_rules = merge_rules(defaults, custom)
    final_rules.sort(key=lambda r: r.get("slug", ""))

    if not final_rules:
        click.echo("No rules found.")
        return

    if output_format.lower() == "markdown":
        if output_dir:
            out_root = Path(output_dir)
            out_root.mkdir(parents=True, exist_ok=True)

            for rule in final_rules:
                provider = rule.get("provider", "custom")
                slug = rule.get("slug", "unknown")

                rule_dir = out_root / provider
                rule_dir.mkdir(parents=True, exist_ok=True)

                rule_content = _render_rule_markdown(rule)
                (rule_dir / f"{slug}.md").write_text(rule_content, encoding="utf-8")

            click.echo(
                f"  ✓ {len(final_rules)} rule files written to {output_dir}", err=True
            )

            if generate_index:
                index_lines = []
                index_lines.append(
                    "| Provider | Slug | Description | Level | Tags | Parameters |"
                )
                index_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
                for rule in final_rules:
                    provider = rule.get("provider", "custom")
                    slug = rule.get("slug", "n/a")
                    description = rule.get("description", "n/a")
                    level = rule.get("level", "info")
                    tags = ", ".join(rule.get("tags", []))
                    params = rule.get("params", {})
                    params_str = ", ".join(f"`{k}={v}`" for k, v in params.items())

                    link = f"./{provider}/{slug}.md"
                    index_lines.append(
                        f"| {provider} | [`{slug}`]({link}) | {description} | {level} | {tags} | {params_str} |"
                    )
                index_content = "\n".join(index_lines) + "\n"
                (out_root / "index.md").write_text(index_content, encoding="utf-8")
                click.echo(f"  ✓ Index file written to {output_dir}/index.md", err=True)
            return

        lines = []
        lines.append("| Provider | Slug | Description | Level | Tags | Parameters |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

        for rule in final_rules:
            provider = rule.get("provider", "custom")
            slug = rule.get("slug", "n/a")
            description = rule.get("description", "n/a")
            level = rule.get("level", "info")
            tags = ", ".join(rule.get("tags", []))
            params = rule.get("params", {})
            params_str = ""
            if params:
                params_str = ", ".join(f"`{k}={v}`" for k, v in params.items())
            lines.append(
                f"| {provider} | `{slug}` | {description} | {level} | {tags} | {params_str} |"
            )
        content = "\n".join(lines) + "\n"
    else:
        lines = []
        for rule in final_rules:
            enabled = rule.get("enable", True)
            enabled_mark = "[x]" if enabled else "[ ]"
            params = rule.get("params", {})
            params_str = ""
            if params:
                params_str = f" ({', '.join(f'{k}={v}' for k, v in params.items())})"
            lines.append(
                f"  {enabled_mark} {rule.get('slug', 'unnamed'):25s} {rule.get('level', 'info'):8s} {rule.get('description', '')}{params_str}"
            )
        content = "\n".join(lines) + "\n"

    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        click.echo(f"  Rules list written to {output_file}", err=True)
    else:
        click.echo(content)


@rules_group.command(name="show")
@click.argument("slug")
@click.option(
    "-r",
    "--rules",
    "rules_path",
    help="Path to an optional rules.yaml file to merge overrides.",
)
def show_rule(slug: str, rules_path: str | None) -> None:
    """Display the full definition of a specific rule."""
    import yaml

    from regis.rules.evaluator import get_default_rules, merge_rules

    analyzers = discover_analyzers()
    defaults = get_default_rules(list(analyzers.keys()))

    custom = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("rules", [])

    final_rules = merge_rules(defaults, custom)
    matching_rule = next((r for r in final_rules if r.get("slug") == slug), None)

    if not matching_rule:
        raise click.ClickException(f"Rule '{slug}' not found.")

    click.echo(json.dumps(matching_rule, indent=2))


@rules_group.command(name="evaluate")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-r",
    "--rules",
    "rules_path",
    help="Path to custom rules.yaml file.",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    help="Output filename for the evaluation result (JSON format).",
)
@click.option(
    "--fail",
    is_flag=True,
    default=False,
    help="Fail command execution if any rule is breached.",
)
@click.option(
    "--fail-level",
    default="critical",
    type=click.Choice(["info", "warning", "critical"], case_sensitive=False),
    help="Minimum rule level that triggers a command failure (default: critical).",
)
def eval_rules(
    input_path: str,
    rules_path: str | None,
    output_file: str | None,
    fail: bool,
    fail_level: str,
) -> None:
    """Evaluate a regis JSON report against rules."""
    import yaml

    from regis.rules.evaluator import evaluate_rules

    try:
        report_data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(f"Failed to load report file: {exc}") from exc

    rules_def = None
    if rules_path:
        try:
            rules_def = yaml.safe_load(Path(rules_path).read_text(encoding="utf-8"))
        except Exception as exc:
            raise click.ClickException(f"Failed to load rules file: {exc}") from exc

    result = evaluate_rules(report_data, rules_def)

    if output_file:
        Path(output_file).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        click.echo(f"Evaluation report written to {output_file}", err=True)
    else:
        score = result["score"]
        click.echo(
            f"\nRules Evaluation Score: {score}% ({result['passed_rules']}/{result['all_rules']})"
        )
        click.echo("-" * 40)
        for r in result["rules"]:
            icon = "✅" if r["passed"] else "❌"
            if r["status"] == "incomplete":
                icon = "⚠️"
            click.echo(f"{icon} [{r['slug']}] {r['message']}")

    if fail:
        level_order = {"critical": 1, "warning": 2, "info": 3, "none": 4}
        threshold = level_order.get(fail_level.lower(), 1)

        breaches = []
        for r in result["rules"]:
            if not r["passed"]:
                rule_level = r.get("level", "info").lower()
                if level_order.get(rule_level, 3) <= threshold:
                    breaches.append(r["slug"])

        if breaches:
            click.echo(
                f"\nError: Evaluation failed due to {len(breaches)} rule breaches at level '{fail_level}' or above.",
                err=True,
            )
            sys.exit(1)
