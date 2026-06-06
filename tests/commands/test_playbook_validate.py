"""Tests for `regis playbook validate` (issue #589)."""

from __future__ import annotations

import textwrap
from pathlib import Path

from click.testing import CliRunner

from regis.cli import main

# Minimal valid envelope fixture (reused across tests).
_VALID_ENVELOPE = (
    "apiVersion: regis.io/v1alpha1\n"
    "kind: Playbook\n"
    "metadata:\n"
    "  name: minimal\n"
    "  labels:\n"
    '    app.kubernetes.io/version: "1.0.0"\n'
    "spec: {}\n"
)


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
        # Envelope without metadata.name — schema requires it.
        bad.write_text(
            "apiVersion: regis.io/v1alpha1\n"
            "kind: Playbook\n"
            "metadata:\n"
            "  labels:\n"
            '    app.kubernetes.io/version: "1.0.0"\n'
            "spec: {}\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(bad)])
        assert result.exit_code == 1
        assert "'name' is a required property" in result.output

    def test_validate_additional_property_rejected(self, tmp_path: Path):
        bad = tmp_path / "extra.yaml"
        # Extra property at the envelope root — additionalProperties: false.
        bad.write_text(
            textwrap.dedent("""
                apiVersion: regis.io/v1alpha1
                kind: Playbook
                metadata:
                  name: with-extras
                  labels:
                    app.kubernetes.io/version: "1.0.0"
                spec: {}
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
        ok.write_text(_VALID_ENVELOPE, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(ok)])
        assert result.exit_code == 0
        assert "is valid" in result.output

    def test_validate_reports_api_version_and_version(self, tmp_path: Path):
        playbook = tmp_path / "playbook.yaml"
        playbook.write_text(
            "apiVersion: regis.io/v1alpha1\n"
            "kind: Playbook\n"
            "metadata:\n"
            "  name: apiversiontest\n"
            "  labels:\n"
            '    app.kubernetes.io/version: "1.2.3"\n'
            "spec: {}\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(playbook)])
        assert result.exit_code == 0, result.output
        assert "apiVersion=regis.io/v1alpha1" in result.output
        assert "kind=Playbook" in result.output
        assert "version=1.2.3" in result.output

    def test_validate_fails_on_missing_api_version(self, tmp_path: Path):
        playbook = tmp_path / "playbook.yaml"
        playbook.write_text(
            "kind: Playbook\n"
            "metadata:\n"
            "  name: no-api-version\n"
            "  labels:\n"
            '    app.kubernetes.io/version: "1.0.0"\n'
            "spec: {}\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["playbook", "validate", str(playbook)])
        assert result.exit_code == 1
        assert "apiVersion" in result.output


def test_validate_prints_api_version(tmp_path) -> None:
    from click.testing import CliRunner

    from regis.commands.playbook import playbook_group

    pb = tmp_path / "playbook.yaml"
    pb.write_text(
        "apiVersion: regis.io/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\n  labels:\n"
        '    app.kubernetes.io/version: "1.0.0"\n'
        "spec: {}\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(playbook_group, ["validate", str(pb)])
    assert result.exit_code == 0
    assert "regis.io/v1alpha1" in result.output
    assert "Playbook" in result.output
