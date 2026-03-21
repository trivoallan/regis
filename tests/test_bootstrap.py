"""Tests for the regis-cli bootstrap command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from regis_cli.cli import main


def test_bootstrap_help():
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "--help"])
    assert result.exit_code == 0
    assert "playbook" in result.output
    assert "archive" in result.output


def test_bootstrap_playbook_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["bootstrap", "playbook", "test-pb", "--no-input"])

        if result.exit_code != 0:
            print(f"DEBUG: {result.output}")
        assert result.exit_code == 0
        # Default project_name is "Custom RegiS Playbook" -> project_slug "custom-regis-playbook"
        pb_dir = Path("test-pb/custom-regis-playbook")
        assert pb_dir.exists()
        assert (pb_dir / "playbook.yaml").exists()


def test_bootstrap_archive_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main, ["bootstrap", "archive", "test-archive", "--no-input"]
        )

        assert result.exit_code == 0
        # Default project_name is "RegiS Archive" -> project_slug "regis-archive"
        project_dir = Path("test-archive/regis-archive")
        assert project_dir.exists()
        assert (project_dir / "package.json").exists()
        assert (project_dir / "static" / "archive" / ".gitkeep").exists()

        # Verify post-install notes were shown and deleted
        assert "POST-INSTALL NOTES:" in result.output
        notes_file = project_dir / ".regis-post-install.md"
        assert not notes_file.exists()


def _make_subprocess_mock(stdout: str = "myuser\n") -> MagicMock:
    """Return a subprocess.run mock where every call succeeds."""

    def _side_effect(args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = stdout
        result.stderr = ""
        return result

    mock = MagicMock(side_effect=_side_effect)
    return mock


class TestBootstrapArchiveRepo:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive-repo", "--help"])
        assert result.exit_code == 0
        assert "--repo-name" in result.output
        assert "--public" in result.output
        assert "--org" in result.output

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_github_happy_path(self, mock_run, _mock_which):
        mock_run.side_effect = _make_subprocess_mock("myuser\n").side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["bootstrap", "archive-repo", "test-repo", "--no-input"]
            )
        assert result.exit_code == 0, result.output
        assert "github.io" in result.output

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_gitlab_happy_path(self, mock_run, _mock_which):
        mock_run.side_effect = _make_subprocess_mock(
            '{"username":"myuser"}\n'
        ).side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Simulate interactive prompts: accept defaults except "platform" → choose "gitlab"
            result = runner.invoke(
                main,
                ["bootstrap", "archive-repo", "test-repo"],
                input="\n\n2\n\n\n\n\n",
            )
        assert result.exit_code == 0, result.output
        assert "gitlab.io" in result.output

    @patch("regis_cli.cli.shutil.which", return_value=None)
    def test_missing_pnpm_fails(self, _mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive-repo", "--no-input"])
        assert result.exit_code != 0
        assert "pnpm" in result.output

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_auth_failure(self, mock_run, _mock_which):
        def _side_effect(args, **kwargs):
            result = MagicMock()
            if "auth" in args:
                result.returncode = 1
                result.stdout = ""
                result.stderr = "not logged in"
            else:
                result.returncode = 0
                result.stdout = ""
                result.stderr = ""
            return result

        mock_run.side_effect = _side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["bootstrap", "archive-repo", "test-repo", "--no-input"]
            )
        assert result.exit_code != 0
        assert "failed" in result.output.lower()

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_pnpm_install_failure(self, mock_run, _mock_which):
        def _side_effect(args, **kwargs):
            result = MagicMock()
            if args[0] == "pnpm":
                result.returncode = 1
                result.stdout = ""
                result.stderr = "install failed"
            else:
                result.returncode = 0
                result.stdout = ""
                result.stderr = ""
            return result

        mock_run.side_effect = _side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["bootstrap", "archive-repo", "test-repo", "--no-input"]
            )
        assert result.exit_code != 0
        assert "pnpm install" in result.output

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_repo_name_defaults_to_slug(self, mock_run, _mock_which):
        gh_create_args: list[str] = []

        def _side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = "myuser\n"
            result.stderr = ""
            if args[0] == "gh" and "create" in args:
                gh_create_args.extend(args)
            return result

        mock_run.side_effect = _side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["bootstrap", "archive-repo", "test-repo", "--no-input"]
            )
        assert result.exit_code == 0, result.output
        assert any("regis-archive" in arg for arg in gh_create_args)

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_org_passed_to_gh(self, mock_run, _mock_which):
        gh_create_args: list[str] = []

        def _side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = "myuser\n"
            result.stderr = ""
            if args[0] == "gh" and "create" in args:
                gh_create_args.extend(args)
            return result

        mock_run.side_effect = _side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "bootstrap",
                    "archive-repo",
                    "test-repo",
                    "--no-input",
                    "--org",
                    "myorg",
                ],
            )
        assert result.exit_code == 0, result.output
        assert any("myorg/regis-archive" in arg for arg in gh_create_args)
