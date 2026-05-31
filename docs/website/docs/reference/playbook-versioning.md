---
sidebar_position: 4
---

# Playbook Versioning

Every Regis playbook declares two version-related fields at its root:

| Field           | Type    | Required | Purpose                                              |
| --------------- | ------- | -------- | ---------------------------------------------------- |
| `schemaVersion` | integer | yes      | Identifies the format version of the playbook.       |
| `version`       | string  | yes      | SemVer of the playbook bundle (`MAJOR.MINOR.PATCH`). |

## Example

```yaml
schemaVersion: 1
version: "1.0.0"
name: My Playbook
# … rules, tiers, badges, …
```

## `schemaVersion`

A monotonically increasing integer. Each bump is **breaking** — Regis ships
with a fixed set of supported `schemaVersion` values, and any playbook
declaring an unsupported value fails to load with a clear error.

Purely **additive** changes to the schema (new optional fields, new JSON
Logic operators) do **not** bump `schemaVersion`.

### Changelog

#### Version 1 (current)

Initial versioned schema. The authoritative source is
[`definition.schema.json`](./schemas/playbook/definition.schema.md).

## `version`

A SemVer string (`MAJOR.MINOR.PATCH`, no pre-release or build metadata).
This is the version of **your playbook bundle**, independent from the Regis
binary version.

Suggested convention:

- **Major:** removed or renamed a rule.
- **Minor:** added a rule, tier, or badge.
- **Patch:** tweaked thresholds, descriptions, or labels.

Regis enforces the SemVer format but not the discipline — the convention
above is yours to follow.

## Validation errors

When `schemaVersion` is missing:

```text
PlaybookVersionError: playbook 'path/to/playbook.yaml' is missing required field 'schemaVersion'.
Add `schemaVersion: 1` at the top of the file.
Supported versions: [1].
```

When `schemaVersion` is set to an unknown value (e.g. when an old Regis
sees a playbook authored for a future version):

```text
PlaybookVersionError: playbook 'path/to/playbook.yaml' declares schemaVersion=2 but this
regis (vX.Y.Z) only supports [1]. Upgrade regis or use a compatible playbook.
```

## Report metadata

A report produced by `regis analyze` carries the playbook's identity for
traceability:

```json
{
  "playbook_name": "My Playbook",
  "playbook_version": "1.2.3",
  "schema_version": 1,
  "version": "0.33.0"
}
```

Where `version` at the top level is the **regis binary** version (set by
`regis analyze`), and `playbook_version` / `schema_version` come from the
playbook itself.

## Migrating an existing playbook

See the [migration guide](../upgrade/playbook-schema-v1.md).
