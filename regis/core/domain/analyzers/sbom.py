"""SBOM analyzer — generates a CycloneDX Software Bill of Materials using Syft."""

from __future__ import annotations

import logging
from typing import Any

from regis.core.domain.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext

logger = logging.getLogger(__name__)

# Known copyleft SPDX license identifiers.
# Strong copyleft: GPL, AGPL — require releasing all derivative source code.
# Weak copyleft: LGPL, MPL, EPL, CDDL, EUPL — apply only to the licensed component.
# SSPL: server-side variant of AGPL; covers services that use the software.
COPYLEFT_LICENSES: frozenset[str] = frozenset(
    {
        # Strong copyleft — GPL
        "GPL-2.0",
        "GPL-2.0-only",
        "GPL-2.0-or-later",
        "GPL-3.0",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        # Strong copyleft — Affero (network / SaaS)
        "AGPL-1.0",
        "AGPL-3.0",
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        # Weak copyleft — LGPL
        "LGPL-2.0",
        "LGPL-2.0-only",
        "LGPL-2.0-or-later",
        "LGPL-2.1",
        "LGPL-2.1-only",
        "LGPL-2.1-or-later",
        "LGPL-3.0",
        "LGPL-3.0-only",
        "LGPL-3.0-or-later",
        # Weak copyleft — Mozilla / Eclipse / CDDL / EUPL
        "MPL-2.0",
        "MPL-2.0-no-copyleft-exception",
        "EPL-1.0",
        "EPL-2.0",
        "CDDL-1.0",
        "EUPL-1.1",
        "EUPL-1.2",
        # Strong copyleft — Server Side Public License
        "SSPL-1.0",
    }
)


def _syft_version(data: dict[str, Any]) -> str:
    """Best-effort extraction of the syft version from CycloneDX metadata.tools."""
    tools = data.get("metadata", {}).get("tools", {})
    # CycloneDX 1.5+: metadata.tools.components[]; older: metadata.tools[] (array).
    candidates = (
        tools.get("components", []) if isinstance(tools, dict) else (tools or [])
    )
    for tool in candidates:
        if (
            isinstance(tool, dict)
            and tool.get("name") == "syft"
            and tool.get("version")
        ):
            return str(tool["version"])
    return "unknown"


def _extract_licenses(component: dict[str, Any]) -> list[str]:
    """Extract license identifiers from a CycloneDX component."""
    licenses_list: list[str] = []
    for lic_entry in component.get("licenses", []):
        # CycloneDX can use either a license id or a license name.
        lic = lic_entry.get("license", lic_entry)
        lid = lic.get("id") or lic.get("name")
        if lid:
            licenses_list.append(lid)
    return licenses_list


class SbomAnalyzer(BaseAnalyzer):
    """Generate a Software Bill of Materials using Syft (CycloneDX)."""

    name = "sbom"
    schema_file = "analyzer/sbom.schema.json"

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "has-sbom",
                "description": "Image must provide a Software Bill of Materials.",
                "level": "warning",
                "tags": ["compliance"],
                "condition": {"==": [{"var": "results.sbom.has_sbom"}, True]},
                "messages": {
                    "pass": "SBOM is available for this image.",  # nosec B105
                    "fail": "No SBOM could be generated or found for this image.",
                },
            },
            {
                "slug": "license-blocklist",
                "description": (
                    "Image must not include components with licenses from the "
                    "configured blocklist."
                ),
                "level": "critical",
                "tags": ["compliance", "licensing"],
                "params": {"blocklist": []},
                "condition": {
                    "!": [
                        {
                            "intersects": [
                                {"var": "results.sbom.licenses"},
                                {"var": "criterion.params.blocklist"},
                            ]
                        }
                    ]
                },
                "messages": {
                    "pass": "No blocked licenses detected across ${results.sbom.total_components} components.",  # nosec B105
                    "fail": "Blocked license(s) detected: ${results.sbom.copyleft_licenses}",
                },
            },
        ]

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:
        data = ctx.tools.generate_sbom(ctx.image)
        repository = ctx.image.repository
        tag = ctx.image.tag

        # Parse CycloneDX structure.
        raw_components = data.get("components", [])

        # Count by type.
        component_types: dict[str, int] = {}
        all_licenses: set[str] = set()
        components: list[dict[str, Any]] = []

        for comp in raw_components:
            ctype = comp.get("type", "unknown")
            component_types[ctype] = component_types.get(ctype, 0) + 1

            comp_licenses = _extract_licenses(comp)
            all_licenses.update(comp_licenses)

            components.append(
                {
                    "name": comp.get("name", ""),
                    "version": comp.get("version"),
                    "type": ctype,
                    "purl": comp.get("purl"),
                    "licenses": comp_licenses,
                }
            )

        return {
            "analyzer": self.name,
            "scanner_version": _syft_version(data),
            "repository": repository,
            "tag": tag,
            "has_sbom": len(raw_components) > 0,
            "sbom_format": data.get("bomFormat", "CycloneDX"),
            "sbom_version": data.get("specVersion", "unknown"),
            "total_components": len(raw_components),
            "component_types": component_types,
            "total_dependencies": len(data.get("dependencies", [])),
            "licenses": sorted(all_licenses),
            "copyleft_licenses": sorted(all_licenses & COPYLEFT_LICENSES),
            "components": components,
        }
