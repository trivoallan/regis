"""Tests for 'regis-cli rules list' command."""

import json
from pathlib import Path

from click.testing import CliRunner

from regis_cli.cli import main


class TestCliRulesList:
    """Test 'rules list' command behavior."""

    def test_rules_list_text(self):
        """Test default text output."""
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list"])
        assert result.exit_code == 0
        assert "trusted-domain" in result.output
        assert "critical" in result.output
        assert "Image must originate from a trusted domain." in result.output

    def test_rules_list_markdown(self):
        """Test markdown output."""
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list", "--format", "markdown"])
        assert result.exit_code == 0
        assert (
            "| Provider | Slug | Title | Level | Tags | Parameters |" in result.output
        )
        assert (
            "| core | `trusted-domain` | Image must originate from a trusted domain. | critical | security | `domains=['docker.io', 'registry-1.docker.io', 'quay.io', 'ghcr.io']` |"
            in result.output
        )

    def test_rules_list_output_file(self):
        """Test writing to a file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "rules.md"
            result = runner.invoke(
                main, ["rules", "list", "--format", "markdown", "--output", output_file]
            )
            assert result.exit_code == 0
            assert f"Rules list written to {output_file}" in result.output

            content = Path(output_file).read_text(encoding="utf-8")
            assert "| Provider |" in content
            assert "| `trusted-domain` |" in content
