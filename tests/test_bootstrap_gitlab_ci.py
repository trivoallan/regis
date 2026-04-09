"""Tests for regis bootstrap gitlab-ci command."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from regis.cli import main


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "gitlab-ci", "--help"])
    assert result.exit_code == 0
    assert "gitlab" in result.output.lower()
    assert "--no-input" in result.output


def test_no_input_generates_files():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["bootstrap", "gitlab-ci", ".", "--no-input"])
        assert result.exit_code == 0, result.output

        project_dir = Path("my-regis-pipeline")
        assert project_dir.exists()
        assert (project_dir / ".gitlab-ci.yml").exists()
        assert (project_dir / "playbook.yaml").exists()
        assert (project_dir / "CI-VARIABLES.md").exists()
        # Post-install notes should be displayed and deleted
        assert not (project_dir / ".regis-post-install.md").exists()


def test_generated_gitlab_ci_is_valid_yaml():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["bootstrap", "gitlab-ci", ".", "--no-input"])
        assert result.exit_code == 0, result.output

        ci_file = Path("my-regis-pipeline/.gitlab-ci.yml")
        data = yaml.safe_load(ci_file.read_text(encoding="utf-8"))
        assert "stages" in data
        assert "request_analysis" in data
        assert "analyze_image" in data
        assert "push_results" in data


def test_generated_playbook_has_gitlab_integration():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["bootstrap", "gitlab-ci", ".", "--no-input"])
        assert result.exit_code == 0, result.output

        pb_file = Path("my-regis-pipeline/playbook.yaml")
        data = yaml.safe_load(pb_file.read_text(encoding="utf-8"))
        assert "integrations" in data
        assert "gitlab" in data["integrations"]
        assert "badges" in data["integrations"]["gitlab"]
        assert "checklists" in data["integrations"]["gitlab"]


def test_generated_ci_variables_lists_required_vars():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["bootstrap", "gitlab-ci", ".", "--no-input"])
        assert result.exit_code == 0, result.output

        content = Path("my-regis-pipeline/CI-VARIABLES.md").read_text(encoding="utf-8")
        assert "GITLAB_TOKEN" in content
        assert "IMAGE_URL" in content


def test_post_install_notes_displayed():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["bootstrap", "gitlab-ci", ".", "--no-input"])
        assert result.exit_code == 0, result.output
        assert "POST-INSTALL NOTES" in result.output or "Next Steps" in result.output
