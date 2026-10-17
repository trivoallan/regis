"""Signature discovery, verification and the signed-by criterion (spec image-signature).

Fixtures are real artifacts: the cosign v3 bundle that signs regis 0.42.0 on GHCR,
and the cosign v2 `.sig` manifest of ghcr.io/sigstore/cosign/cosign:v2.4.1.
"""

from __future__ import annotations

import base64
import datetime
import json
from pathlib import Path
from typing import Any

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID, ObjectIdentifier

from regis.core.domain import signatures as sigs
from regis.core.domain.analyzers.provenance import ProvenanceAnalyzer
from regis.core.domain.errors import RegistryError, ToolError
from regis.core.domain.rules.evaluator import evaluate_rules
from regis.core.model.image_reference import ImageReference
from tests.fakes import FakeImageInspector, FakeToolRunner, make_ctx

FIXTURES = Path(__file__).parent / "fixtures" / "signatures"
INDEX = "sha256:bf13fe50b59c76ff9e23369a5cb56fe4599e3120a1a604588a3abbf305514c6f"
AMD64 = "sha256:81b3a75b334f0000000000000000000000000000000000000000000000000000"
REFERRER = "sha256:ffabdc55de014e33363da425ee4c841cbd2cb2857d3315aad3748e174e1a1f92"
REGIS = (
    "https://github.com/trivoallan/regis/.github/workflows/release.yml@refs/heads/main",
    "https://token.actions.githubusercontent.com",
)
GOOGLE = (
    "keyless@projectsigstore.iam.gserviceaccount.com",
    "https://accounts.google.com",
)


def _load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text())


def _referrer_manifest() -> dict[str, Any]:
    return _load("regis-0.42.0-referrer.json")


def _bundle_digest() -> str:
    return _referrer_manifest()["layers"][0]["digest"]


def _v3_inspector(
    cls: type[FakeImageInspector] = FakeImageInspector, **extra: Any
) -> FakeImageInspector:
    """GHCR as observed: no .sig tag, one bundle referrer whose descriptor says empty."""
    return cls(
        digest=INDEX,
        referrers={
            INDEX: [
                {
                    "digest": REFERRER,
                    "artifactType": "application/vnd.oci.empty.v1+json",
                }
            ]
        },
        manifests={
            "0.42.0": {
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [{"digest": AMD64}],
            },
            REFERRER: _referrer_manifest(),
            **extra.pop("manifests", {}),
        },
        blobs={_bundle_digest(): _load("regis-0.42.0-bundle.json")},
        **extra,
    )


def _analyze(inspector: FakeImageInspector, verified: set[tuple[str, str]], **kw: Any):
    tools = FakeToolRunner(verify_signature=verified)
    ctx = make_ctx(
        inspector=inspector,
        tools=tools,
        registry="ghcr.io",
        repository="trivoallan/regis",
        tag=kw.get("tag", "0.42.0"),
    )
    result = ProvenanceAnalyzer().analyze(ctx)
    ProvenanceAnalyzer().validate(result)
    return result


class _RecordingInspector(FakeImageInspector):
    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.referrer_calls: list[str] = []

    def get_referrers(self, digest: str) -> list[dict[str, Any]]:
        self.referrer_calls.append(digest)
        return super().get_referrers(digest)


# --- Subject digest -------------------------------------------------------------


def test_multi_arch_subject_is_the_index_not_a_child() -> None:
    inspector = _RecordingInspector(
        digest=INDEX,
        manifests={
            "0.42.0": {
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [{"digest": AMD64}],
            }
        },
    )
    _analyze(inspector, set())
    assert inspector.referrer_calls == [INDEX]


def test_single_arch_subject_is_the_manifest_not_the_config() -> None:
    inspector = _RecordingInspector(
        digest="sha256:manifest",
        manifest={"mediaType": "manifest", "config": {"digest": "sha256:config"}},
    )
    _analyze(inspector, set())
    assert inspector.referrer_calls == ["sha256:manifest"]


def test_digest_reference_is_its_own_subject() -> None:
    inspector = _RecordingInspector(digest=None)
    _analyze(inspector, set(), tag=INDEX)
    assert inspector.referrer_calls == [INDEX]


def test_unresolvable_subject_is_a_gap() -> None:
    result = _analyze(FakeImageInspector(digest=None), set())
    assert result["signatures_complete"] is None
    assert result["signature_gaps"] == ["registry returned no digest for the reference"]


def test_subject_lookup_error_is_a_gap() -> None:
    class _Boom(FakeImageInspector):
        def get_digest(self, reference: str) -> str | None:
            raise RegistryError("HEAD 500")

    result = _analyze(_Boom(), set())
    assert result["signatures_complete"] is None
    assert "HEAD 500" in result["signature_gaps"][0]


# --- Discovery and verification -----------------------------------------------


