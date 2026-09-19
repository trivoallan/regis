## Why

Reproducible builds (ko, distroless/Bazel, `SOURCE_DATE_EPOCH=0`) pin the image config `created` field to 1970-01-01 on purpose. The freshness analyzer reads that as "20715 days old", so the `age` rule fails for the images with the best hygiene (`gcr.io/distroless/static-debian12:nonroot`, `cosign:v3.1.1`). Downstream playbooks (oci-supply-chain-spec "Placement direct") then send them to a rebuild they do not need.

## What Changes

- The freshness analyzer treats a `created` date before 1980-01-01 as a pinned date, not an age: it reports `reproducible_build: true` and `age_days: null`.
- `freshness.schema.json` gains a required boolean `reproducible_build`.
- The default `age` criterion passes when `reproducible_build` is true or `age_days < max_days`; an unparseable or missing date still fails.

## Capabilities

### New Capabilities

- `freshness-analysis`: how the freshness analyzer reports image age and how the default `age` criterion judges it, including reproducible builds.

### Modified Capabilities

## Impact

- `regis/core/domain/analyzers/freshness.py`, `regis/schemas/analyzer/freshness.schema.json`, `tests/test_analyzer_freshness.py`.
- Report output gains a field (additive). Custom playbooks with their own age condition must add the same `or reproducible_build` clause.
- The default playbook's "Fresh" badge follows `rules.age.passed`, so it shows "Fresh" for reproducible images.
