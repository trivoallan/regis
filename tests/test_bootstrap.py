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

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_github_happy_path(self, mock_run, _mock_which):
        mock_run.side_effect = _make_subprocess_mock("myuser\n").side_effect
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
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

    @patch("regis_cli.cli.shutil.which", return_value=None)
    def test_missing_pnpm_fails(self, _mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive", "--repo", "--no-input"])
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
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
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
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
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
                main, ["bootstrap", "archive", "test-repo", "--repo", "--no-input"]
            )
        assert result.exit_code == 0, result.output
        assert any("regis-archive" in arg for arg in gh_create_args)

    @patch("regis_cli.cli.shutil.which", return_value="/usr/bin/fake")
    @patch("regis_cli.cli.subprocess.run")
    def test_sync_from_option_in_help(self, mock_run, _mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive", "--help"])
        assert "--sync-from" in result.output

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


class TestBootstrapArchiveSyncFrom:
    """Tests for `bootstrap archive --sync-from`."""

    _SYNC_META = {
        "template": "archive",
        "context": {
            "project_name": "My Test Archive",
            "project_slug": "my-test-archive",
            "description": "A test archive site.",
            "version": "0.19.0",
            "platform": "github",
        },
    }

    def _make_working_copy(self, tmp_path: Path, sync_meta: dict | None = None) -> Path:
        """Create a minimal working copy with .regis-sync.json."""
        import json

        wc = tmp_path / "my-test-archive"
        wc.mkdir()
        meta = sync_meta or self._SYNC_META
        (wc / ".regis-sync.json").write_text(json.dumps(meta), encoding="utf-8")
        return wc

    def test_missing_working_copy_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            main, ["bootstrap", "archive", "--sync-from", "/nonexistent/path"]
        )
        assert result.exit_code != 0

    def test_missing_sync_json_errors(self, tmp_path):
        wc = tmp_path / "no-sync"
        wc.mkdir()
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "archive", "--sync-from", str(wc)])
        assert result.exit_code != 0
        assert ".regis-sync.json" in result.output

    def test_sync_json_written_at_bootstrap(self, tmp_path):
        """Bootstrapping an archive site produces a .regis-sync.json in the project."""
        import json

        runner = CliRunner()
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = runner.invoke(
            main, ["bootstrap", "archive", str(out_dir), "--no-input"]
        )
        assert result.exit_code == 0, result.output

        project_dir = out_dir / "regis-archive"
        sync_file = project_dir / ".regis-sync.json"
        assert sync_file.exists()

        meta = json.loads(sync_file.read_text(encoding="utf-8"))
        assert meta["template"] == "archive"
        assert meta["context"]["project_name"] == "RegiS Archive"
        assert meta["context"]["project_slug"] == "regis-archive"
        assert "platform" in meta["context"]

    def test_sync_succeeds_on_fresh_working_copy(self, tmp_path):
        """Syncing a fresh working copy exits cleanly with no error."""
        runner = CliRunner()
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = runner.invoke(
            main, ["bootstrap", "archive", str(out_dir), "--no-input"]
        )
        assert result.exit_code == 0, result.output

        project_dir = out_dir / "regis-archive"

        result = runner.invoke(
            main, ["bootstrap", "archive", "--sync-from", str(project_dir)]
        )
        assert result.exit_code == 0, result.output
        # No crash, and the sync report was emitted
        assert "Sync:" in result.output

    def test_changed_file_is_synced_back(self, tmp_path):
        """Modifying a file in the working copy syncs the change back to the template."""
        import json
        from importlib import resources

        runner = CliRunner()
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = runner.invoke(
            main, ["bootstrap", "archive", str(out_dir), "--no-input"]
        )
        assert result.exit_code == 0, result.output
        project_dir = out_dir / "regis-archive"

        # Modify a plain file (no cookiecutter vars) in the working copy
        custom_css = project_dir / "src" / "css" / "custom.css"
        original = custom_css.read_text(encoding="utf-8")
        custom_css.write_text(original + "\n/* my custom style */\n", encoding="utf-8")

        result = runner.invoke(
            main, ["bootstrap", "archive", "--sync-from", str(project_dir)]
        )
        assert result.exit_code == 0, result.output
        assert "Updated" in result.output
        assert "src/css/custom.css" in result.output

        # The template file should now contain the new style
        template_css = Path(
            str(
                resources.files("regis_cli")
                / "cookiecutters"
                / "archive"
                / "{{cookiecutter.project_slug}}"
                / "src"
                / "css"
                / "custom.css"
            )
        )
        assert "/* my custom style */" in template_css.read_text(encoding="utf-8")

        # Restore the template file to avoid polluting other test runs
        template_css.write_text(original, encoding="utf-8")

    def test_variable_placeholders_restored(self, tmp_path):
        """Cookiecutter variables are re-inserted when syncing docusaurus.config.ts."""
        import json
        from importlib import resources

        runner = CliRunner()
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = runner.invoke(
            main, ["bootstrap", "archive", str(out_dir), "--no-input"]
        )
        assert result.exit_code == 0, result.output
        project_dir = out_dir / "regis-archive"

        # Append a comment to docusaurus.config.ts in the working copy
        config = project_dir / "docusaurus.config.ts"
        original_wc = config.read_text(encoding="utf-8")
        config.write_text(original_wc + "\n// end of config\n", encoding="utf-8")

        template_config = Path(
            str(
                resources.files("regis_cli")
                / "cookiecutters"
                / "archive"
                / "{{cookiecutter.project_slug}}"
                / "docusaurus.config.ts"
            )
        )
        original_tmpl = template_config.read_text(encoding="utf-8")

        result = runner.invoke(
            main, ["bootstrap", "archive", "--sync-from", str(project_dir)]
        )
        assert result.exit_code == 0, result.output
        assert "docusaurus.config.ts" in result.output

        new_tmpl = template_config.read_text(encoding="utf-8")
        # Concrete value replaced by placeholder
        assert "{{ cookiecutter.project_name }}" in new_tmpl
        assert "RegiS Archive" not in new_tmpl

        # Restore
        template_config.write_text(original_tmpl, encoding="utf-8")
