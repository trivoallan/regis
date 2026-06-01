---
sidebar_position: 4
---

# Playbook Versioning

Every Regis playbook uses a Kubernetes-style resource envelope. Two fields carry version information:

| Field                                           | Required | Purpose                                                      |
| ----------------------------------------------- | -------- | ------------------------------------------------------------ |
| `apiVersion`                                    | yes      | Identifies the playbook format. Must equal `regis.trivoallan.dev/v1alpha1`. |
| `metadata.labels["app.kubernetes.io/version"]`  | yes      | SemVer of your playbook bundle (`MAJOR.MINOR.PATCH`).        |

## Example

```yaml
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: my-playbook
  title: My Playbook
  labels:
    app.kubernetes.io/version: "1.0.0"
spec:
  # … rules, tiers, badges, …
```

## `apiVersion`

The `apiVersion` field encodes the API group and version of the playbook format.
The only supported value is `regis.trivoallan.dev/v1alpha1`.

Future breaking changes to the schema will introduce a new `apiVersion` (e.g.
`v1beta1`, `v1`). Regis will reject playbooks declaring an unsupported
`apiVersion` with a clear error.

Purely **additive** changes to the schema (new optional fields, new JSON Logic
operators) do **not** bump the `apiVersion`.

## `metadata.labels["app.kubernetes.io/version"]`

A SemVer string (`MAJOR.MINOR.PATCH`, no pre-release or build metadata).
This is the version of **your playbook bundle**, independent from the Regis
binary version.

Suggested convention:

- **Major:** removed or renamed a rule.
- **Minor:** added a rule, tier, or badge.
- **Patch:** tweaked thresholds, descriptions, or labels.

Regis enforces the SemVer format but not the discipline — the convention
above is yours to follow.

## Validation

```bash
regis playbook validate path/to/playbook.yaml
```

A successful run prints:

```text
  ✓ path/to/playbook.yaml is valid (apiVersion=regis.trivoallan.dev/v1alpha1, kind=Playbook, version=1.0.0).
```

If validation fails, the error message names the offending field and suggests the fix.

## Report metadata

A report produced by `regis analyze` carries the playbook's identity for
traceability:

```json
{
  "playbook_name": "My Playbook",
  "playbook_version": "1.2.3",
  "api_version": "regis.trivoallan.dev/v1alpha1",
  "version": "0.33.0"
}
```

Where `version` at the top level is the **regis binary** version (set by
`regis analyze`), and `playbook_version` / `api_version` come from the
playbook itself.

## Migrating an existing playbook

If your `playbook.yaml` still uses the old `schemaVersion`/`name` flat format,
run the automated migration:

```bash
regis playbook upgrade path/to/playbook.yaml
```

See the [migration guide](../upgrade/playbook-schema-v1.md) for details.
