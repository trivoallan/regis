"""Find an image's cosign signatures and confirm who signed them.

Two layouts exist in the field (see openspec change ``signature-referrers``):

- legacy (cosign v2): tag ``sha256-<hex>.sig``, one layer per signature, the
  Fulcio certificate in the ``dev.sigstore.cosign/certificate`` annotation;
- referrers (cosign v3): a Sigstore bundle manifest whose ``subject`` is the
  image, reached through the Referrers API or the ``sha256-<hex>`` fallback tag.

A signature only *claims* a signer until cosign confirms it for that exact
identity and issuer, so a genuine bundle copied from another image is never
credited.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from cryptography import x509

from regis.core.domain.errors import RegistryError, ToolError
from regis.core.ports.image_inspector import ImageInspector

BUNDLE_MEDIA_PREFIX = "application/vnd.dev.sigstore.bundle"
LEGACY_CERT_ANNOTATION = "dev.sigstore.cosign/certificate"
# Fulcio OIDC issuer extensions: v2 is a DER UTF8String, v1 (deprecated) raw bytes.
_ISSUER_V2 = "1.3.6.1.4.1.57264.1.8"
_ISSUER_V1 = "1.3.6.1.4.1.57264.1.1"

Signer = tuple[str, str]  # (identity, issuer)


@dataclass(frozen=True)
class Candidate:
    """A discovered signature and the signer its certificate claims (if any)."""

    format: str  # "legacy-tag" | "sigstore-bundle"
    location: str
    claimed: Signer | None


def legacy_tag(digest: str) -> str:
    """Return the cosign v2 signature tag for *digest*."""
    return digest.replace(":", "-") + ".sig"


def _issuer(cert: x509.Certificate) -> str | None:
    for ext in cert.extensions:
        oid = ext.oid.dotted_string
        if oid not in (_ISSUER_V2, _ISSUER_V1):
            continue
        raw = ext.value.value  # UnrecognizedExtension
        if oid == _ISSUER_V2:
            # DER UTF8String: tag 0x0c, then a short or long-form length.
            offset = 2 + (raw[1] & 0x7F if raw[1] & 0x80 else 0)
            raw = raw[offset:]
        return str(raw.decode())
    return None


def certificate_signer(cert: x509.Certificate) -> Signer | None:
    """Return the (identity, issuer) a Fulcio certificate claims, or None."""
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    except x509.ExtensionNotFound:
        return None
    names = [str(name.value) for name in san.value]
    issuer = _issuer(cert)
    if not names or issuer is None:
        return None
    return names[0], issuer


def _bundle_signer(bundle: dict[str, Any]) -> Signer | None:
    material = bundle.get("verificationMaterial") or {}
    raw = (material.get("certificate") or {}).get("rawBytes")
    if raw is None:  # bundle v0.1/v0.2 carry a chain instead
        chain = (material.get("x509CertificateChain") or {}).get("certificates")
        raw = (chain or [{}])[0].get("rawBytes")
    if raw is None:
        return None
    try:
        cert = x509.load_der_x509_certificate(base64.b64decode(raw))
    except (ValueError, binascii.Error):
        return None
    return certificate_signer(cert)


def _legacy_signer(layer: dict[str, Any]) -> Signer | None:
    pem = (layer.get("annotations") or {}).get(LEGACY_CERT_ANNOTATION)
    if not pem:
        return None  # key-based signature: no identity to confirm
    try:
        cert = x509.load_pem_x509_certificate(pem.encode())
    except ValueError:
        return None
    return certificate_signer(cert)


def discover(
    inspector: ImageInspector, digest: str
) -> tuple[list[Candidate], list[str]]:
    """Return the signatures attached to *digest* and any lookup gaps."""
    candidates: list[Candidate] = []
    gaps: list[str] = []

    try:
        referrers = inspector.get_referrers(digest)
        for descriptor in referrers:
            ref = descriptor.get("digest", "")
            # The index descriptor's artifactType is unreliable (cosign v3 writes
            # vnd.oci.empty there): classify by the referrer manifest itself.
            manifest = inspector.get_manifest(ref)
            if not str(manifest.get("artifactType", "")).startswith(
                BUNDLE_MEDIA_PREFIX
            ):
                continue
            layers = manifest.get("layers") or [{}]
            bundle = inspector.get_blob(layers[0].get("digest", ""))
            candidates.append(Candidate("sigstore-bundle", ref, _bundle_signer(bundle)))
    except RegistryError as exc:
        gaps.append(f"referrers lookup failed: {exc}")

    tag = legacy_tag(digest)
    try:
        # ponytail: tag membership, not a manifest fetch, because the inspectors
        # don't tell a 404 from a failure; list_tags is cached per run. Very large
        # repositories pay one full tag listing.
        if tag in inspector.list_tags():
            for layer in inspector.get_manifest(tag).get("layers") or []:
                candidates.append(Candidate("legacy-tag", tag, _legacy_signer(layer)))
    except RegistryError as exc:
        gaps.append(f"legacy signature lookup failed: {exc}")

    return candidates, gaps


def verify(
    candidates: list[Candidate], confirm: Callable[[str, str], bool]
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    """Confirm each claimed signer once; return signatures, verified signers, gaps.

    *confirm(identity, issuer)* asks the verification tool whether the image
    carries a valid signature by exactly that signer.
    """
    outcome: dict[Signer, bool] = {}
    gaps: list[str] = []
    for claimed in {c.claimed for c in candidates if c.claimed}:
        try:
            outcome[claimed] = confirm(*claimed)
        except ToolError as exc:
            gaps.append(f"signature verification failed: {exc}")

    signatures: list[dict[str, Any]] = []
    signers: list[dict[str, str]] = []
    for c in candidates:
        verified = bool(c.claimed and outcome.get(c.claimed))
        entry: dict[str, Any] = {
            "format": c.format,
            "location": c.location,
            "verified": verified,
        }
        if verified and c.claimed:
            identity, issuer = c.claimed
            entry.update(identity=identity, issuer=issuer)
            signer = {"identity": identity, "issuer": issuer}
            if signer not in signers:
                signers.append(signer)
        signatures.append(entry)
    return signatures, signers, gaps
