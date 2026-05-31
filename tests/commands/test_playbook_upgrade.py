"""Tests for `regis playbook upgrade`."""

from __future__ import annotations

from click.testing import CliRunner

from regis.cli import main


def test_upgrade_injects_missing_fields_preserving_comments(tmp_path) -> None:
    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(
        """# Important business context for this playbook
name: LegacyPlaybook
# Tiers come from compliance team
tiers:
  - name: Gold
    condition: { ">": [{ var: rules_summary.score }, 90] }
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["playbook", "upgrade", str(playbook)])
    assert result.exit_code == 0, result.output

    text = playbook.read_text(encoding="utf-8")
    assert "schemaVersion: 1" in text
    assert 'version: "1.0.0"' in text or "version: '1.0.0'" in text
    # Comments preserved:
    assert "# Important business context" in text
    assert "# Tiers come from compliance team" in text
    # Existing content preserved:
    assert "name: LegacyPlaybook" in text


def test_upgrade_noop_when_fields_present(tmp_path) -> None:
    original = 'schemaVersion: 1\nversion: "2.0.0"\nname: AlreadyUpgraded\n'
    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["playbook", "upgrade", str(playbook)])
    assert result.exit_code == 0, result.output
    # Version not bumped, file unchanged
    assert playbook.read_text(encoding="utf-8") == original


def test_upgrade_adds_only_missing_field(tmp_path) -> None:
    """If schemaVersion is present but version is not, only version is injected."""
    playbook = tmp_path / "playbook.yaml"
    playbook.write_text(
        "schemaVersion: 1\nname: PartialUpgrade\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["playbook", "upgrade", str(playbook)])
    assert result.exit_code == 0, result.output

    text = playbook.read_text(encoding="utf-8")
    assert "schemaVersion: 1" in text
    assert 'version: "1.0.0"' in text or "version: '1.0.0'" in text
    assert "name: PartialUpgrade" in text


def test_upgrade_validates_after_writing(tmp_path) -> None:
    """After upgrade, the file should pass `regis playbook validate`."""
    playbook = tmp_path / "playbook.yaml"
    playbook.write_text("name: NeedsUpgrade\n", encoding="utf-8")

    runner = CliRunner()
    upgrade_result = runner.invoke(main, ["playbook", "upgrade", str(playbook)])
    assert upgrade_result.exit_code == 0

    validate_result = runner.invoke(main, ["playbook", "validate", str(playbook)])
    assert validate_result.exit_code == 0, validate_result.output
    assert "schemaVersion=1" in validate_result.output
