---
sidebar_position: 1
---

# Migrating to the apiVersion/kind playbook format

Starting with Regis v0.34, every playbook **must** use the Kubernetes-style
resource envelope:

```yaml
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: <id>
  title: <Display Name>
  labels:
    app.kubernetes.io/version: "1.0.0"
spec:
  tiers: [...]
  rules: [...]
```

Playbooks that still use the old flat format (`schemaVersion`/`name`/`version`
at the root) are automatically upgraded on load, but the upgrade is not written
back to disk. Run the migration command to make the change permanent.

## Field mapping

| Old field                    | New location                                   | Notes                                       |
| ---------------------------- | ---------------------------------------------- | ------------------------------------------- |
| `schemaVersion`              | replaced by `apiVersion`                       | `apiVersion: regis.trivoallan.dev/v1alpha1` |
| `name`                       | `metadata.title`                               | human-readable display name                 |
| `slug`                       | `metadata.name`                                | machine id — RFC 1123 DNS label             |
| `description`                | `metadata.description`                         | optional                                    |
| `version`                    | `metadata.labels["app.kubernetes.io/version"]` | SemVer string                               |
| `tiers`                      | `spec.tiers`                                   |                                             |
| `rules`                      | `spec.rules`                                   |                                             |
| `badges`                     | `spec.badges`                                  |                                             |
| `integrations`               | `spec.integrations`                            |                                             |
| `links`                      | `spec.links`                                   |                                             |
| `pages`/`sections`/`sidebar` | removed                                        | not used by the report viewer               |

## Automated migration

If you have an up-to-date Regis installed locally:

```bash
regis playbook upgrade path/to/playbook.yaml
```

The command:

- Rewrites the file to the `apiVersion`/`kind`/`metadata`/`spec` envelope
- Moves every field to its new location (see mapping above)
- Preserves existing comments and formatting (uses `ruamel.yaml`)
- Is idempotent — safe to re-run, prints `nothing to do` when the file is
  already in the new format

For a directory of playbooks:

```bash
find playbooks/ -name 'playbook.yaml' -exec regis playbook upgrade {} \;
```

## Manual migration

Replace the flat header with the envelope. Example:

**Before:**

```yaml
schemaVersion: 1
version: "1.0.0"
name: Your Playbook Name
slug: your-playbook
description: "Optional description."
# … rest of the file unchanged …
```

**After:**

```yaml
# yaml-language-server: $schema=https://trivoallan.github.io/regis/schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: your-playbook # was: slug
  title: Your Playbook Name # was: name
  description: "Optional description."
  labels:
    app.kubernetes.io/version: "1.0.0" # was: version
spec:
  tiers: [...] # unchanged content, now under spec
  rules: [...] # unchanged content, now under spec
  badges: [...] # unchanged content, now under spec
```

Note: `metadata.name` must be an RFC 1123 DNS label — lowercase alphanumerics
and hyphens only, max 63 characters. If your old `slug` contained underscores or
uppercase letters, replace them with hyphens.

## Verifying

```bash
regis playbook validate path/to/playbook.yaml
```

A successful run prints:

```text
  ✓ path/to/playbook.yaml is valid (apiVersion=regis.trivoallan.dev/v1alpha1, kind=Playbook, version=1.0.0).
```

If validation fails, the error message names the offending field and suggests
the fix.

## Why this change?

- **Kubernetes-style familiarity:** the envelope matches the format used by
  Helm charts, Kustomize overlays, and most cloud-native tooling, making
  playbooks easier to read and to validate with standard YAML tooling.
- **Forward compatibility:** when a future `v1beta1` lands, an old Regis will
  fail loudly instead of silently misinterpreting new syntax.
- **Auditability:** reports carry the playbook bundle version
  (`playbook_version`), so you can attribute a report to a specific playbook
  revision when investigating discrepancies.
