# Tasks

Build plan: Wave 0 is T1, T2 and T3, run in parallel. T4 waits for T1 and T2, T5 for T3 and T4, and T6 for T5. Critical path: T2 → T4 → T5 → T6. Merge T3 alone first if the image-size check fails (design D4).

## 1. Subject digest (T1, S, Wave 0)

- [x] 1.1 Make the `provenance` analyzer resolve the subject with `get_digest` on the reference as given, removing the `entries[0]` and `config.digest` fallbacks; verify with unit tests for an index (the subject is the index digest, never the amd64 child) and for a single manifest (the subject is the manifest digest, never the config digest)

## 2. Referrers lookup (T2, M, Wave 0)

- [x] 2.1 Add `get_referrers(digest, artifact_type=None)` to the `ImageInspector` port; verify that `make lint` (import-linter, mypy) passes
- [x] 2.2 Implement it in the registry adapter: use the Referrers API when it answers 200, otherwise the `sha256-<hex>` fallback tag, and raise a distinct error for any status other than 404; verify with recorded-response tests for API 200, API 404 with the fallback tag present, both absent, and fallback 500
- [x] 2.3 Implement it in the regctl adapter with the same behavior; verify with the same test cases run against a stubbed `ToolRunner`

## 3. Verification tool (T3, S, Wave 0)

- [x] 3.1 Add `cosign` v3.1.3 to `tools/manifest.yaml` (pinned, checksummed, fetched on demand in `slim`) and bake it into `full`; verify that `make image` passes, including the smoke test, and that `extra-image-size.yml` stays under its ceilings
- [x] 3.2 Add `cosign` to the required-tools list and to the docs that name the required binaries (`CLAUDE.md`, `docs/`); verify that `regis doctor` reports cosign

## 4. Discovery (T4, M, after T1 and T2)

- [x] 4.1 Run the three lookups from design D2 (Referrers API or fallback tag, then the legacy `.sig` tag), keep only Sigstore bundle referrers, and report `signatures[]` with `format` and `location`; verify with tests covering the v3-only, v2-only, both, non-signature-referrers and unsigned cases from the spec
- [x] 4.2 Report a lookup gap (any error other than "not found") in the analyzer output instead of reporting no signature; verify with a test where the fallback tag answers 500
- [x] 4.3 Make `has_cosign_signature` mean "at least one signature discovered" and extend `provenance.schema.json` additively (`signatures[]`, the gap fields); verify with schema validation tests and with `make reference` followed by committing the regenerated `docs/reference`

## 5. Verification and rule template (T5, M, after T3 and T4)

- [x] 5.1 Read the claimed identity and issuer from each signature's certificate (bundle verification material or legacy annotation), then confirm each distinct pair with `ToolRunner.verify_signature` (`cosign verify` for that exact identity and issuer, optional `REGIS_COSIGN_TRUSTED_ROOT`); verify with tests on a fixture bundle (verified, with the expected SAN and issuer), on a bundle signed for another digest (not verified), and on the tool being missing (a gap)
- [x] 5.2 Add the template `provenance:signed-by` (`options.signers`, exact `{identity, issuer}` pairs) to `default_criteria()`, without enabling it in the default playbook; verify with JSON Logic tests for passed, wrong identity (failed), identity with the wrong issuer (failed), unverified bundle (failed), unsigned (failed), and a gap with no other signature (incomplete)
- [x] 5.3 Document the template and its options in `docs/` (rule reference and a playbook example); verify that `make reference` leaves no diff

## 6. Acceptance on a real release (T6, S, after T5)

- [x] 6.1 Run `regis analyze ghcr.io/trivoallan/regis:0.42.0` with a playbook using `provenance:signed-by` and the CI identity and issuer from the spec, then with `attacker@example.com`; verify that the first is `passed`, the second `failed`, and that the reported signature is `sigstore-bundle` at the referrer manifest digest
- [ ] 6.2 Repeat on an image that knock signed in the pilot Harbor (Referrers API path) with knock's admission identity; verify `passed`, and record the Harbor version and the lookup path taken in the PR description
- [x] 6.3 Run the full suite and the gates (`make lint`, `make test`, `make security`); verify that all pass, with per-file coverage at or above 90%
