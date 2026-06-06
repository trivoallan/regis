"""Schema validation for the spec.presentation section."""

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA = json.loads(
    Path("regis/schemas/playbook/v1alpha1/playbook.schema.json").read_text()
)


def _doc(spec_extra: dict) -> dict:
    return {
        "apiVersion": "regis.io/v1alpha1",
        "kind": "Playbook",
        "metadata": {"name": "p", "labels": {"app.kubernetes.io/version": "1.0.0"}},
        "spec": {"rules": [], **spec_extra},
    }


def test_presentation_section_validates():
    doc = _doc(
        {
            "presentation": {
                "badges": ["score"],
                "checklists": [{"title": "T", "items": [{"label": "do X"}]}],
                "templates": [{"url": "gh:org/tmpl"}],
            }
        }
    )
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)


def test_integrations_section_is_rejected():
    doc = _doc({"integrations": {"gitlab": {"badges": ["score"]}}})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(SCHEMA).validate(doc)
