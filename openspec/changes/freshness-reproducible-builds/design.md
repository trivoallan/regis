## Context

See proposal.md. `_get_created_date` returns the config `created` string; `analyze` derives `age_days` and `behind_latest_days` from it. JSON Logic evaluates `null < N` as false, so a null age fails the rule (fail-closed).

## Goals / Non-Goals

**Goals:**
- Stop penalising epoch-pinned images without weakening the rule for unknown dates.

**Non-Goals:**
- Sourcing an age from elsewhere (`org.opencontainers.image.created`, layer history, registry Last-Modified). A reproducible image is *unknown-age*, not *fresh*; a follow-up can add a real signal.
- Changing the "Fresh" badge semantics.

## Decisions

- **Cutoff 1980-01-01 rather than exact epoch**: covers epoch 0 and the ZIP epoch (1980) some tools use; no real image predates it. Alternative (exact `== 1970-01-01`) misses the 1980 case.
- **New boolean instead of overloading `age_days`**: keeps `age_days` honest (null = unknown) and lets rules distinguish "pinned on purpose" from "unparseable" (which must still fail). Alternative (a large sentinel age) would recreate the bug.
- **Rule carries the exemption (`or`)**: the exemption lives in the criterion condition, visible in the playbook, rather than hidden in the analyzer.
- **Pass message reworded** to avoid printing "null days".

## Risks / Trade-offs

- [Reproducible image passes freshness without evidence it is fresh] → documented non-goal; follow-up signal.
- [Custom playbooks re-implementing `age`] → must add the same `or` clause; noted in proposal.
- ["Fresh" badge misleading for reproducible images] → out of scope here; candidate follow-up "Unknown" badge.
