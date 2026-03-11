# trunk-ignore-all(bandit/B101)
"""Tests for the regis-cli bootstrap command."""

from pathlib import Path

from click.testing import CliRunner

from regis_cli.cli import main


def test_bootstrap_help():
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "--help"])
    assert result.exit_code == 0
    assert "repository" in result.output
    assert "playbook" in result.output


def test_bootstrap_repository_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # We need to mock the template path or ensure it's accessible during tests
        # For simplicity in this test, we'll assume the command can find the template
        result = runner.invoke(
            main, ["bootstrap", "repository", "test-output", "--no-input"]
        )

        assert result.exit_code == 0
        # Cookiecutter creates the directory based on project_slug in cookiecutter.json
        # Default project_name is "RegiS Image Security" -> project_slug "regis-image-security"
        project_dir = Path("test-output/regis-image-security")
        assert project_dir.exists()
        assert (project_dir / "README.md").exists()


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
