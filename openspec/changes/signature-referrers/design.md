# Design

## Context

See proposal.md (Why) for the defect and the evidence from the `0.42.0` release. The design is shaped by these constraints from the current code:

- Analyzers run before rules and take no playbook options. A rule is a JSON Logic condition over `results.<analyzer>.*` and `criterion.params.*` (`freshness:age` is the model). A signer identity supplied by the playbook can therefore reach only the rule, not the analyzer.
- `ImageInspector` exposes `get_manifest`, `get_blob`, `get_digest` and `list_tags`, and nothing for referrers.
- `cosign` is absent from both regis images. `adapters/driven/tools/cosign.py` uses it best-effort, for tool binaries only. `knock`'s image already bundles cosign v3.
- The two layouts as they exist in the field:

```
 subject = digest of the reference as given (index for multi-arch)
     |
     +-- legacy (cosign v2) ......... tag  sha256-<hex>.sig
     |                                 manifest, layer simplesigning.v1+json,
     |                                 cert + bundle in layer annotations
     |
     +-- referrers (cosign v3) ...... Referrers API  GET /v2/<repo>/referrers/<digest>
                                       or fallback tag sha256-<hex> (GHCR)
                                       -> index -> manifest
                                          artifactType sigstore.bundle.v0.3+json
                                          subject = <digest>
```

## Goals / Non-Goals

**Goals:**

- Discovery that is correct for both layouts and for every registry regis targets (GHCR, Docker Hub, Harbor).
- A verdict that depends on a cryptographically verified signer, never on the mere presence of an artifact.
- Signer policy declared in the playbook, in the same declarative form as other rule templates.

**Non-Goals:**

- Signing anything. Regis judges, and knock and CI sign.
- Signatures on platform children. Regis looks at the subject it was given. Signing each child is a publisher choice that regis does not chase.
- A trust policy beyond identity and issuer, such as a Rekor inclusion-time window or a key-based (non-keyless) signer. These can be added later as more template options.

## Decisions

### D1. The subject is the digest of the reference as given

