# OCI platform whitelist/blacklist rules — design

**Date:** 2026-06-08
**Status:** Approved (pending spec review)
**Scope:** Add three platform-identity criteria to the OCI analyzer.

## Problem

The OCI analyzer ships a single platform-oriented criterion, `platforms-count`,
which only checks the _number_ of supported platforms (`min_platforms`). There is
no way to express requirements about _which_ platforms an image supports:

- "the image must support at least `linux/amd64` and `linux/arm64`"
- "the image must support _only_ an approved set of platforms"
- "the image must not support a forbidden platform"

## Constraints from the existing model

- Each criterion in `default_criteria()` carries a **static** JSON Logic condition.
  The playbook overrides `params`, severity and tier — never the operator. So each
  distinct semantic needs its own slug.
- `results.oci.platforms` is a list of **objects** `{os, architecture, variant?, …}`,
  not strings, so it cannot be compared directly to a user-supplied string list.
- Custom JSON Logic operators already available: `intersects`, `contains_all`,
  `subset`, `keys`, `get`, `env_contains`. No new operator is needed.
- Rule reference pages under `docs/website/docs/reference/rules/oci/` are **generated**
  by `regis rules list -f markdown -D …` in CI (`cd-docs.yml`), straight from
  `default_criteria()`. New criteria get their reference page automatically.

## Design

### 1. Flat platform projection in the analyzer output

Add a new top-level field to the OCI analyzer result:

```text
results.oci.platforms_supported = ["linux/amd64", "linux/arm64", "linux/arm64/v8", …]
```

Built in `OciAnalyzer.analyze()` (`regis/analyzers/oci.py`) after the `platforms`
list is assembled. For each platform object:

- skip entries where `os` or `architecture` is missing or `"unknown"`;
- canonical string = `f"{os}/{architecture}"`, plus `f"/{variant}"` when a truthy
  `variant` is present;
- deduplicate while preserving first-seen order.

This mirrors `exposed_ports`, which is already a flat string list on each platform.
The three criteria below consume this field through existing operators only.

### 2. Three new criteria

Appended to `OciAnalyzer.default_criteria()`. Param name is `platforms` in all three
(the slug already carries the required/whitelist/blacklist intent — same convention as
`required-labels`, whose param is plainly `labels`). Tags `["compatibility"]`, default
level `warning` (playbooks override level/tier per binding).

| Slug                  | Semantics                             | Default `platforms`              | Condition (JSON Logic)                          |
| :-------------------- | :------------------------------------ | :------------------------------- | :---------------------------------------------- |
| `platforms-required`  | image must support **at least** these | `["linux/amd64", "linux/arm64"]` | `contains_all(platforms_supported, platforms)`  |
| `platforms-whitelist` | image must support **only** these     | `["linux/amd64", "linux/arm64"]` | `subset(platforms_supported, platforms)`        |
| `platforms-blacklist` | image must support **none** of these  | `["windows/amd64"]`              | `!(intersects(platforms_supported, platforms))` |

Operator orientation follows the existing siblings:

- `contains_all(haystack, needles)` — as in `required-labels`
  (`contains_all(keys(labels), params.labels)`).
- `subset(small, big)` — as in `exposed-ports-whitelist`
  (`subset(exposed_ports, allowed_ports)`).
- `!(intersects(...))` — blacklist as the negation, mirroring `env-blacklist`'s
  `!(env_contains(...))`.

Each criterion carries `pass`/`fail` messages with interpolation, e.g.:

- `platforms-required`
  - pass: `Image supports all required platforms.`
  - fail: `Image is missing required platforms (supported: ${results.oci.platforms_supported}; required: ${criterion.params.platforms}).`
- `platforms-whitelist`
  - pass: `All supported platforms are allowed.`
  - fail: `Image supports disallowed platforms: ${results.oci.platforms_supported} (allowed: ${criterion.params.platforms}).`
- `platforms-blacklist`
  - pass: `Image supports no forbidden platforms.`
  - fail: `Image supports forbidden platforms: ${results.oci.platforms_supported} (forbidden: ${criterion.params.platforms}).`

### 3. Schema

Add `platforms_supported` (array of string) to
`regis/schemas/analyzer/oci.schema.json`. Required because the schema sets
`additionalProperties: false`. The field is **optional** (not added to `required`),
so existing hand-crafted fixtures remain valid.

### 4. Identity & matching

Platform identity is a **canonical string**, exact-match. `linux/arm64` does **not**
match `linux/arm64/v8` — the variant is part of the identity when present. This
matches the Docker `--platform` convention and keeps matching to plain set operators.

## Edge cases (assumed behavior)

- `platforms_supported` empty (no resolvable platform): `platforms-required` **fails**
  (can't satisfy), `platforms-whitelist` **passes** (nothing disallowed),
  `platforms-blacklist` **passes** (nothing forbidden present).
- Empty `platforms` param:
  - `platforms-required` → `contains_all(x, [])` is vacuously **true** → no-op pass.
  - `platforms-whitelist` → `subset(x, [])` is true only when `x` is empty → **fails**
    as soon as any platform exists ("nothing allowed"). Documented as a footgun.
  - `platforms-blacklist` → `!(intersects(x, []))` → always **passes**.

## Testing (TDD)

- Analyzer: `platforms_supported` projection — multi-arch, variant suffix,
  `unknown`/missing filtering, dedup/order preservation.
- Rule evaluation: pass and fail paths for each of the three criteria, including the
  empty-list edge cases above.

## Out of scope

- No new JSON Logic operator.
- Default playbook left unchanged (these are opt-in policy rules).
- `platforms-count` is untouched.

## Touch list

- `regis/analyzers/oci.py` — projection in `analyze()`, three entries in
  `default_criteria()`.
- `regis/schemas/analyzer/oci.schema.json` — `platforms_supported` property.
- `docs/website/docs/reference/analyzers/oci.md` — document the new field.
- Reference rule pages — generated, not hand-written.
- Tests under the OCI analyzer / rules suites.
