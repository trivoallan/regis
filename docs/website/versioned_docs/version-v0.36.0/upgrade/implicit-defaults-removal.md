---
sidebar_position: 3
---

# Migrating off implicit default-rule inheritance

**Breaking change.** Playbooks now evaluate **only the rules they declare**.
Previously, every analyzer's `default_criteria()` was auto-injected and evaluated
even when a playbook did not mention it. That implicit inheritance is gone:
`default_criteria()` is now a **catalogue of templates**, resolved only when a
playbook binds them via `criterion:`.

## What changed in the default playbook

Three security criteria that used to be auto-injected are now declared explicitly
and keep running by default:

- `dockle:severity-count` (slug `dockle-fatal`)
- `hadolint:severity-count` (slug `hadolint-error`)
- `secrets:secret-scan` (slug `secret-scan`)

Six opinionated OCI heuristics are **no longer evaluated by the default
playbook** (they remain available as templates you can bind yourself):

`oci:max-size`, `oci:layers-count`, `oci:platforms-count`,
`oci:exposed-ports-whitelist`, `oci:required-labels`, `oci:env-blacklist`.

The default playbook version label is bumped to `2.0.0` accordingly.

## Migrating your own playbook

If your playbook relied on analyzer defaults being applied automatically, declare
them explicitly. Discover what each analyzer offers with:

```bash
regis rules list
```

Then bind the criteria you want under `spec.rules`, for example:

```yaml
spec:
  rules:
    - provider: oci
      criterion: max-size
      slug: max-size
      level: warning
      options:
        max_mb: 1000
```

There is no automatic codemod: re-injecting former defaults would reintroduce the
heuristics the default playbook intentionally dropped.