The analyzer resolves the reference with `get_digest` (the registry's `Docker-Content-Digest`) and looks for signatures on that digest only. It drops the current `entries[0]` and `config.digest` fallbacks. Both are wrong: cosign signs whatever the publisher named, and the publisher names the index. `uske` already passes digests, so this matches what a screening judges.

*Alternative rejected:* also probing each child. It doubles the registry calls and would let a signed child make an unsigned index look signed.

### D2. Discovery is a union of three probes, in a fixed order

1. Referrers API on the subject. The Referrers API is authoritative when the registry answers 200.
2. Fallback tag `sha256-<hex>`, only when the API answers 404 or is absent.
3. Legacy tag `sha256-<hex>.sig`, always. A v2 signature and a v3 signature can coexist on one image after a re-sign.

A referrer counts as a signature when the `artifactType` of its own manifest is `application/vnd.dev.sigstore.bundle*`. The descriptor in the referrers index can't be trusted for this: on `0.42.0`, cosign v3.1.1 wrote `application/vnd.oci.empty.v1+json` there. Each referrer is therefore opened (one `get_manifest` each). Other referrers, such as SBOMs and attestations, are not counted. A probe that fails for a reason other than "not found" makes discovery `incomplete`, not "unsigned". A registry outage must not read as an absence.

`ImageInspector.get_referrers(digest) -> list[descriptor]` implements probes 1 and 2 inside the adapter: the HTTP adapter calls the API and falls back to the tag on 404, and the regctl adapter delegates to `regctl artifact list`, which does both. The fallback-tag rule is an OCI distribution-spec detail, so the core stays unaware of it. Probe 3 checks membership in `list_tags()` rather than fetching the tag, because the registry adapters do not tell a 404 from another error. `list_tags()` is already cached per run.

### D3. The analyzer verifies, and the rule decides who is acceptable

For each signature found, the analyzer reads the identity (SAN) and OIDC issuer that its certificate *claims*. The certificate comes from the bundle's verification material, or from the `dev.sigstore.cosign/certificate` annotation of a legacy layer. For each distinct claimed pair, it runs `cosign verify --certificate-identity <SAN> --certificate-oidc-issuer <issuer>`. This checks the certificate chain against Fulcio, the transparency-log inclusion against Rekor, and the subject digest, for exactly that signer. A single permissive `cosign verify` would not be enough: one valid signature would let a genuine bundle, copied from another image, be credited with its claimed identity. A signature counts as verified only when cosign confirms its claimed pair. Its identity and issuer are reported only then:

```json
"signatures": [
  {"format": "sigstore-bundle", "location": "referrers-tag",
   "verified": true,
   "identity": "https://github.com/trivoallan/regis/.github/workflows/release.yml@refs/heads/main",
   "issuer": "https://token.actions.githubusercontent.com"}
]
```

The analyzer also emits `verified_signers`, the distinct `{identity, issuer}` pairs of verified signatures, and `signatures_complete`, which is `true` when there was no gap and `null` otherwise. A new template `provenance:signed-by` takes `options: {signers: [{identity, issuer}, ...]}`. Its condition is `if(intersects(verified_signers, params.signers), true, and(signatures_complete, false))`, which uses the existing `intersects` operator (it compares dict items by equality). Pairs rather than two separate lists: with two lists, signature A's identity could be matched with signature B's issuer. `if` is lazy, so `signatures_complete` is read, and a gap marks the rule `incomplete`, only when no listed signer matched. Exact match only. That is enough for CI identities, which are stable URLs, and regex support would need a new JSON Logic operator.

*Alternatives rejected:* (a) passing identity options down to the analyzer would add a playbook-to-analyzer configuration channel that regis does not have, only for this case. (b) A rule on `has_cosign_signature` would accept any bundle pushed by anyone who has push rights to the repository.

`has_cosign_signature` stays in the output with a corrected meaning: at least one signature was discovered. The default playbook keeps no rule on it at `critical`.

### D4. Engine: the `cosign` binary through `ToolRunner`

The `cosign` binary handles both layouts (simplesigning in the legacy tag and bundle v0.3 in referrers) with one CLI. It is pinned to v3.1.3, the version knock ships. It joins the required tools (`regis doctor`) and is pinned with checksums in `tools/manifest.yaml`. The `full` image bakes it in. The `slim` image fetches it on first use, like grype and syft, so slim does not grow. It is reached through a new capability, `ToolRunner.verify_signature(image, identity=, issuer=) -> bool`. The adapter owns the credentials (a temporary `DOCKER_CONFIG`, as for regctl) and the optional `REGIS_COSIGN_TRUSTED_ROOT`. It maps cosign's `no matching …` and `no signatures found` errors to `False`, and any other failure to `ToolError`.

*Alternative considered:* `sigstore-python`. It is a library and adds no binary, but it verifies bundles and does not read OCI layouts. Regis would have to rebuild the legacy simplesigning path and check the DSSE subject against the image digest itself, which is security-sensitive code that cosign already maintains. If the image-size ceiling (`extra-image-size.yml`) cannot absorb cosign, revisit this choice for the `slim` variant only.

### D5. Rule outcome when verification cannot run

| Situation | `signed-by` outcome |
|---|---|
| A verified signature matches the identity and issuer | `passed` |
| Signatures found and verified, none matches | `failed` |
| No signature discovered (all probes returned "not found") | `failed` |
| A probe failed, cosign is missing, or the trust root is unreachable | `incomplete`, with the missing data named |

This follows the `incomplete` semantics introduced by `refus-auto-explicatifs`: a technical gap must never read as a refusal.

## Risks / Trade-offs

- [Keyless verification needs the Sigstore TUF root and Rekor online, which may be unreachable from an air-gapped Harbor] → A mounted trust root (`--trusted-root`) is supported through configuration, and verification without network access is `incomplete`, never `failed`.
- [Harbor's Referrers API support varies by version] → D2 falls back to the tag schema. The acceptance test covers the pilot Harbor and GHCR, not just GHCR.
- [cosign adds weight to the image] → measured against the size ceilings before the merge (see D4).
- [The output of `cosign verify` for bundles carries little identity data] → regis reads the SAN and issuer from the certificate in the verified bundle (or from the legacy layer annotations), using the `cryptography` library, and never from unverified fields.
- [The meaning of `has_cosign_signature` changes from mostly false to correct] → No rule reads it today (checked across regis and the workspace). The change log states the new meaning.

## Migration Plan

Additive. Schema fields are added, a template is added, and the default playbook is unchanged. A playbook adopts `signed-by` at `warning` first, then moves it to `critical` once a screening has shown no false refusal on the images it covers, including regis's own releases. Rollback means removing the rule from the playbook.

## Open Questions

- Should knock's admission signer identity, which differs from regis's CI identity, ship as a documented example in `docs/playbooks`? This affects only the example data, not this change.