def test_cosign_v3_bundle_on_ghcr_is_found_and_verified() -> None:
    result = _analyze(_v3_inspector(), {REGIS})
    assert result["has_cosign_signature"] is True
    assert result["signatures"] == [
        {
            "format": "sigstore-bundle",
            "location": REFERRER,
            "verified": True,
            "identity": REGIS[0],
            "issuer": REGIS[1],
        }
    ]
    assert result["verified_signers"] == [{"identity": REGIS[0], "issuer": REGIS[1]}]
    assert result["signatures_complete"] is True
    assert {
        "type": "cosign-signature",
        "key": "sigstore-bundle",
        "value": REFERRER,
    } in (result["indicators"])


def test_bundle_signed_for_another_digest_is_not_verified() -> None:
    # cosign rejects the claimed signer: the bundle exists but signs something else.
    result = _analyze(_v3_inspector(), set())
    assert result["has_cosign_signature"] is True
    assert result["signatures"] == [
        {"format": "sigstore-bundle", "location": REFERRER, "verified": False}
    ]
    assert result["verified_signers"] == []


def test_legacy_v2_signature_is_found() -> None:
    legacy = _load("cosign-v2.4.1-legacy-sig.json")
    tag = sigs.legacy_tag(INDEX)
    inspector = FakeImageInspector(digest=INDEX, tags=[tag], manifests={tag: legacy})
    result = _analyze(inspector, {GOOGLE})
    # One key-based layer (no certificate) and one keyless layer.
    assert [s["format"] for s in result["signatures"]] == ["legacy-tag", "legacy-tag"]
    assert [s["verified"] for s in result["signatures"]] == [False, True]
    assert result["signatures"][1]["location"] == tag
    assert result["verified_signers"] == [{"identity": GOOGLE[0], "issuer": GOOGLE[1]}]


def test_both_layouts_after_a_re_sign_are_reported() -> None:
    tag = sigs.legacy_tag(INDEX)
    inspector = _v3_inspector(
        tags=[tag], manifests={tag: _load("cosign-v2.4.1-legacy-sig.json")}
    )
    result = _analyze(inspector, {REGIS, GOOGLE})
    formats = [s["format"] for s in result["signatures"]]
    assert formats == ["sigstore-bundle", "legacy-tag", "legacy-tag"]
    assert len(result["verified_signers"]) == 2


def test_non_signature_referrers_are_not_signatures() -> None:
    inspector = FakeImageInspector(
        digest=INDEX,
        referrers={INDEX: [{"digest": "sha256:sbom"}, {"digest": "sha256:att"}]},
        manifests={
            "sha256:sbom": {"artifactType": "application/spdx+json"},
            "sha256:att": {"artifactType": "application/vnd.in-toto+json"},
        },
    )
    result = _analyze(inspector, set())
    assert result["has_cosign_signature"] is False
    assert result["signatures"] == []


def test_unsigned_image() -> None:
    result = _analyze(FakeImageInspector(digest=INDEX), set())
    assert result["has_cosign_signature"] is False
    assert result["signatures_complete"] is True
    assert result["signature_gaps"] == []


def test_legacy_lookup_error_is_a_gap() -> None:
    class _NoTags(FakeImageInspector):
        def list_tags(self) -> list[str]:
            raise RegistryError("tags 503")

    result = _analyze(_NoTags(digest=INDEX), set())
    assert result["signatures_complete"] is None
    assert "tags 503" in result["signature_gaps"][0]


def test_verification_that_cannot_run_is_a_gap() -> None:
    class _Offline(FakeToolRunner):
        def verify_signature(self, image, *, identity, issuer):
            raise ToolError("getting trusted root: dial tcp: timeout")

    ctx = make_ctx(inspector=_v3_inspector(), tools=_Offline(), tag="0.42.0")
    result = ProvenanceAnalyzer().analyze(ctx)
    assert result["signatures"][0]["verified"] is False
    assert result["signatures_complete"] is None
    assert "trusted root" in result["signature_gaps"][0]


def test_verification_targets_the_subject_digest() -> None:
    seen: list[ImageReference] = []

    class _Spy(FakeToolRunner):
        def verify_signature(self, image, *, identity, issuer):
            seen.append(image)
            return True

    ctx = make_ctx(
        inspector=_v3_inspector(),
        tools=_Spy(),
        registry="ghcr.io",
        repository="trivoallan/regis",
        tag="0.42.0",
    )
    ProvenanceAnalyzer().analyze(ctx)
    assert seen == [ImageReference("ghcr.io", "trivoallan/regis", INDEX)]


# --- Certificate parsing edge cases --------------------------------------------


def _cert(*, san: str | None, issuer_ext: tuple[str, bytes] | None) -> x509.Certificate:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "t")])
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
    )
    if san:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.UniformResourceIdentifier(san)]),
            critical=False,
        )
    if issuer_ext:
        oid, value = issuer_ext
        builder = builder.add_extension(
            x509.UnrecognizedExtension(ObjectIdentifier(oid), value), critical=False
        )
    return builder.sign(key, hashes.SHA256())


