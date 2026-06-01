"""Tests du schéma Playbook v1alpha1 (enveloppe Kubernetes)."""

from __future__ import annotations

import importlib.resources
import json

import jsonschema
import pytest
from referencing import Registry, Resource


def _load_schema() -> dict:
    pkg = importlib.resources.files("regis.schemas.playbook.v1alpha1")
    return json.loads(pkg.joinpath("playbook.schema.json").read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load_schema()
    pb_root = importlib.resources.files("regis.schemas.playbook")
    jsonlogic = json.loads(
        pb_root.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
    )
    registry = Registry().with_resources(
        [
            (schema["$id"], Resource.from_contents(schema)),
            ("../jsonlogic.schema.json", Resource.from_contents(jsonlogic)),
        ]
    )
    return jsonschema.Draft202012Validator(schema, registry=registry)


VALID = {
    "apiVersion": "regis.trivoallan.dev/v1alpha1",
    "kind": "Playbook",
    "metadata": {
        "name": "default",
        "title": "RegiS Default Playbook",
        "labels": {"app.kubernetes.io/version": "1.0.0"},
    },
    "spec": {
        "rules": [
            {"provider": "cve", "rule": "cve-count", "slug": "x", "level": "info"}
        ]
    },
}


def test_valid_envelope_passes() -> None:
    _validator().validate(VALID)


def test_missing_kind_fails() -> None:
    doc = {k: v for k, v in VALID.items() if k != "kind"}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_bad_metadata_name_fails() -> None:
    doc = {**VALID, "metadata": {**VALID["metadata"], "name": "Invalid Name"}}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_missing_version_label_fails() -> None:
    doc = {**VALID, "metadata": {**VALID["metadata"], "labels": {}}}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_non_semver_version_label_fails() -> None:
    doc = {
        **VALID,
        "metadata": {
            **VALID["metadata"],
            "labels": {"app.kubernetes.io/version": "1.2"},
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_additional_property_in_spec_fails() -> None:
    doc = {**VALID, "spec": {**VALID["spec"], "pages": []}}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)
