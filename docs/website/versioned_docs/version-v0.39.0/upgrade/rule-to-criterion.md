---
sidebar_position: 2
---

# Migrating from `rule` to `criterion`

Regis renamed one layer of its policy vocabulary. The reusable, parameterized
_condition_ an analyzer ships is now called a **criterion**. The word **rule** is
reserved for the policy _decision_ you write in a playbook — a criterion bound to
options, a severity level, and a tier. See [Rules and
criteria](../concepts/rules.md) for the full four-layer model.

This rename touched two surfaces of a playbook:

- the **template-reference key** in each rule entry: `rule:` → `criterion:`;
- **JSON Logic and message references** to the bound condition's parameters:
  `rule.params.*` → `criterion.params.*` (and bare `${rule.…}` interpolations →
  `${criterion.…}`).

Analyzer **metrics** under the `results.*` namespace are unchanged.

## Deprecation window

The legacy forms still work, so existing playbooks keep evaluating:

- A playbook entry that uses the `rule:` key is still accepted, but emits a
  deprecation warning. Prefer `criterion:`.
- Inside conditions and messages, `rule.params.*` (and bare `rule`) still resolve
  through a dual-bind, but are deprecated. Prefer `criterion.params.*`.

Migrate at your convenience before the legacy forms are removed in a future
release.

## Automated migration

If you have an up-to-date Regis installed locally, run the codemod:

```bash
regis playbook migrate path/to/playbook.yaml
```

By default the migrated YAML is written to **stdout**, so you can review the diff
before committing:

```bash
regis playbook migrate playbook.yaml | diff playbook.yaml -
```

Pass `--in-place` (or `-i`) to overwrite the file:

```bash
regis playbook migrate playbook.yaml --in-place
```

The command:

- Renames the `rule:` template-reference key to `criterion:` in every rule entry.
- Rewrites `rule.` references in JSON Logic `condition` trees and `${rule.…}`
  interpolations in `messages` to `criterion`. `results.*` metric paths are left
  untouched.
- Preserves comments, ordering, and formatting (round-trip YAML).
- Is **idempotent** — running it on an already-migrated playbook is a no-op.
- Is **evaluation-preserving** — the report a migrated playbook produces is
  identical to the report the original produced.

For a directory of playbooks:

```bash
find playbooks/ -name 'playbook.yaml' -exec regis playbook migrate {} --in-place \;
```

:::caution Known limitation
A trailing inline comment on the renamed `rule:` key is dropped during migration
(for example, `rule: cve-count  # critical CVEs`). Block comments and overall
ordering are preserved. If you rely on such a comment, re-add it after migrating.
:::

## Manual migration

If you prefer to edit by hand, apply the same two changes.

**Before:**

```yaml
spec:
  rules:
    - provider: cve
      rule: cve-count # template reference
      slug: cve-critical
      level: critical
      options:
        level: critical
        max_count: 0
      messages:
        fail: "Found ${results.cve.critical_count} CVEs (max ${rule.params.max_count})."
```

**After:**

```yaml
spec:
  rules:
    - provider: cve
      criterion: cve-count # was: rule
      slug: cve-critical
      level: critical
      options:
        level: critical
        max_count: 0
      messages:
        fail: "Found ${results.cve.critical_count} CVEs (max ${criterion.params.max_count})."
```

Note that `results.cve.critical_count` — a metric — is unchanged; only the
criterion reference and `criterion.params.*` change.

## Verifying

```bash
regis playbook validate path/to/playbook.yaml
```

Because the migration is evaluation-preserving, you can also confirm a report is
unchanged by evaluating before and after against the same `report.json`:

```bash
regis evaluate report.json --playbook before.yaml -o before-rules.json
regis evaluate report.json --playbook after.yaml  -o after-rules.json
diff before-rules.json after-rules.json   # expect no differences
```
