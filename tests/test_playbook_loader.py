"""Tests for playbook bundle directory support in the loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from regis.playbook.engine import bundle_meta_schema_path, is_bundle, load_playbook
from regis.playbook.loader import PlaybookVersionError

MINIMAL_PLAYBOOK = {
    "schemaVersion": 1,
    "version": "1.0.0",
    "name": "Bundle Playbook",
    "sections": [
        {
            "name": "Main",
            "scorecards": [
                {
                    "name": "always-pass",
                    "description": "Always passes",
                    "condition": {"==": [1, 1]},
                }
            ],
        }
    ],
}


class TestIsBundle:
    """Test the is_bundle() helper."""

    def test_directory_is_bundle(self, tmp_path):
        assert is_bundle(tmp_path) is True

    def test_file_is_not_bundle(self, tmp_path):
        f = tmp_path / "playbook.yaml"
        f.write_text(yaml.dump(MINIMAL_PLAYBOOK))
        assert is_bundle(f) is False

    def test_string_path_to_directory_is_bundle(self, tmp_path):
        assert is_bundle(str(tmp_path)) is True

    def test_string_path_to_file_is_not_bundle(self, tmp_path):
        f = tmp_path / "playbook.yaml"
        f.write_text(yaml.dump(MINIMAL_PLAYBOOK))
        assert is_bundle(str(f)) is False

    def test_url_is_not_bundle(self):
        assert is_bundle("https://example.com/playbook.yaml") is False

    def test_nonexistent_path_is_not_bundle(self, tmp_path):
        assert is_bundle(tmp_path / "does_not_exist") is False


class TestBundleMetaSchemaPath:
    """Test the bundle_meta_schema_path() helper."""

    def test_returns_path_when_schema_exists(self, tmp_path):
        schema_file = tmp_path / "meta.schema.json"
        schema_file.write_text(json.dumps({"type": "object"}))
        result = bundle_meta_schema_path(tmp_path)
        assert result == schema_file
        assert isinstance(result, Path)

    def test_returns_none_when_schema_absent(self, tmp_path):
        result = bundle_meta_schema_path(tmp_path)
        assert result is None

    def test_accepts_string_path(self, tmp_path):
        schema_file = tmp_path / "meta.schema.json"
        schema_file.write_text(json.dumps({"type": "object"}))
        result = bundle_meta_schema_path(str(tmp_path))
        assert result == schema_file

    def test_returns_none_for_string_path_without_schema(self, tmp_path):
        result = bundle_meta_schema_path(str(tmp_path))
        assert result is None


class TestLoadPlaybookBundle:
    """Test that load_playbook() accepts bundle directories."""

    def test_load_from_bundle_directory(self, tmp_path):
        bundle_dir = tmp_path / "my-bundle"
        bundle_dir.mkdir()
        playbook_file = bundle_dir / "playbook.yaml"
        playbook_file.write_text(yaml.dump(MINIMAL_PLAYBOOK))

        loaded = load_playbook(bundle_dir)
        assert loaded["name"] == "Bundle Playbook"
        assert len(loaded["sections"][0]["scorecards"]) == 1

    def test_load_from_bundle_directory_string_path(self, tmp_path):
        bundle_dir = tmp_path / "my-bundle"
        bundle_dir.mkdir()
        (bundle_dir / "playbook.yaml").write_text(yaml.dump(MINIMAL_PLAYBOOK))

        loaded = load_playbook(str(bundle_dir))
        assert loaded["name"] == "Bundle Playbook"

    def test_bundle_with_meta_schema_loads_rules(self, tmp_path):
        """Extra files in the bundle (e.g. meta.schema.json) don't affect loading."""
        bundle_dir = tmp_path / "my-bundle"
        bundle_dir.mkdir()
        (bundle_dir / "playbook.yaml").write_text(yaml.dump(MINIMAL_PLAYBOOK))
        (bundle_dir / "meta.schema.json").write_text(json.dumps({"type": "object"}))
        (bundle_dir / "README.md").write_text("# My Bundle")

        loaded = load_playbook(bundle_dir)
        assert loaded["name"] == "Bundle Playbook"

    def test_bundle_missing_playbook_yaml_raises(self, tmp_path):
        bundle_dir = tmp_path / "empty-bundle"
        bundle_dir.mkdir()

        with pytest.raises((FileNotFoundError, OSError)):
            load_playbook(bundle_dir)

    def test_legacy_yaml_file_still_works(self, tmp_path):
        """Plain .yaml files continue to work as before."""
        f = tmp_path / "playbook.yaml"
        f.write_text(yaml.dump(MINIMAL_PLAYBOOK))
        loaded = load_playbook(f)
        assert loaded["name"] == "Bundle Playbook"

    def test_legacy_json_file_still_works(self, tmp_path):
        """Plain .json files continue to work as before."""
        f = tmp_path / "playbook.json"
        f.write_text(json.dumps(MINIMAL_PLAYBOOK))
        loaded = load_playbook(f)
        assert loaded["name"] == "Bundle Playbook"


def _write(tmp_path, content: str) -> str:
    path = tmp_path / "playbook.yaml"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_loads_valid_v1_playbook(tmp_path) -> None:
    content = (
        "schemaVersion: 1\n"
        'version: "1.0.0"\n'
        "name: Valid Playbook\n"
    )
    pb = load_playbook(_write(tmp_path, content))
    assert pb["schemaVersion"] == 1
    assert pb["version"] == "1.0.0"
    assert pb["name"] == "Valid Playbook"


def test_missing_schema_version_raises(tmp_path) -> None:
    content = 'version: "1.0.0"\nname: No Schema Version\n'
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    msg = str(exc.value)
    assert "schemaVersion" in msg
    assert "Add `schemaVersion: 1`" in msg
    assert "[1]" in msg


def test_schema_version_not_integer_raises(tmp_path) -> None:
    content = (
        'schemaVersion: "1"\n'
        'version: "1.0.0"\n'
        "name: String Schema Version\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "must be an integer" in str(exc.value)


def test_schema_version_boolean_raises(tmp_path) -> None:
    content = (
        "schemaVersion: true\n"
        'version: "1.0.0"\n'
        "name: Boolean Schema Version\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "must be an integer" in str(exc.value)


def test_unknown_schema_version_raises(tmp_path) -> None:
    content = (
        "schemaVersion: 99\n"
        'version: "1.0.0"\n'
        "name: Future Playbook\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    msg = str(exc.value)
    assert "schemaVersion=99" in msg
    assert "[1]" in msg


def test_missing_version_field_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = "schemaVersion: 1\nname: No Version\n"
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))


def test_invalid_semver_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = (
        "schemaVersion: 1\n"
        'version: "1.2"\n'
        "name: Invalid SemVer\n"
    )
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))
