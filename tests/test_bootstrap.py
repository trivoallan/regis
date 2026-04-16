"""Tests for the regis bootstrap command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from regis.cli import main
from regis.commands.bootstrap import _run_initial_analyze


class TestRunInitialAnalyze:
    """Tests for _run_initial_analyze helper."""

    def test_no_sync_file(self, tmp_path, capsys):
        _run_initial_analyze(tmp_path)
        assert "not found" in capsys.readouterr().err

    def test_empty_image_url(self, tmp_path, capsys):
        sync = tmp_path / ".regis-sync.json"
        sync.write_text(json.dumps({"context": {"regis_image_url": ""}}))
        _run_initial_analyze(tmp_path)
        assert "not set" in capsys.readouterr().err

    @patch("regis.commands.bootstrap.subprocess.run")
    def test_analysis_succeeds(self, mock_run, tmp_path, capsys):
        sync = tmp_path / ".regis-sync.json"
        sync.write_text(json.dumps({"context": {"regis_image_url": "alpine:latest"}}))
        mock_run.return_value = MagicMock(returncode=0)
        _run_initial_analyze(tmp_path)
        assert "complete" in capsys.readouterr().err

    @patch("regis.commands.bootstrap.subprocess.run")
    def test_analysis_fails_non_blocking(self, mock_run, tmp_path, capsys):
        sync = tmp_path / ".regis-sync.json"
        sync.write_text(json.dumps({"context": {"regis_image_url": "alpine:latest"}}))
        mock_run.return_value = MagicMock(returncode=1)
        _run_initial_analyze(tmp_path)
        assert "non-blocking" in capsys.readouterr().err.lower()

    @patch(
        "regis.commands.bootstrap.subprocess.run",
        side_effect=FileNotFoundError("regis"),
    )
    def test_regis_not_in_path(self, _mock_run, tmp_path, capsys):
        sync = tmp_path / ".regis-sync.json"
        sync.write_text(json.dumps({"context": {"regis_image_url": "alpine:latest"}}))
        _run_initial_analyze(tmp_path)
        assert "not found" in capsys.readouterr().err.lower()


class TestBootstrapPlaybookErrors:
    """Tests for playbook bootstrap error paths."""

    @patch(
        "cookiecutter.main.cookiecutter", side_effect=RuntimeError("template broken")
    )
    def test_cookiecutter_runtime_error(self, _mock_cc):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "playbook", "--no-input"])
        assert result.exit_code != 0
        assert "template broken" in result.output.lower()

    @patch("cookiecutter.main.cookiecutter", side_effect=RuntimeError("archive broken"))
    def test_archive_cookiecutter_runtime_error(self, _mock_cc):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive", "--no-input"])
        assert result.exit_code != 0
        assert "archive broken" in result.output.lower()


class TestBootstrapArchiveDev:
    """Tests for bootstrap archive --dev path."""

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
    @patch("regis.commands.bootstrap.subprocess.run")
    def test_dev_starts_server(self, mock_bootstrap_run, mock_process_run, _mock_which):
        mock_process_run.side_effect = _make_subprocess_mock().side_effect
        mock_bootstrap_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["bootstrap", "archive", ".", "--dev", "--no-input"],
            )
        assert result.exit_code == 0, result.output
        assert (
            "dev server" in result.output.lower()
            or "localhost" in result.output.lower()
        )


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


def test_bootstrap_archive_dev_and_repo_mutually_exclusive():
    runner = CliRunner()
    result = runner.invoke(
        main, ["bootstrap", "archive", "--dev", "--repo", "--no-input"]
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


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
        result = runner.invoke(main, ["bootstrap", "archive", "--help"])
        assert result.exit_code == 0
        assert "--repo-name" in result.output
        assert "--public" in result.output
        assert "--org" in result.output
        assert "--repo" in result.output

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
    def test_github_happy_path(self, mock_run, _mock_which):
        mock_run.side_effect = _make_subprocess_mock("myuser\n").side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
            )
        assert result.exit_code == 0, result.output
        assert "github.io" in result.output

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
    def test_gitlab_happy_path(self, mock_run, _mock_which):
        mock_run.side_effect = _make_subprocess_mock(
            '{"username":"myuser"}\n'
        ).side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "bootstrap",
                    "archive",
                    "test-repo",
                    "--repo",
                    "--platform",
                    "gitlab",
                    "--no-input",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "gitlab.io" in result.output

    @patch("regis.utils.process.shutil.which", return_value=None)
    def test_missing_pnpm_fails(self, _mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive", "--repo", "--no-input"])
        assert result.exit_code != 0
        assert "pnpm" in result.output

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
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
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
            )
        assert result.exit_code != 0
        assert "failed" in result.output.lower()

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
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
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
            )
        assert result.exit_code != 0
        assert "pnpm install" in result.output

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
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
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
            )
        assert result.exit_code == 0, result.output
        assert any("regis-archive" in arg for arg in gh_create_args)

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
    def test_gitlab_repo_already_exists(self, mock_run, _mock_which):
        call_count = 0

        def _side_effect(args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.returncode = 0
            result.stdout = '{"username":"myuser"}\n'
            result.stderr = ""
            # Fail the glab repo create, succeed on glab repo view
            if args[0] == "glab" and "create" in args:
                result.returncode = 1
                result.stdout = "already exists"
                result.stderr = "already exists"
            return result

        mock_run.side_effect = _side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "bootstrap",
                    "archive",
                    "test-repo",
                    "--repo",
                    "--platform",
                    "gitlab",
                    "--no-input",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "already exists" in result.output.lower()

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
    def test_gitlab_repo_create_fails(self, mock_run, _mock_which):
        def _side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = '{"username":"myuser"}\n'
            result.stderr = ""
            if args[0] == "glab" and "create" in args:
                result.returncode = 1
                result.stdout = ""
                result.stderr = "permission denied"
            elif args[0] == "glab" and "view" in args:
                result.returncode = 1
                result.stdout = ""
                result.stderr = "not found"
            return result

        mock_run.side_effect = _side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "bootstrap",
                    "archive",
                    "test-repo",
                    "--repo",
                    "--platform",
                    "gitlab",
                    "--no-input",
                ],
            )
        assert result.exit_code != 0
        assert "permission denied" in result.output.lower()

    @patch("regis.commands.bootstrap.sys.stdin.isatty", return_value=False)
    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
    def test_non_tty_skips_prompts(self, mock_run, _mock_which, _mock_isatty):
        """Without --no-input, non-TTY stdin should auto-enable no_input mode."""
        mock_run.side_effect = _make_subprocess_mock(
            '{"username":"myuser"}\n'
        ).side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "bootstrap",
                    "archive",
                    "test-repo",
                    "--repo",
                    "--platform",
                    "gitlab",
                    "--repo-name",
                    "my-archive",
                ],
            )
        assert result.exit_code == 0, result.output
        assert Path("test-repo/my-archive").exists()
        assert "gitlab.io" in result.output

    @patch("regis.utils.process.shutil.which", return_value="/usr/bin/fake")
    @patch("regis.utils.process.subprocess.run")
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
                    "archive",
                    "test-repo",
                    "--repo",
                    "--no-input",
                    "--org",
                    "myorg",
                ],
            )
        assert result.exit_code == 0, result.output
        assert any("myorg/regis-archive" in arg for arg in gh_create_args)
