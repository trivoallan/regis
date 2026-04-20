# Available Rules Catalog

This file lists all verified rule templates that can be instantiated in a Regis
playbook via `rule: <slug>` + `options:`. Slugs are sourced directly from the
analyzer source files.

---

## trivy — Vulnerability & secret scanning

Source: `regis/analyzers/trivy.py`

| slug            | options                                                                                  | description                                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `cve-count`     | `level` (string: `critical` / `high` / `medium` / `low`), `max_count` (int, default `0`) | Fail if the number of CVEs at the given severity exceeds `max_count`. Use one rule per severity level you want to enforce. |
| `fix-available` | `max_count` (int, default `0`)                                                           | Fail if the number of CVEs that have a fix available exceeds `max_count`.                                                  |
| `secret-scan`   | `max_count` (int, default `0`)                                                           | Fail if the number of embedded secrets/tokens detected exceeds `max_count`.                                                |

### Example — trivy rules

```yaml
- provider: trivy
  rule: cve-count
  slug: cve-critical
  level: critical
  options:
    level: critical
    max_count: 0

- provider: trivy
  rule: cve-count
  slug: cve-high
  level: warning
  options:
    level: high
    max_count: 10

- provider: trivy
  rule: fix-available
  slug: cve-fixable
  level: warning
  options:
    max_count: 0

- provider: trivy
  rule: secret-scan
  slug: no-secrets
  level: critical
  options:
    max_count: 0
```

---

## hadolint — Dockerfile linting

Source: `regis/analyzers/hadolint.py`

| slug             | options                                                                        | description                                                                  |
| ---------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `severity-count` | `level` (string: `error` / `warning` / `info`), `max_count` (int, default `0`) | Fail if Dockerfile lint violations at the given severity exceed `max_count`. |

### Example — hadolint rules

```yaml
- provider: hadolint
  rule: severity-count
  slug: dockerfile-errors
  level: warning
  options:
    level: error
    max_count: 0
```

---

## dockle — CIS Docker Benchmark

Source: `regis/analyzers/dockle.py`

| slug             | options                                                                     | description                                                                                                                                                  |
| ---------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `severity-count` | `level` (string: `fatal` / `warn` / `info`), `max_count` (int, default `0`) | Fail if CIS benchmark violations at the given severity exceed `max_count`. Note: dockle severity levels are `fatal`, `warn`, `info` — not `error`/`warning`. |

### Example — dockle rules

```yaml
- provider: dockle
  rule: severity-count
  slug: cis-fatal
  level: critical
  options:
    level: fatal
    max_count: 0
```

---

## sbom — Software Bill of Materials

Source: `regis/analyzers/sbom.py`

| slug                | options                                              | description                                                          |
| ------------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| `has-sbom`          | (none)                                               | Image must provide an SBOM (CycloneDX or SPDX). No options required. |
| `license-blocklist` | `blocklist` (list of SPDX identifiers, default `[]`) | Fail if any package in the SBOM uses a license from the blocklist.   |

### Example — sbom rules

```yaml
- provider: sbom
  rule: has-sbom
  slug: has-sbom
  level: warning

- provider: sbom
  rule: license-blocklist
  slug: no-copyleft
  level: critical
  enable: false # opt-in; remove or set true to activate
  options:
    blocklist:
      - GPL-2.0
      - GPL-2.0-only
      - GPL-2.0-or-later
      - GPL-3.0
      - GPL-3.0-only
      - GPL-3.0-or-later
      - AGPL-1.0
      - LGPL-2.1
      - LGPL-3.0
```

---

## freshness — Image age

Source: `regis/analyzers/freshness.py`

| slug  | options                        | description                                             |
| ----- | ------------------------------ | ------------------------------------------------------- |
| `age` | `max_days` (int, default `30`) | Image must have been built no more than `max_days` ago. |

### Example — freshness rules

```yaml
- provider: freshness
  rule: age
  slug: age
  level: info
  options:
    max_days: 90
```

---

## scorecarddev — OpenSSF Scorecard

Source: `regis/analyzers/scorecarddev.py`

| slug        | options                            | description                                                                                              |
| ----------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `min-score` | `min_score` (float, default `5.0`) | The OpenSSF Scorecard score for the image's source repository must be at least `min_score` (0–10 scale). |

### Example — scorecarddev rules

```yaml
- provider: scorecarddev
  rule: min-score
  slug: openssf-score
  level: warning
  options:
    min_score: 7.0
```

---

## skopeo — Image configuration

Source: `regis/analyzers/skopeo.py`

| slug                      | options                                             | description                                                                           |
| ------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `user-blacklist`          | `blacklist` (list of strings, e.g. `["root", "0"]`) | Fail if the container runs as a blacklisted user.                                     |
| `max-size`                | `max_mb` (float)                                    | Fail if the image exceeds the given size in megabytes.                                |
| `layers-count`            | `max_count` (int)                                   | Fail if the image has more than `max_count` layers.                                   |
| `tag-blacklist`           | `blacklist` (list of tag pattern strings)           | Fail if the image tag matches any pattern in the blacklist (e.g., `["latest"]`).      |
| `platforms-count`         | `min_count` (int)                                   | Fail if the image supports fewer than `min_count` platforms (multi-arch enforcement). |
| `exposed-ports-whitelist` | `whitelist` (list of port strings or numbers)       | Fail if any exposed port is not in the whitelist.                                     |
| `required-labels`         | `labels` (list of OCI label name strings)           | Fail if any label in the list is absent from the image manifest.                      |
| `env-blacklist`           | `blacklist` (list of env var name strings)          | Fail if any env var in the blacklist is set in the image config.                      |

### Example — skopeo rules

```yaml
- provider: skopeo
  rule: user-blacklist
  slug: no-root
  level: critical
  options:
    blacklist:
      - root
      - "0"

- provider: skopeo
  rule: max-size
  slug: image-size
  level: warning
  options:
    max_mb: 500

- provider: skopeo
  rule: tag-blacklist
  slug: no-latest-tag
  level: warning
  options:
    blacklist:
      - latest

- provider: skopeo
  rule: required-labels
  slug: required-labels
  level: warning
  options:
    labels:
      - org.opencontainers.image.version
      - org.opencontainers.image.source
```

---

## core — Built-in policy rules

| slug                        | options                                                                          | description                                      |
| --------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------ |
| `registry-domain-whitelist` | `domains` (list, default: `[docker.io, registry-1.docker.io, quay.io, ghcr.io]`) | Image must come from an allowed registry domain. |

### Example — core rules

```yaml
- provider: core
  rule: registry-domain-whitelist
  slug: registry-domain-whitelist
  level: critical
  options:
    domains:
      - docker.io
      - registry-1.docker.io
      - quay.io
      - ghcr.io
```

---

## Providers with no configurable rule templates

These providers run automatically during `regis analyze` and contribute data to the
report, but they do not expose rule templates you can configure in a playbook:

| Provider     | What it measures                                      |
| ------------ | ----------------------------------------------------- |
| `endoflife`  | Whether the base OS / runtime has reached end-of-life |
| `popularity` | Registry pull counts and stars                        |
| `size`       | Compressed and uncompressed image size breakdown      |
| `provenance` | Supply chain provenance evidence (Sigstore / SLSA)    |

To enforce policy on these, use the `skopeo` rules (size) or wait for future rule
templates to be added to those analyzers.
