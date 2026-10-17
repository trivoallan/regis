# Spec Delta

## Purpose

Lets a playbook require that an image was signed by an expected signer. Regis finds the signature in the layout the signer used (the legacy cosign tag or OCI referrers) and accepts it only once it is cryptographically verified.

## ADDED Requirements

### Requirement: Signatures are looked up on the digest of the reference as given
The `provenance` analyzer SHALL look for signatures on the digest that the analyzed reference resolves to: the index digest for a multi-arch image and the manifest digest for a single-arch image. It SHALL NOT substitute the digest of a platform child or of an image config.

#### Scenario: Multi-arch release of regis
- **WHEN** `ghcr.io/trivoallan/regis:0.42.0` is analyzed, which resolves to the index `sha256:bf13fe50b59c76ff9e23369a5cb56fe4599e3120a1a604588a3abbf305514c6f` with amd64, arm64 and two attestation-manifest children
- **THEN** signatures are looked up on `sha256:bf13fe50…514c6f`, and not on the amd64 child `sha256:81b3a75b334f…`

#### Scenario: Single-arch image
- **WHEN** a reference resolves to a single image manifest
- **THEN** signatures are looked up on that manifest's digest, never on its config digest

### Requirement: Signatures are discovered in both cosign layouts
The analyzer SHALL report every signature attached to the subject. That includes signatures stored under the legacy cosign tag `sha256-<hex>.sig` and Sigstore bundles attached as OCI referrers. Referrers SHALL be found through the registry's Referrers API, or through the fallback tag `sha256-<hex>` when the registry has no Referrers API. Each reported signature SHALL carry its format (`legacy-tag` or `sigstore-bundle`) and its location: the `sha256-<hex>.sig` tag for a legacy signature, the referrer manifest digest for a bundle. A referrer SHALL be classified by its own manifest's `artifactType`, not by the descriptor in the referrers index (cosign v3 writes `application/vnd.oci.empty.v1+json` there). Referrers that are not Sigstore bundles SHALL NOT be counted as signatures.

#### Scenario: cosign v3 signature on a registry without a Referrers API
- **WHEN** `ghcr.io/trivoallan/regis:0.42.0` is analyzed, where GHCR serves no Referrers API, `sha256-bf13fe50…514c6f.sig` returns 404, and the tag `sha256-bf13fe50…514c6f` holds an index with one manifest of `artifactType` `application/vnd.dev.sigstore.bundle.v0.3+json` whose subject is the index
- **THEN** the analyzer reports exactly one signature, with format `sigstore-bundle` and location `sha256:ffabdc55de01…` (the referrer manifest), and `has_cosign_signature` is true

#### Scenario: Legacy cosign v2 signature
- **WHEN** the subject has a `sha256-<hex>.sig` tag whose manifest has at least one layer, and no referrers
- **THEN** the analyzer reports one signature with format `legacy-tag`

#### Scenario: Both layouts present after a re-sign
- **WHEN** the subject has both a `sha256-<hex>.sig` tag and a Sigstore bundle referrer
- **THEN** the analyzer reports both signatures

#### Scenario: Non-signature referrers
- **WHEN** the subject's only referrers are an SBOM and an in-toto attestation
- **THEN** the analyzer reports no signature and `has_cosign_signature` is false

#### Scenario: Unsigned image
- **WHEN** every lookup for the subject answers "not found"
- **THEN** the analyzer reports no signature and `has_cosign_signature` is false

### Requirement: Each discovered signature is verified and its signer reported
For each discovered signature, the analyzer SHALL verify the certificate chain, the transparency-log inclusion, and that the signed digest equals the subject, for the exact identity and OIDC issuer its certificate claims. It SHALL report whether verification succeeded. For a verified signature it SHALL report that identity and issuer; for an unverified one it SHALL report neither. It SHALL also report `verified_signers`, the distinct `{identity, issuer}` pairs of verified signatures.

#### Scenario: Verified signer of regis 0.42.0
- **WHEN** the signature of `ghcr.io/trivoallan/regis:0.42.0` is verified
- **THEN** it is reported as verified, with identity `https://github.com/trivoallan/regis/.github/workflows/release.yml@refs/heads/main` and issuer `https://token.actions.githubusercontent.com`

#### Scenario: Bundle signed for another digest
- **WHEN** a Sigstore bundle is attached as a referrer to the subject but signs a different digest
- **THEN** that signature is reported as not verified, with no identity

### Requirement: A playbook rule accepts only a verified signature from a listed signer
Regis SHALL provide the rule template `provenance:signed-by`, which takes `options.signers`, a list of exact `{identity, issuer}` pairs. The rule SHALL be `passed` only when a verified signature's identity and issuer together equal one listed pair. It SHALL be `failed` when no signature is discovered, or when the discovered signatures fail verification or are signed by a pair that is not listed.

#### Scenario: Regis release passes with its own CI identity
- **WHEN** `ghcr.io/trivoallan/regis:0.42.0` is judged by a playbook rule `provenance:signed-by` with `signers: [{identity: "https://github.com/trivoallan/regis/.github/workflows/release.yml@refs/heads/main", issuer: "https://token.actions.githubusercontent.com"}]`
- **THEN** the rule is `passed`

#### Scenario: Regis release fails with another identity
- **WHEN** the same image is judged with `signers: [{identity: "attacker@example.com", issuer: "https://token.actions.githubusercontent.com"}]`
- **THEN** the rule is `failed`

#### Scenario: Identity and issuer are matched as a pair
- **WHEN** a verified signature has identity A with issuer X, and the rule lists only `{identity: A, issuer: Y}`
- **THEN** the rule is `failed`

#### Scenario: Presence alone does not pass
- **WHEN** a Sigstore bundle referrer is discovered but fails verification
- **THEN** the rule is `failed`, even though `has_cosign_signature` is true

#### Scenario: Unsigned image
- **WHEN** an image with no discovered signature is judged by `provenance:signed-by`
- **THEN** the rule is `failed`

### Requirement: A technical gap makes the signature rule incomplete, never failed
When a signature lookup fails for a reason other than "not found", or verification cannot run (verification tool missing, trust root or transparency log unreachable), the analyzer SHALL report the gap. A `provenance:signed-by` rule SHALL then be `incomplete` and name what was missing, unless another signature already satisfies it.

#### Scenario: Registry error on the referrers lookup
- **WHEN** the fallback tag lookup answers HTTP 500 for an image with no other signature
- **THEN** `provenance:signed-by` is `incomplete`, not `failed`

#### Scenario: Air-gapped verification
- **WHEN** a signature is discovered but the Sigstore trust root cannot be reached and none is configured
- **THEN** `provenance:signed-by` is `incomplete` and names the verification as the missing data
