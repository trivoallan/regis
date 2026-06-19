from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from regis.adapters.driven.tools.manifest import Tool, load_manifest

SCHEMA_PATH = Path("regis/schemas/tools-manifest.schema.json")


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_loads_and_is_draft_2020_12(schema: dict) -> None:
    assert schema["$schema"].endswith("/2020-12/schema")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_minimal_valid_manifest(schema: dict) -> None:
    doc = {
        "schema_version": 1,
        "tools": {
            "grype": {
                "version": "0.112.0",
                "url_template": "https://example.com/{version}/{arch}",
                "archive": "tar.gz",
                "member": "grype",
                "sha256": {"amd64": "a" * 64, "arm64": "b" * 64},
            }
        },
    }
    jsonschema.validate(doc, schema)


def test_rejects_short_sha256(schema: dict) -> None:
    doc = {
        "schema_version": 1,
        "tools": {
            "grype": {
                "version": "0.1.0",
                "url_template": "https://x/{version}",
                "archive": "none",
                "sha256": {"amd64": "abc", "arm64": "b" * 64},
            }
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)


def test_rejects_unknown_archive_type(schema: dict) -> None:
    doc = {
        "schema_version": 1,
        "tools": {
            "x": {
                "version": "0.1.0",
                "url_template": "u",
                "archive": "rar",
                "sha256": {"amd64": "a" * 64, "arm64": "b" * 64},
            }
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)


def test_load_manifest_returns_typed_tools() -> None:
    tools = load_manifest()
    assert "grype" in tools
    grype = tools["grype"]
    assert isinstance(grype, Tool)
    assert grype.version
    assert grype.sha256["amd64"] and grype.sha256["arm64"]


def test_tool_resolves_url_for_arch() -> None:
    tools = load_manifest()
    url = tools["dockle"].url(arch="amd64")
    assert url.endswith("Linux-64bit.tar.gz")
    assert "/v" + tools["dockle"].version + "/" in url


def test_tool_url_hadolint_arch_alt() -> None:
    tools = load_manifest()
    url = tools["hadolint"].url(arch="arm64")
    assert url.endswith("hadolint-Linux-arm64")


def test_load_manifest_raises_on_unknown_path(tmp_path) -> None:
    bad = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_manifest(path=bad)
