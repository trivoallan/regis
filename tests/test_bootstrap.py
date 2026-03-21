"""Tests for the regis-cli bootstrap command."""

from pathlib import Path

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
