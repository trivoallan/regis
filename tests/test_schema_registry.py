"""Tests du registre de schémas playbook (clé = apiVersion)."""

from __future__ import annotations

import pytest

from regis.playbook import schema_registry


def test_supported_versions_lists_v1alpha1() -> None:
    assert "regis.io/v1alpha1" in schema_registry.supported_versions()


def test_get_schema_returns_playbook_kind() -> None:
    schema = schema_registry.get_schema("regis.io/v1alpha1")
    assert schema["properties"]["kind"]["const"] == "Playbook"


def test_get_schema_unknown_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        schema_registry.get_schema("regis.io/v9")
