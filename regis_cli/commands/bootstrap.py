"""bootstrap command group (playbook and archive subcommands)."""

from __future__ import annotations

import json
import subprocess  # nosec B404
from pathlib import Path

import click

from regis_cli.utils.process import require_tool, run_cmd


def _sync_archive_template(working_copy: str) -> None:
    """Sync UI changes from a working copy back to the archive cookiecutter template.

    For each file in the template:
    - Files with no Jinja2 variable references → copied back verbatim.
    - Files with ``{{ cookiecutter.X }}`` references → concrete values are
      substituted back to their placeholder form.
    - Files containing Jinja2 block tags (``{%``) → skipped with a warning;
      auto-merging conditional blocks is not safe.
    """
    from importlib import resources

    working_path = Path(working_copy).resolve()
    if not working_path.is_dir():
        raise click.ClickException(f"Path '{working_copy}' is not a directory.")

    sync_file = working_path / ".regis-sync.json"
    if not sync_file.exists():
        raise click.ClickException(
            f"No .regis-sync.json found in {working_path}.\n"
            "Only working copies bootstrapped with 'regis-cli bootstrap archive' are supported."
        )

    sync_meta = json.loads(sync_file.read_text(encoding="utf-8"))
    context: dict[str, str] = sync_meta.get("context", {})
    if not context:
        raise click.ClickException(".regis-sync.json is missing the 'context' key.")

    template_path = Path(
        str(
            resources.files("regis_cli")
            / "cookiecutters"
            / "archive"
            / "{{cookiecutter.project_slug}}"
        )
    )

    _SKIP_NAMES = {
        ".regis-sync.json",
        ".regis-post-install.md",
        "pnpm-lock.yaml",
        "package-lock.json",
    }
    _SKIP_DIRS = {"node_modules", ".next", "build", ".git"}
    _SKIP_DIR_PREFIXES = {"static/archive"}

    sorted_context = sorted(
        context.items(), key=lambda kv: len(str(kv[1])), reverse=True
    )

    updated: list[Path] = []
    skipped_complex: list[Path] = []
    missing: list[Path] = []

    for tmpl_file in sorted(template_path.rglob("*")):
        if not tmpl_file.is_file():
            continue

        rel = tmpl_file.relative_to(template_path)

        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if any(str(rel).startswith(prefix) for prefix in _SKIP_DIR_PREFIXES):
            continue
        if rel.name in _SKIP_NAMES:
            continue

        working_file = working_path / rel
        if not working_file.exists():
            missing.append(rel)
            continue

        try:
            tmpl_content = tmpl_file.read_text(encoding="utf-8")
            working_content = working_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary file — skip

        if "{%" in tmpl_content:
            skipped_complex.append(rel)
            continue

        if "{{cookiecutter." in tmpl_content.replace(" ", ""):
            new_content = working_content
            for key, value in sorted_context:
                if value and isinstance(value, str):
                    new_content = new_content.replace(
                        value, f"{{{{ cookiecutter.{key} }}}}"
                    )
        else:
            new_content = working_content

        if new_content != tmpl_content:
            tmpl_file.write_text(new_content, encoding="utf-8")
            updated.append(rel)

    click.echo(f"\nSync: {working_path} → template", err=True)
    if updated:
        click.echo(f"\n  Updated ({len(updated)}):", err=True)
        for f in sorted(updated):
            click.echo(f"    ✓ {f}", err=True)
    if skipped_complex:
        click.echo(
            f"\n  Skipped — Jinja2 block tags, manual sync required ({len(skipped_complex)}):",
            err=True,
        )
        for f in sorted(skipped_complex):
            click.echo(f"    ⚠ {f}", err=True)
    if missing:
        click.echo(f"\n  Not found in working copy ({len(missing)}):", err=True)
        for f in sorted(missing):
            click.echo(f"    - {f}", err=True)
    if not updated:
        click.echo("\n  No changes detected.", err=True)


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

    template_path = resources.files("regis_cli") / "cookiecutters" / "playbook"

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


