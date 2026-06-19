"""Tests for the regis bootstrap command."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from regis.adapters.driving.cli.cli import main


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


def test_bootstrap_help():
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "--help"])
    assert result.exit_code == 0
    assert "playbook" in result.output
    assert "gitlab-ci" not in result.output
    assert "tools" in result.output
    assert "archive" not in result.output


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