def test_v1_issuer_extension_is_read_raw() -> None:
    cert = _cert(san="https://x", issuer_ext=("1.3.6.1.4.1.57264.1.1", b"https://iss"))
    assert sigs.certificate_signer(cert) == ("https://x", "https://iss")


def test_v2_issuer_with_long_form_length() -> None:
    issuer = "https://" + "a" * 200
    der = b"\x0c\x81" + bytes([len(issuer)]) + issuer.encode()
    cert = _cert(san="https://x", issuer_ext=("1.3.6.1.4.1.57264.1.8", der))
    assert sigs.certificate_signer(cert) == ("https://x", issuer)


@pytest.mark.parametrize(
    ("san", "issuer_ext"),
    [(None, ("1.3.6.1.4.1.57264.1.1", b"i")), ("https://x", None)],
)
def test_certificate_without_san_or_issuer_claims_nothing(san, issuer_ext) -> None:
    assert sigs.certificate_signer(_cert(san=san, issuer_ext=issuer_ext)) is None


def test_bundle_with_certificate_chain_is_read() -> None:
    cert = _cert(san="https://x", issuer_ext=("1.3.6.1.4.1.57264.1.1", b"https://i"))
    raw = base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()
    bundle = {
        "verificationMaterial": {
            "x509CertificateChain": {"certificates": [{"rawBytes": raw}]}
        }
    }
    assert sigs._bundle_signer(bundle) == ("https://x", "https://i")


@pytest.mark.parametrize(
    "bundle",
    [
        {},
        {"verificationMaterial": {"publicKey": {"hint": "k"}}},
        {"verificationMaterial": {"certificate": {"rawBytes": "not base64!"}}},
        {"verificationMaterial": {"certificate": {"rawBytes": "AAAA"}}},
    ],
)
def test_unreadable_bundle_claims_nothing(bundle) -> None:
    assert sigs._bundle_signer(bundle) is None


def test_unreadable_legacy_certificate_claims_nothing() -> None:
    layer = {"annotations": {sigs.LEGACY_CERT_ANNOTATION: "-----BEGIN junk"}}
    assert sigs._legacy_signer(layer) is None


# --- signed-by criterion -----------------------------------------------------------


def _judge(provenance: dict[str, Any], signers: list[dict[str, str]]) -> dict[str, Any]:
    report = {
        "request": {"analyzers": ["provenance"]},
        "results": {"provenance": provenance},
    }
    rules = {
        "rules": [
            {
                "provider": "provenance",
                "criterion": "signed-by",
                "slug": "signed",
                "options": {"signers": signers},
            }
        ]
    }
    return next(
        r for r in evaluate_rules(report, rules)["rules"] if r["slug"] == "signed"
    )


def _pair(signer: tuple[str, str]) -> dict[str, str]:
    return {"identity": signer[0], "issuer": signer[1]}


def test_regis_release_passes_with_its_own_ci_identity() -> None:
    result = _analyze(_v3_inspector(), {REGIS})
    assert _judge(result, [_pair(REGIS)])["status"] == "passed"


def test_regis_release_fails_with_another_identity() -> None:
    result = _analyze(_v3_inspector(), {REGIS})
    attacker = _pair(("attacker@example.com", REGIS[1]))
    assert _judge(result, [attacker])["status"] == "failed"


def test_identity_and_issuer_match_as_a_pair() -> None:
    result = _analyze(_v3_inspector(), {REGIS})
    wrong_issuer = _pair((REGIS[0], "https://accounts.google.com"))
    assert _judge(result, [wrong_issuer])["status"] == "failed"


def test_presence_alone_does_not_pass() -> None:
    result = _analyze(_v3_inspector(), set())
    assert result["has_cosign_signature"] is True
    assert _judge(result, [_pair(REGIS)])["status"] == "failed"


def test_unsigned_image_fails() -> None:
    result = _analyze(FakeImageInspector(digest=INDEX), set())
    assert _judge(result, [_pair(REGIS)])["status"] == "failed"


def test_gap_without_a_match_is_incomplete() -> None:
    class _Boom(FakeImageInspector):
        def get_referrers(self, digest: str) -> list[dict[str, Any]]:
            raise RegistryError("fallback tag 500")

    rule = _judge(_analyze(_Boom(digest=INDEX), set()), [_pair(REGIS)])
    assert rule["status"] == "incomplete"
    assert rule["missing_keys"] == ["results.provenance.signatures_complete"]


def test_gap_with_a_match_still_passes() -> None:
    class _NoTags(FakeImageInspector):
        def list_tags(self) -> list[str]:
            raise RegistryError("tags 503")

    inspector = _v3_inspector(_NoTags)
    result = _analyze(inspector, {REGIS})
    assert result["signatures_complete"] is None
    assert _judge(result, [_pair(REGIS)])["status"] == "passed"
