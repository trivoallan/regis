# Proposal

## Why

A "signed" rule in a product-tier playbook would refuse regis's own releases today, even though they are signed. Checked on `ghcr.io/trivoallan/regis:0.42.0` (index `sha256:bf13fe50…`) on 2026-10-17:

- The release workflow signs with cosign v3.1.1 (`cosign sign --yes $IMAGE@$DIGEST`, keyless). cosign v3 stores the signature as a Sigstore bundle (`application/vnd.dev.sigstore.bundle.v0.3+json`), attached as an OCI 1.1 referrer to the index. GHCR has no Referrers API, so the bundle is reachable only through the fallback tag `sha256-<hex>`. There is no `sha256-<hex>.sig` tag (404). `cosign verify` accepts the signature.
- The `provenance` analyzer looks only for the `.sig` tag. It also derives that tag from the wrong digest: the first child of an index (here amd64) instead of the index, or the config digest instead of the manifest digest for a single-arch image. As a result, `has_cosign_signature` is false for almost every image, whether it was signed with cosign v2 or v3.
- No rule reads `has_cosign_signature` yet, so the defect has not caused a wrong verdict. It must be fixed before a playbook makes signature a critical rule. `knock` signs at admission with the same cosign v3, so images placed in Harbor have the same layout.

Presence is also not proof. Anyone with push rights can attach a bundle referrer. A critical rule must check who signed, not only that an artifact exists.

## What Changes

- The `provenance` analyzer resolves the signed subject correctly: the digest of the reference as given (the index for a multi-arch image, the manifest for a single-arch one), never a child or config digest.
- It discovers signatures in both layouts: the legacy cosign tag (`sha256-<hex>.sig`) and OCI referrers. It uses the Referrers API when the registry offers one, and the `sha256-<hex>` fallback tag otherwise. It keeps bundles whose `artifactType` is a Sigstore bundle.
- Its output reports what it found: `has_cosign_signature` (kept, now correct), plus each signature's format (`legacy-tag` or `sigstore-bundle`) and where it was found.
- A new rule template verifies the signature against an identity that the playbook supplies as options: certificate identity (exact or regexp) and OIDC issuer. Its result is `passed`, `failed` (a signature exists but none matches the identity), or `incomplete` (verification could not run). It does not report `passed` because a signature merely exists.
- `ImageInspector` gains a referrers lookup. Its registry and regctl adapters implement it.
- Regis's own release becomes the acceptance fixture. A regis release must pass the verification rule with the identity `https://github.com/trivoallan/regis/.github/workflows/release.yml@refs/heads/main` and the issuer `https://token.actions.githubusercontent.com`.

Out of scope: verifying attestations (SLSA provenance and SBOM, which BuildKit attaches as `attestation-manifest` entries, and which knock attests), Notation/Notary v2 signatures, and pushing a `.sig` tag from the release workflow to work around the analyzer.

## Capabilities

### New Capabilities

- `image-signature`: how regis finds an image's signatures (subject digest, legacy tag and referrers layouts) and how a playbook rule checks them against an expected signer identity.

### Modified Capabilities

## Impact

- `regis/core/domain/analyzers/provenance.py` (subject digest, discovery, output), `regis/schemas/analyzer/provenance.schema.json` (additive fields).
- `regis/core/ports/image_inspector.py`, `regis/adapters/driven/registry/` (Referrers API with fallback tag).
- Verification engine: either `sigstore-python` (a new runtime dependency) or the `cosign` binary (a new required tool in both image variants). See design.md.
- `docs/reference` regenerated (`make reference`). `uske` and `knock` are unaffected until a playbook uses the new rule; the playbooks that would use it live outside this repo.
- Network: keyless verification needs a Sigstore trust root (TUF), which is fetched online or provided offline. This matters in an air-gapped Harbor setup.
