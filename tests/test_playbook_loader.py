"""Tests for playbook bundle directory support in the loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from regis.playbook.engine import bundle_meta_schema_path, is_bundle, load_playbook
from regis.playbook.loader import PlaybookVersionError

MINIMAL_PLAYBOOK = {
    "apiVersion": "regis.trivoallan.dev/v1alpha1",
    "kind": "Playbook",
    "metadata": {
        "name": "bundle-playbook",
        "title": "Bundle Playbook",
        "labels": {"app.kubernetes.io/version": "1.0.0"},
    },
    "spec": {
        "rules": [
            {"provider": "cve", "rule": "cve-count", "slug": "always", "level": "info"}
        ]
    },
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
        assert loaded["slug"] == "bundle-playbook"
        assert loaded["version"] == "1.0.0"
        assert loaded["rules"][0]["slug"] == "always"

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


def test_loads_valid_envelope(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n"
        "  name: valid\n"
        "  title: Valid Playbook\n"
        "  labels:\n"
        '    app.kubernetes.io/version: "1.0.0"\n'
        "spec: {}\n"
    )
    pb = load_playbook(_write(tmp_path, content))
    assert pb["apiVersion"] == "regis.trivoallan.dev/v1alpha1"
    assert pb["kind"] == "Playbook"
    assert pb["name"] == "Valid Playbook"  # metadata.title
    assert pb["slug"] == "valid"  # metadata.name
    assert pb["version"] == "1.0.0"  # label


def test_name_falls_back_to_metadata_name_when_no_title(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n"
        "  name: no-title\n"
        "  labels:\n"
        '    app.kubernetes.io/version: "1.0.0"\n'
        "spec: {}\n"
    )
    pb = load_playbook(_write(tmp_path, content))
    assert pb["name"] == "no-title"


def test_missing_api_version_raises(tmp_path) -> None:
    content = "kind: Playbook\nmetadata:\n  name: x\nspec: {}\n"
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    msg = str(exc.value)
    assert "apiVersion" in msg
    assert "Add `apiVersion: regis.trivoallan.dev/v1alpha1`" in msg


def test_wrong_kind_raises(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: RuleSet\n"
        "metadata:\n  name: x\nspec: {}\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "expected 'Playbook'" in str(exc.value)


def test_unknown_api_version_raises(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v9\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\nspec: {}\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    msg = str(exc.value)
    assert "apiVersion=" in msg
    assert "regis playbook upgrade" in msg


def test_legacy_flat_format_rejected(tmp_path) -> None:
    content = 'schemaVersion: 1\nversion: "1.0.0"\nname: Legacy\n'
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "apiVersion" in str(exc.value)


def test_missing_version_label_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\n  labels: {}\n"
        "spec: {}\n"
    )
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))


def test_invalid_semver_label_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\n  labels:\n"
        '    app.kubernetes.io/version: "1.2"\n'
        "spec: {}\n"
    )
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))