@bootstrap.command(name="archive")
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json defaults.",
)
@click.option(
    "--platform",
    type=click.Choice(["github", "gitlab"], case_sensitive=False),
    default=None,
    help="Target platform. Skips the cookiecutter platform prompt.",
)
@click.option(
    "--dev",
    is_flag=True,
    help="After scaffolding, run pnpm install and start the local dev server.",
)
@click.option(
    "--port",
    default=3000,
    show_default=True,
    help="Port for the dev server (only with --dev).",
)
@click.option(
    "--repo",
    is_flag=True,
    help="After scaffolding, create a remote repository and enable Pages.",
)
@click.option(
    "--repo-name",
    default=None,
    help="Name of the remote repository (only with --repo).",
)
@click.option(
    "--public/--private",
    default=None,
    help="Repository visibility (only with --repo; default: public for GitHub, private for GitLab).",
)
@click.option(
    "--org",
    default=None,
    help="Organisation or group to create the repo in (only with --repo).",
)
@click.option(
    "--sync-from",
    "sync_from",
    default=None,
    metavar="PATH",
    help="Sync UI changes from a working copy back to the cookiecutter template.",
)
def bootstrap_archive(
    output_dir: str,
    no_input: bool,
    platform: str | None,
    dev: bool,
    port: int,
    repo: bool,
    repo_name: str | None,
    public: bool | None,
    org: str | None,
    sync_from: str | None,
) -> None:
    """Bootstrap a standalone archive viewer site for regis-cli reports.

    Use --dev to start a local dev server after scaffolding.
    Use --repo to create a remote repository and enable Pages.
    Use --sync-from PATH to sync UI changes back to the cookiecutter template.
    """
    if sync_from:
        _sync_archive_template(sync_from)
        return

    if dev and repo:
        raise click.UsageError("--dev and --repo are mutually exclusive.")

    try:
        from importlib import resources

        from cookiecutter.main import cookiecutter
    except ImportError as exc:
        raise click.ClickException(
            f"cookiecutter not found or failed to import: {exc}. Please install it with 'pip install cookiecutter'."
        ) from None

    if repo:
        click.echo("Checking required tools...", err=True)
        require_tool("pnpm")
        require_tool("git")
        click.echo("  ✓ pnpm and git found.", err=True)

    if platform:
        extra_context: dict[str, str] | None = {"platform": platform}
    elif dev:
        extra_context = {"platform": "github"}
    else:
        extra_context = None

    template_path = resources.files("regis_cli") / "cookiecutters" / "archive"
    click.echo(f"\nScaffolding archive site into {output_dir}...", err=True)
    try:
        project_dir = cookiecutter(
            str(template_path),
            no_input=no_input,
            output_dir=output_dir,
            extra_context=extra_context,
        )
    except Exception as exc:
        raise click.ClickException(f"Failed to bootstrap archive site: {exc}") from exc

    project_path = Path(project_dir)
    click.echo(f"  ✓ Site scaffolded at {project_path}.", err=True)

    notes_file = project_path / ".regis-post-install.md"
    if notes_file.exists():
        click.echo("\n" + "=" * 40, err=True)
        click.echo("POST-INSTALL NOTES:", err=True)
        click.echo("=" * 40, err=True)
        click.echo(notes_file.read_text(encoding="utf-8"), err=True)
        click.echo("=" * 40 + "\n", err=True)
        notes_file.unlink()

    if dev:
        require_tool("pnpm")
        click.echo("\nInstalling Node dependencies (pnpm install)...", err=True)
        run_cmd(["pnpm", "install"], cwd=project_path, step_label="pnpm install")
        click.echo("  ✓ Dependencies installed.", err=True)
        click.echo(f"\nStarting dev server on http://localhost:{port} ...", err=True)
        click.echo(
            f"  Add reports: regis-cli analyze <IMAGE> --archive {project_path}/static/archive",
            err=True,
        )
        try:
            subprocess.run(  # nosec B603 B607
                ["pnpm", "dev", "--port", str(port)],
                cwd=str(project_path),
                check=False,
            )
        except FileNotFoundError as err:
            raise click.ClickException(
                "'pnpm' not found in PATH. Is it installed?"
            ) from err
        return

    if not repo:
        return

    if (project_path / ".github").is_dir():
        detected_platform, tool = "github", "gh"
    elif (project_path / ".gitlab-ci.yml").is_file():
        detected_platform, tool = "gitlab", "glab"
    else:
        raise click.ClickException("Cannot detect platform from scaffolded files.")

    click.echo(f"  ✓ Platform detected: {detected_platform}.", err=True)
    require_tool(tool)
    click.echo(f"\nChecking {tool} authentication...", err=True)
    run_cmd([tool, "auth", "status"], step_label=f"{tool} auth check")
    click.echo(f"  ✓ {tool} authenticated.", err=True)

    click.echo("\nInstalling Node dependencies (pnpm install)...", err=True)
    run_cmd(["pnpm", "install"], cwd=project_path, step_label="pnpm install")
    click.echo("  ✓ Dependencies installed.", err=True)

    click.echo("\nInitialising local git repository...", err=True)
    run_cmd(["git", "init", "-b", "main"], cwd=project_path)
    run_cmd(["git", "add", "."], cwd=project_path)
    run_cmd(
        ["git", "commit", "-m", "chore(report): initial archive site scaffold"],
        cwd=project_path,
    )
    click.echo("  ✓ Initial commit created.", err=True)

    effective_repo_name = repo_name or project_path.name

    click.echo(f"\nCreating remote repository '{effective_repo_name}'...", err=True)
    if detected_platform == "github":
        is_public = public if public is not None else True
        visibility = "--public" if is_public else "--private"
        target = f"{org}/{effective_repo_name}" if org else effective_repo_name
        run_cmd(
            [
                "gh",
                "repo",
                "create",
                target,
                visibility,
                "--source",
                str(project_path),
                "--remote",
                "origin",
                "--push",
            ],
            step_label="gh repo create",
        )
        click.echo(
            f"  ✓ Repository created and pushed to github.com/{target}.", err=True
        )
    else:
        is_public = public if public is not None else False
        glab_args = [
            "glab",
            "repo",
            "create",
            effective_repo_name,
            "--public" if is_public else "--private",
            "--defaultBranch=main",
        ]
        if org:
            glab_args.append(f"--group={org}")
        create_result = run_cmd(glab_args, check=False, step_label="glab repo create")
        if create_result.returncode != 0:
            view_result = run_cmd(
                ["glab", "repo", "view", effective_repo_name],
                check=False,
                step_label="glab repo view",
            )
            if view_result.returncode == 0:
                click.echo(
                    f"  ⚠ Repository '{effective_repo_name}' already exists, skipping creation.",
                    err=True,
                )
            else:
                detail = (create_result.stderr or create_result.stdout).strip()
                raise click.ClickException(
                    f"Step 'glab repo create' failed (exit {create_result.returncode}):\n{detail}"
                )
        else:
            click.echo(f"  ✓ Repository '{effective_repo_name}' created.", err=True)

        namespace = org
        if not namespace:
            click.echo("  Resolving GitLab username...", err=True)
            user_json = run_cmd(
                ["glab", "api", "/user"], step_label="glab api user"
            ).stdout
            namespace = json.loads(user_json)["username"]

        remote_url = f"https://gitlab.com/{namespace}/{effective_repo_name}.git"
        click.echo(f"  Adding remote origin: {remote_url}", err=True)
        run_cmd(["git", "remote", "add", "origin", remote_url], cwd=project_path)
        click.echo("  Pushing to origin/main...", err=True)
        run_cmd(["git", "push", "-u", "origin", "main"], cwd=project_path)
        click.echo("  ✓ Code pushed.", err=True)

    if detected_platform == "github":
        click.echo("\nEnabling GitHub Pages...", err=True)
        owner = org
        if not owner:
            owner = run_cmd(
                ["gh", "api", "user", "--jq", ".login"],
                step_label="gh api user",
            ).stdout.strip()
        run_cmd(
            [
                "gh",
                "api",
                "-X",
                "POST",
                f"repos/{owner}/{effective_repo_name}/pages",
                "--field",
                "build_type=workflow",
            ],
            step_label="enable GitHub Pages",
        )
        click.echo("  ✓ GitHub Pages enabled (workflow mode).", err=True)
        pages_url = f"https://{owner}.github.io/{effective_repo_name}/"
    else:
        pages_url = f"https://{namespace}.gitlab.io/{effective_repo_name}/"

    click.echo("\n✓ Done.", err=True)
    click.echo(f"\n  Pages URL (after first pipeline): {pages_url}")
    click.echo(
        f"  Add reports: regis-cli analyze <IMAGE> --archive {project_path}/static/archive"
    )
