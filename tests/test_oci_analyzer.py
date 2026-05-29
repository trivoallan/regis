"""Tests for the oci analyzer (formerly skopeo)."""

from __future__ import annotations

import json
from importlib import resources

import jsonschema


def test_oci_schema_is_valid_draft7():
    schema_text = (
        resources.files("regis.schemas").joinpath("analyzer/oci.schema.json").read_text()
    )
    schema = json.loads(schema_text)
    jsonschema.Draft7Validator.check_schema(schema)
    assert schema["properties"]["analyzer"]["const"] == "oci"
