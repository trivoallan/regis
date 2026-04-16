"""bootstrap command group (playbook and archive subcommands)."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
from pathlib import Path

import click

from regis.utils.process import require_tool, run_cmd


def _run_initial_analyze(project_path: Path) -> None:
    """Run a first regis analysis on the regis image itself.

    The image URL is read from the generated .regis-sync.json context so it
    always matches the scaffolded version.  Failures are non-blocking: a
    warning is printed and the bootstrap continues normally.
    """
    sync_file = project_path / ".regis-sync.json"
    if not sync_file.exists():
        click.echo(
            "  ⚠ .regis-sync.json not found — skipping initial analysis.",
            err=True,
        )
        return

    context = json.loads(sync_file.read_text(encoding="utf-8")).get("context", {})
    image_url: str = context.get("regis_image_url", "")
    if not image_url:
        click.echo(
            "  ⚠ regis_image_url not set in context — skipping initial analysis.",
            err=True,
        )
        return

    archive_dir = project_path / "static" / "archive"
    click.echo(f"\nRunning initial analysis: {image_url} ...", err=True)
    try:
        result = subprocess.run(  # nosec B603 B607
            ["regis", "analyze", image_url, "--archive", str(archive_dir)],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            click.echo(
                "  ⚠ Initial analysis finished with errors (non-blocking).",
                err=True,
            )
        else:
            click.echo("  ✓ Initial analysis complete.", err=True)
    except FileNotFoundError:
        click.echo(
            "  ⚠ 'regis' not found in PATH — skipping initial analysis.",
            err=True,
        )


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
) -> None:
    """Bootstrap a standalone archive dashboard site for regis reports.

    Use --dev to start a local dev server after scaffolding.
    Use --repo to create a remote repository and enable Pages.
    """

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

    # When --repo-name is provided, use it as the project directory name so the
    # scaffolded slug matches the remote repository name without requiring an
    # extra interactive prompt.
    if repo_name:
        extra_context = extra_context or {}
        extra_context.setdefault("project_slug", repo_name)

    # Automatically skip prompts when stdin has no TTY (Docker without -it,
    # CI pipelines, etc.).  Explicit --no-input always takes precedence.
    effective_no_input = no_input or not sys.stdin.isatty()

    template_path = resources.files("regis") / "cookiecutters" / "archive"
    click.echo(f"\nScaffolding archive site into {output_dir}...", err=True)
    try:
        project_dir = cookiecutter(
            str(template_path),
            no_input=effective_no_input,
            output_dir=output_dir,
            extra_context=extra_context,
        )
    except Exception as exc:
        detail = str(exc) or repr(exc)
        raise click.ClickException(
            f"Failed to bootstrap archive site: {detail}"
        ) from exc

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
        _run_initial_analyze(project_path)
        click.echo(f"\nStarting dev server on http://localhost:{port} ...", err=True)
        click.echo(
            f"  Add reports: regis analyze <IMAGE> --archive {project_path}/static/archive",
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

    _run_initial_analyze(project_path)

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
        f"  Add reports: regis analyze <IMAGE> --archive {project_path}/static/archive"
    )
