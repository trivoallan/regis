"""SBOM analyzer — generates a CycloneDX Software Bill of Materials using Trivy."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from typing import Any

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

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


def _run_trivy_sbom(
    image: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Run ``trivy image --format cyclonedx`` and return parsed CycloneDX JSON."""
    trivy_path = shutil.which("trivy")
    if not trivy_path:
        raise AnalyzerError("trivy executable not found in PATH")

    # Forward registry credentials to Trivy when available.
    env = os.environ.copy()

    # Priority: passed credentials > environment variables
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")

    if user and pwd:
        env["TRIVY_USERNAME"] = user
        env["TRIVY_PASSWORD"] = pwd

    cmd = [
        trivy_path,
        "image",
        "--format",
        "cyclonedx",
        "--quiet",
        "--no-progress",
    ]
    if platform:
        cmd.extend(["--platform", platform])

    cmd.append(image)

    logger.debug("Running trivy SBOM: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return json.loads(result.stdout)  # type: ignore[no-any-return]
    except subprocess.CalledProcessError as exc:
        raise AnalyzerError(f"trivy sbom failed: {exc.stderr}") from exc
    except json.JSONDecodeError as exc:
        raise AnalyzerError(f"trivy produced invalid JSON: {exc}") from exc


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
    """Generate a Software Bill of Materials using Trivy (CycloneDX)."""

    name = "sbom"
    schema_file = "analyzer/sbom.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
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
                                {"var": "rule.params.blocklist"},
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

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        # Build full image reference — same logic as TrivyAnalyzer.
        if client.registry in ("docker.io", "registry-1.docker.io"):
            full_image = f"{repository}:{tag}"
        else:
            full_image = f"{client.registry}/{repository}:{tag}"

        data = _run_trivy_sbom(
            full_image,
            username=client.username,
            password=client.password,
            platform=platform,
        )

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
