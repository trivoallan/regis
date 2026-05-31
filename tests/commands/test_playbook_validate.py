"""Tests for `regis playbook validate` (issue #589)."""

from __future__ import annotations

import textwrap
from pathlib import Path

from click.testing import CliRunner

from regis.cli import main


class TestPlaybookValidate:
    def test_validate_built_in_default_bundle(self):
        runner = CliRunner()
        result = runner.invoke(
            main, ["playbook", "validate", "regis/playbooks/default"]
        )
        assert result.exit_code == 0
        assert "is valid" in result.output

    def test_validate_missing_required_name_field(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            'schemaVersion: 1\nversion: "1.0.0"\ndescription: missing-name\n',
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(bad)])
        assert result.exit_code == 1
        assert "'name' is a required property" in result.output

    def test_validate_additional_property_rejected(self, tmp_path: Path):
        bad = tmp_path / "extra.yaml"
        bad.write_text(
            textwrap.dedent("""
                schemaVersion: 1
                version: "1.0.0"
                name: with-extras
                foo: bar
                """).strip(),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(bad)])
        assert result.exit_code == 1
        assert "Additional properties" in result.output

    def test_validate_nonexistent_file(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["playbook", "validate", str(tmp_path / "ghost.yaml")]
        )
        # Click rejects the missing path before our callback runs
        assert result.exit_code != 0

    def test_validate_unparseable_yaml(self, tmp_path: Path):
        bad = tmp_path / "broken.yaml"
        bad.write_text(":\ninvalid:\n  - yaml: [unclosed", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(bad)])
        assert result.exit_code != 0
        assert "Failed to load playbook" in result.output

    def test_validate_minimal_valid_playbook(self, tmp_path: Path):
        ok = tmp_path / "min.yaml"
        ok.write_text(
            'schemaVersion: 1\nversion: "1.0.0"\nname: minimal\n', encoding="utf-8"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(ok)])
        assert result.exit_code == 0
        assert "is valid" in result.output
