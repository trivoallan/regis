"""Every analyzer schema must declare the identical optional `source` block."""

import json
from importlib.resources import files

ANALYZERS = [
    "cve", "dockle", "endoflife", "freshness", "hadolint", "oci",
    "popularity", "provenance", "sbom", "scorecarddev", "secrets",
    "size", "versioning",
]

SOURCE_BLOCK = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "fetched_at": {"type": "string", "format": "date-time"},
        "built_at": {"type": "string", "format": "date-time"},
        "version": {"type": "string"},
        "checksum": {"type": "string"},
    },
}


def _schema(name: str) -> dict:
    text = (
        files("regis")
        .joinpath(f"schemas/analyzer/{name}.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def test_every_analyzer_schema_declares_source():
    for name in ANALYZERS:
        schema = _schema(name)
        assert "source" in schema["properties"], f"{name} missing source"


def test_source_block_is_identical_everywhere():
    for name in ANALYZERS:
        schema = _schema(name)
        assert schema["properties"]["source"] == SOURCE_BLOCK, (
            f"{name} source block differs from canonical shape"
        )
