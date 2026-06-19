"""Typed view over regis/adapters/driven/tools/manifest.yaml."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Mapping

import jsonschema
import yaml

MANIFEST_RESOURCE = "manifest.yaml"
SCHEMA_RESOURCE = "tools-manifest.schema.json"


@dataclass(frozen=True)
class CosignPolicy:
    issuer: str
    identity_regex: str


@dataclass(frozen=True)
class Tool:
    name: str
    version: str
    url_template: str
    archive: str  # "none" | "tar.gz" | "zip"
    sha256: Mapping[str, str]  # arch -> hex
    member: str | None = None
    arch_alt: Mapping[str, str] = field(default_factory=dict)
    cosign: CosignPolicy | None = None

    def url(self, arch: str) -> str:
        arch_alt = self.arch_alt.get(arch, arch)
        return (
            self.url_template.replace("{version}", self.version)
            .replace("{arch_alt}", arch_alt)
            .replace("{arch}", arch)
        )

    def sha_for(self, arch: str) -> str:
        try:
            return self.sha256[arch]
        except KeyError as exc:
            raise KeyError(f"no sha256 pinned for {self.name}/{arch}") from exc


def _load_schema() -> dict:
    schema_path = files("regis.schemas").joinpath(SCHEMA_RESOURCE)
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_manifest(path: Path | None = None) -> dict[str, Tool]:
    """Load and validate the tools manifest. Returns name -> Tool."""
    if path is None:
        resource = files("regis.adapters.driven.tools").joinpath(MANIFEST_RESOURCE)
        raw = resource.read_text(encoding="utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")
    doc = yaml.safe_load(raw)
    jsonschema.validate(doc, _load_schema())

    tools: dict[str, Tool] = {}
    for name, body in doc["tools"].items():
        cosign_block = body.get("cosign")
        cosign = (
            CosignPolicy(
                issuer=cosign_block["issuer"],
                identity_regex=cosign_block["identity_regex"],
            )
            if cosign_block
            else None
        )
        tools[name] = Tool(
            name=name,
            version=body["version"],
            url_template=body["url_template"],
            archive=body["archive"],
            sha256=dict(body["sha256"]),
            member=body.get("member"),
            arch_alt=dict(body.get("arch_alt") or {}),
            cosign=cosign,
        )
    return tools
