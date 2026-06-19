"""Tests for 'regis rules list' command."""

from pathlib import Path

from click.testing import CliRunner

from regis.adapters.driving.cli.cli import main


class TestCliRulesList:
    """Test 'rules list' command behavior."""

    def test_rules_list_text(self):
        """Test default text output."""
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list"])
        assert result.exit_code == 0
        assert "registry-domain-whitelist" in result.output
        assert "critical" in result.output
        assert (
            "Checks if requested image registry domain is in the domains list."
            in result.output
        )

    def test_rules_list_markdown(self):
        """Test markdown output."""
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list", "--format", "markdown"])
        assert result.exit_code == 0
        assert (
            "| Provider | Slug | Description | Level | Tags | Parameters |"
            in result.output
        )
        assert (
            "| core | `registry-domain-whitelist` | Checks if requested image registry domain is in the domains list. | critical | security | `domains=['docker.io', 'registry-1.docker.io', 'quay.io', 'ghcr.io']` |"
            in result.output
        )

    def test_rules_list_shows_full_catalogue_without_rules_file(self):
        """Discovery surfaces analyzer templates the default playbook omits."""
        result = CliRunner().invoke(main, ["rules", "list"])
        assert result.exit_code == 0
        # oci:max-size is a template the default playbook does NOT declare; the
        # catalogue must still list it.
        assert "max-size" in result.output
        assert "registry-domain-whitelist" in result.output

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
            assert "| `registry-domain-whitelist` |" in content

    def test_rules_list_markdown_output_dir(self):
        """Test multi-file markdown output."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            output_dir = "rules_doc"
            result = runner.invoke(
                main,
                [
                    "rules",
                    "list",
                    "--format",
                    "markdown",
                    "--output-dir",
                    output_dir,
                    "--index",
                ],
            )
            assert result.exit_code == 0
            assert f"rule files written to {output_dir}" in result.output
            assert f"Index file written to {output_dir}/index.md" in result.output

            out_path = Path(output_dir)
            assert (out_path / "index.md").exists()
            assert (out_path / "core" / "registry-domain-whitelist.md").exists()

            index_content = (out_path / "index.md").read_text(encoding="utf-8")
            assert "| Provider |" in index_content
            assert (
                "[`registry-domain-whitelist`](./core/registry-domain-whitelist.md)"
                in index_content
            )

            rule_content = (
                out_path / "core" / "registry-domain-whitelist.md"
            ).read_text(encoding="utf-8")
            assert "# registry-domain-whitelist" in rule_content
            assert (
                "Checks if requested image registry domain is in the domains list."
                in rule_content
            )
            assert "| core | Critical | security |" in rule_content
            assert "## Condition" in rule_content
            # The playbook example must use the `criterion:` vocabulary, not the
            # legacy `rule:` template key (renamed in #646).
            assert "## Playbook Example" in rule_content
            assert "criterion: registry-domain-whitelist" in rule_content
            assert "\n    rule:" not in rule_content


class TestCliRulesListFilters:
    """Filter options on 'rules list' (issue #586)."""

    def test_filter_level_critical_only(self):
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list", "--filter-level", "critical"])
        assert result.exit_code == 0
        # registry-domain-whitelist is critical → kept
        assert "registry-domain-whitelist" in result.output
        # No info/warning lines
        for line in result.output.splitlines():
            if line.strip().startswith("[x]") or line.strip().startswith("[ ]"):
                assert "info " not in line
                assert "warning " not in line

    def test_filter_level_no_match(self):
        """A level with no rule yields the empty-set message."""
        runner = CliRunner()
        # 'warning' may have zero rules in defaults — accept either empty or filtered output
        result = runner.invoke(
            main,
            [
                "rules",
                "list",
                "--filter-level",
                "info",
                "--filter-provider",
                "nonexistent-provider",
            ],
        )
        assert result.exit_code == 0
        assert "No rules found." in result.output

    def test_filter_provider_only(self):
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list", "--filter-provider", "core"])
        assert result.exit_code == 0
        assert "registry-domain-whitelist" in result.output

    def test_filter_provider_unknown_yields_empty(self):
        runner = CliRunner()
        result = runner.invoke(
            main, ["rules", "list", "--filter-provider", "no-such-provider"]
        )
        assert result.exit_code == 0
        assert "No rules found." in result.output

    def test_filter_level_invalid_choice(self):
        runner = CliRunner()
        result = runner.invoke(main, ["rules", "list", "--filter-level", "bogus"])
        assert result.exit_code != 0

    def test_filters_combined(self):
        """Both filters apply (AND)."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "rules",
                "list",
                "--filter-level",
                "critical",
                "--filter-provider",
                "core",
            ],
        )
        assert result.exit_code == 0
        assert "registry-domain-whitelist" in result.output
