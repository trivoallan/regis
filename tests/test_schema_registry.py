"""Tests for the playbook schema registry."""

from __future__ import annotations

import pytest

from regis.playbook import schema_registry


def test_supported_versions_lists_v1() -> None:
    assert schema_registry.supported_versions() == [1]


def test_get_schema_v1_returns_dict_with_expected_id() -> None:
    schema = schema_registry.get_schema(1)
    assert isinstance(schema, dict)
    assert schema["$id"].endswith("/v1/definition.schema.json")
    assert schema["title"] == "playbook.definition"


def test_get_schema_unknown_version_raises_key_error() -> None:
    with pytest.raises(KeyError):
        schema_registry.get_schema(99)
