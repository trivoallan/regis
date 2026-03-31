"""Provenance analyzer — checks for SLSA provenance and build attestations."""

from __future__ import annotations

import logging
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.registry.client import RegistryClient

logger = logging.getLogger(__name__)

# OCI artifact types for known attestation formats.
_ATTESTATION_TYPES = {
    "application/vnd.in-toto+json": "in-toto",
    "application/vnd.dev.cosign.simplesigning.v1+json": "cosign",
    "application/vnd.dsse.envelope.v1+json": "dsse",
}


class ProvenanceAnalyzer(BaseAnalyzer):
    """Check for build provenance and supply-chain attestations."""

    name = "provenance"
    schema_file = "analyzer/provenance.schema.json"

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        labels: dict[str, str] = {}
        image_digest: str | None = None

        # Fetch manifest and config to extract labels and digest.
        try:
            manifest = client.get_manifest(tag)
            media_type = manifest.get("mediaType", "")

            if "list" in media_type or "index" in media_type:
                entries = manifest.get("manifests", [])
                if entries:
                    image_digest = entries[0].get("digest")
                    manifest = client.get_manifest(image_digest)
                else:
                    manifest = {}

            config_digest = manifest.get("config", {}).get("digest")
            if not image_digest:
                image_digest = config_digest

            if config_digest:
                config = client.get_blob(config_digest)
                labels = config.get("config", {}).get("Labels") or {}
        except Exception:
            logger.debug("Could not fetch manifest for provenance", exc_info=True)

        # Check for well-known provenance labels.
        provenance_indicators: list[dict[str, str]] = []

        # OCI annotations for build source.
        oci_source = labels.get("org.opencontainers.image.source")
        if oci_source:
            provenance_indicators.append(
                {
                    "type": "oci-annotation",
                    "key": "org.opencontainers.image.source",
                    "value": oci_source,
                }
            )

        oci_revision = labels.get("org.opencontainers.image.revision")
        if oci_revision:
            provenance_indicators.append(
                {
                    "type": "oci-annotation",
                    "key": "org.opencontainers.image.revision",
                    "value": oci_revision,
                }
            )

        oci_created = labels.get("org.opencontainers.image.created")
        if oci_created:
            provenance_indicators.append(
                {
                    "type": "oci-annotation",
                    "key": "org.opencontainers.image.created",
                    "value": oci_created,
                }
            )

        oci_vendor = labels.get("org.opencontainers.image.vendor")
        if oci_vendor:
            provenance_indicators.append(
                {
                    "type": "oci-annotation",
                    "key": "org.opencontainers.image.vendor",
                    "value": oci_vendor,
                }
            )

        # Check for Docker BuildKit build info.
        buildkit_src = labels.get("org.mobyproject.buildkit.source.ref")
        if buildkit_src:
            provenance_indicators.append(
                {
                    "type": "buildkit",
                    "key": "org.mobyproject.buildkit.source.ref",
                    "value": buildkit_src,
                }
            )

        # Try to detect cosign signatures by fetching the tag with cosign suffix.
        has_cosign_signature = False
        if image_digest:
            cosign_tag = image_digest.replace(":", "-") + ".sig"
            try:
                sig_manifest = client.get_manifest(cosign_tag)
                if sig_manifest.get("layers") or sig_manifest.get("manifests"):
                    has_cosign_signature = True
                    provenance_indicators.append(
                        {
                            "type": "cosign-signature",
                            "key": "signature-tag",
                            "value": cosign_tag,
                        }
                    )
            except Exception:
                pass  # No cosign signature found.

        # Determine has_provenance and score.
        has_provenance = len(provenance_indicators) > 0
        source_tracked = any(
            i["key"]
            in ("org.opencontainers.image.source", "org.opencontainers.image.revision")
            for i in provenance_indicators
        )

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "has_provenance": has_provenance,
            "has_cosign_signature": has_cosign_signature,
            "source_tracked": source_tracked,
            "indicators_count": len(provenance_indicators),
            "indicators": provenance_indicators,
        }
