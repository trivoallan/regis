---
sidebar_position: 1
---

# Migrating to Playbook schemaVersion 1

Starting with the next minor release of Regis, every playbook **must**
declare two top-level fields:

- `schemaVersion: 1` (integer)
- `version: "1.0.0"` (or another valid SemVer string)

Playbooks missing either field fail to load with a `PlaybookVersionError`.

## Automated migration

If you have an up-to-date Regis installed locally:

```bash
regis playbook upgrade path/to/playbook.yaml
```

The command:

- Injects `schemaVersion: 1` and `version: "1.0.0"` if missing
- Preserves existing comments and formatting (uses `ruamel.yaml`)
- Is idempotent — safe to re-run, prints `nothing to do` when both fields are already present

For a directory of playbooks:

```bash
find playbooks/ -name 'playbook.yaml' -exec regis playbook upgrade {} \;
```

## Manual migration

Add the two lines at the top of your `playbook.yaml`, before any other
top-level keys:

```yaml
schemaVersion: 1
version: "1.0.0"
name: Your Playbook Name
# … rest of the file unchanged …
```

Set `version` to the SemVer that best represents the current state of
your playbook (see the [reference doc](../reference/playbook-versioning.md)
for conventions). `1.0.0` is fine as a starting point.

## Verifying

```bash
regis playbook validate path/to/playbook.yaml
```

A successful run prints:

```text
  ✓ path/to/playbook.yaml is valid (schemaVersion=1, version=1.0.0).
```

If validation fails, the error message names the offending field and
suggests the fix.

## Why this change?

- **Forward compatibility:** when a future schemaVersion 2 lands, an old
  Regis will fail loudly instead of silently misinterpreting new syntax.
- **Auditability:** reports carry the playbook bundle version
  (`playbook_version`), so you can attribute a report to a specific
  playbook revision when investigating discrepancies.
