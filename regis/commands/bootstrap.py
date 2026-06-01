"""bootstrap command group (playbook, gitlab-ci, and tools subcommands)."""

from __future__ import annotations

from pathlib import Path

import click

from regis.tools.fetcher import ToolFetcher, ToolFetchError


@click.group(name="bootstrap")
def bootstrap():
    """Bootstrap a new project or playbook."""
    pass


@bootstrap.command(name="playbook")
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json defaults.",
)
def bootstrap_playbook(output_dir: str, no_input: bool) -> None:
    """Bootstrap a new RegiS playbook."""
    try:
        from importlib import resources

        from cookiecutter.main import cookiecutter
    except ImportError as exc:
        raise click.ClickException(
            f"cookiecutter not found or failed to import: {exc}. Please install it with 'pip install cookiecutter'."
        ) from None

    template_path = resources.files("regis") / "cookiecutters" / "playbook"

    click.echo(f"Bootstrapping playbook into {output_dir}...", err=True)
    try:
        project_dir = cookiecutter(
            str(template_path),
            no_input=no_input,
            output_dir=output_dir,
        )
        click.echo("  ✓ Playbook bootstrapped successfully.", err=True)

        notes_file = Path(project_dir) / ".regis-post-install.md"
        if notes_file.exists():
            click.echo("\n" + "=" * 40, err=True)
            click.echo("POST-INSTALL NOTES:", err=True)
            click.echo("=" * 40, err=True)
            click.echo(notes_file.read_text(encoding="utf-8"), err=True)
            click.echo("=" * 40 + "\n", err=True)
            notes_file.unlink()

    except Exception as exc:
        raise click.ClickException(f"Failed to bootstrap playbook: {exc}") from exc


@bootstrap.command(name="gitlab-ci")
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json defaults.",
)
def bootstrap_gitlab_ci(output_dir: str, no_input: bool) -> None:
    """Scaffold a GitLab CI pipeline for the Request-to-MR analysis workflow."""
    try:
        from importlib import resources

        from cookiecutter.main import cookiecutter
    except ImportError as exc:
        raise click.ClickException(
            f"cookiecutter not found or failed to import: {exc}. "
            "Please install it with 'pip install cookiecutter'."
        ) from None

    template_path = resources.files("regis") / "cookiecutters" / "gitlab-ci"

    click.echo(f"Scaffolding GitLab CI pipeline into {output_dir}...", err=True)
    try:
        project_dir = cookiecutter(
            str(template_path),
            no_input=no_input,
            output_dir=output_dir,
        )
        click.echo("  ✓ GitLab CI pipeline scaffolded successfully.", err=True)

        notes_file = Path(project_dir) / ".regis-post-install.md"
        if notes_file.exists():
            click.echo("\n" + "=" * 40, err=True)
            click.echo("POST-INSTALL NOTES:", err=True)
            click.echo("=" * 40, err=True)
            click.echo(notes_file.read_text(encoding="utf-8"), err=True)
            click.echo("=" * 40 + "\n", err=True)
            notes_file.unlink()

    except Exception as exc:
        raise click.ClickException(
            f"Failed to scaffold GitLab CI pipeline: {exc}"
        ) from exc


@bootstrap.command(name="tools")
@click.option("--tool", "tool_name", default=None, help="Fetch a single tool.")
@click.option("--check", is_flag=True, help="Show status without downloading.")
def bootstrap_tools(tool_name: str | None, check: bool) -> None:
    """Fetch (or check) tool binaries declared in the manifest."""
    fetcher = ToolFetcher()
    if check:
        for status in fetcher.status():
            if status.cached and status.sha256_ok:
                mark = "✓"
            elif status.cached and status.sha256_ok is False:
                mark = "✗"
            else:
                mark = "⏩"
            path = str(status.path) if status.path else "(not cached)"
            click.echo(f"  {mark} {status.name:<12} {status.version:<10} {path}")
        return
    names = [tool_name] if tool_name else None
    try:
        result = fetcher.fetch_all(names=names)
    except ToolFetchError as exc:
        raise click.ClickException(str(exc)) from exc
    for name, fetched_path in result.items():
        click.echo(f"  ✓ {name:<12} -> {fetched_path}")
