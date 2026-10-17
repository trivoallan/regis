"""Provenance analyzer — checks for SLSA provenance and build attestations."""

from __future__ import annotations

import logging
from typing import Any

from regis.core.domain import signatures as sigs
from regis.core.domain.analyzers.base import BaseAnalyzer
from regis.core.domain.context import AnalysisContext
from regis.core.domain.errors import RegistryError
from regis.core.model.image_reference import ImageReference

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

    def analyze(self, ctx: AnalysisContext) -> dict[str, Any]:
        repository = ctx.image.repository
        tag = ctx.image.tag
        labels: dict[str, str] = {}

        # Fetch manifest and config to extract labels (any platform carries them).
        try:
            manifest = ctx.inspector.get_manifest(tag)
            media_type = manifest.get("mediaType", "")

            if "list" in media_type or "index" in media_type:
                entries = manifest.get("manifests", [])
                if entries:
                    manifest = ctx.inspector.get_manifest(entries[0].get("digest"))
                else:
                    manifest = {}

            config_digest = manifest.get("config", {}).get("digest")
            if config_digest:
                config = ctx.inspector.get_blob(config_digest)
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

        signatures, verified_signers, gaps = self._signatures(ctx)
        for sig in signatures:
            provenance_indicators.append(
                {
                    "type": "cosign-signature",
                    "key": sig["format"],
                    "value": sig["location"],
                }
            )

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
            "has_cosign_signature": bool(signatures),
            "signatures": signatures,
            "verified_signers": verified_signers,
            # None (read as missing data) makes signed-by incomplete, not failed.
            "signatures_complete": True if not gaps else None,
            "signature_gaps": gaps,
            "source_tracked": source_tracked,
            "indicators_count": len(provenance_indicators),
            "indicators": provenance_indicators,
        }

    @staticmethod
    def _signatures(
        ctx: AnalysisContext,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
        """Find and verify the signatures on the digest the reference resolves to.

        The subject is the reference as given (the index for a multi-arch image),
        never a platform child or a config digest: cosign signs what it was named.
        """
        image = ctx.image
        try:
            subject = (
                image.tag
                if image.tag.startswith("sha256:")
                else ctx.inspector.get_digest(image.tag)
            )
        except RegistryError as exc:
            return [], [], [f"subject digest lookup failed: {exc}"]
        if not subject:
            return [], [], ["registry returned no digest for the reference"]

        candidates, gaps = sigs.discover(ctx.inspector, subject)
        target = ImageReference(
            registry=image.registry, repository=image.repository, tag=subject
        )
        signatures, signers, verify_gaps = sigs.verify(
            candidates,
            lambda identity, issuer: ctx.tools.verify_signature(
                target, identity=identity, issuer=issuer
            ),
        )
        return signatures, signers, gaps + verify_gaps

    @classmethod
    def default_criteria(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "signed-by",
                "description": "Image must carry a verified signature by a listed signer.",
                "level": "critical",
                "enable": False,
                "tags": ["supply-chain", "signature"],
                "params": {"signers": []},
                "condition": {
                    "if": [
                        {
                            "intersects": [
                                {"var": "results.provenance.verified_signers"},
                                {"var": "criterion.params.signers"},
                            ]
                        },
                        True,
                        # Reached only when no listed signer matched: a lookup or
                        # verification gap (None) makes the rule incomplete.
                        {
                            "and": [
                                {"var": "results.provenance.signatures_complete"},
                                False,
                            ]
                        },
                    ]
                },
                "messages": {
                    "pass": "Image is signed by an accepted signer.",
                    "fail": "No verified signature by an accepted signer (found: ${results.provenance.verified_signers}).",
                },
            }
        ]
