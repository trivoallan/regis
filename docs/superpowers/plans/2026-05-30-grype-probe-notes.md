# grype/syft/trufflehog probe notes — locking down output shapes

- **Date:** 2026-05-30
- **Goal:** resolve the trivy→grype/syft/trufflehog migration's open questions
  empirically so later tasks parse real output shapes, not guesses. Mirrors the
  prior regctl spike (`2026-05-29-regctl-probe-notes.md`).
- **Probe image (clean):** `alpine:3.20` (`docker.io/library/alpine:3.20`).
- **Richer reference image (CVE variety):** `debian:11` — alpine:3.20 only
  surfaces 3 Medium CVEs, too thin to enumerate the full severity / fix-state
  vocabularies, so debian:11 (173 matches) was scanned to confirm them.
- **Secret-detection probe:** locally-built throwaway image with a fake AWS key
  pair (built, scanned, removed — not committed). The fake key is redacted out
  of the saved fixture.
- **Fixtures captured under `tests/fixtures/`:**
  - `grype/alpine_json.json` — grype JSON, clean image.
  - `grype/debian11_json.json` — grype JSON, rich CVE set (severity + fix-state).
  - `syft/alpine_cyclonedx.json` — syft CycloneDX-JSON.
  - `trufflehog/alpine_ndjson.txt` — empty (clean image, zero secrets).
  - `trufflehog/stderr.txt` — clean-image log + `exit=0`.
  - `trufflehog/secret_present_ndjson.txt` — 2 findings, `Raw`/`RawV2` redacted.
  - `trufflehog/secret_present_stderr.txt` — scan summary + `exit=183`.

Platform: `darwin/arm64`, all tools installed via Homebrew bottles.

---

## 1. Version sub-command, output stream, and pinned versions

| Tool       | Sub-command            | Output stream | Exit | Installed version |
| ---------- | ---------------------- | ------------- | ---- | ----------------- |
| grype      | `grype version`        | **stdout**    | 0    | **0.112.0**       |
| syft       | `syft version`         | **stdout**    | 0    | **1.44.0**        |
| trufflehog | `trufflehog --version` | **stdout**    | 0    | **3.95.3**        |

Notes:

- **grype / syft** use the bare `version` sub-command (no `--`). `grype version`
  also prints `Syft Version: v1.44.0` and `Supported DB Schema: 6`; `syft version`
  prints `SchemaVersion: 16.1.3`. Both emit multi-line key/value blocks; the
  version number is on the `Version:` line.
- **trufflehog** uses `--version` (the _flag_), **not** a `version` sub-command —
  `trufflehog version` errors with `expected command but got "version"`.
  Output is the single line `trufflehog 3.95.3`.
- **All three print version info to stdout, not stderr.** (Differs from regctl's
  doctor expectations only in the sub-command spelling — see trufflehog.) A
  doctor/`require_tool` check can read stdout uniformly. For trufflehog, parse
  `trufflehog --version` → split on whitespace, take the last token.

Pin targets for later tasks / CI: `grype@0.112.0`, `syft@1.44.0`,
`trufflehog@3.95.3`.

---

## 2. grype JSON shape — RESOLVED

Command: `grype <ref> -o json` → JSON to **stdout**, exit 0. (stderr carries
progress + an "EOL distro" warning for alpine 3.20; harmless, ignore.)

Top-level keys: `descriptor`, `distro`, `matches`, `source`, `alertsByPackage`.

- **`descriptor.version` → CONFIRMED** = `"0.112.0"` (the grype version string,
  no `v` prefix). `descriptor.name` = `"grype"`. So the report can record the
  scanner version from `descriptor.version` directly.

### `matches[].vulnerability.severity` — CONFIRMED (matches plan)

Full observed set across alpine + debian:11:
`Critical`, `High`, `Medium`, `Low`, `Negligible`, `Unknown`
— exactly the six the plan expected. Capitalized, title-case.

### `matches[].vulnerability.fix.state` — ⚠️ PARTIAL DISCREPANCY

`fix` is an object `{ "versions": [...], "state": "..." }`.

- **Observed `state` values:** `fixed`, `not-fixed`, `wont-fix`, **and `""`
  (empty string)**.
- The plan expected `fixed / not-fixed / wont-fix / unknown`. In practice grype
  emitted **`""` (empty)** for the "unknown" case in the alpine sample, not the
  literal string `unknown`.
- **However** grype's own CLI advertises the canonical vocabulary as
  `[fixed not-fixed unknown wont-fix]` (from `grype --help`:
  `--ignore-states ... options=[fixed not-fixed unknown wont-fix]`). So
  `unknown` is a valid value grype _can_ emit, but the JSON output also uses
  `""` for the unknown/unset case.
- **Plan impact:** later code must treat `fix.state` as one of
  `{fixed, not-fixed, wont-fix, unknown, ""}` and normalize `""` → `unknown`
  (or handle both). Do **not** assume a non-empty value.

### `matches[].artifact.{name,version,type}` — CONFIRMED

`artifact` keys (union): `id`, `name`, `version`, `type`, `language`,
`licenses`, `cpes`, `purl`, `locations`, `upstreams`, `metadata`,
`metadataType`. `artifact.type` was `apk` (alpine) / `deb` (debian) — i.e. the
package ecosystem.

### Representative `matches[]` element (alpine, `busybox` CVE)

```json
{
  "vulnerability": {
    "id": "CVE-2025-60876",
    "dataSource": "https://nvd.nist.gov/vuln/detail/CVE-2025-60876",
    "namespace": "nvd:cpe",
    "severity": "Medium",
    "urls": ["..."],
    "description": "BusyBox wget ...",
    "cvss": [
      {
        "source": "134c704f-9b21-4f2e-91b3-4a467353bcc0",
        "type": "Secondary",
        "version": "3.1",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N",
        "metrics": { "baseScore": 6.5, "exploitabilityScore": 3.9, "impactScore": 2.6 },
        "vendorMetadata": {}
      }
    ],
    "epss": [{ "cve": "CVE-2025-60876", "epss": 0.00051, "percentile": 0.16364, "date": "2026-05-29" }],
    "cwes": [{ "cve": "CVE-2025-60876", "cwe": "CWE-284", "source": "...", "type": "Secondary" }],
    "fix": { "versions": [], "state": "" },
    "advisories": [],
    "risk": 0.029325
  },
  "relatedVulnerabilities": [],
  "matchDetails": [
    {
      "type": "cpe-match",
      "matcher": "apk-matcher",
      "searchedBy": { "namespace": "nvd:cpe", "cpes": ["cpe:2.3:a:busybox:busybox:1.36.1:*:*:*:*:*:*:*"],
                      "package": { "name": "busybox", "version": "1.36.1-r31" } },
      "found": { "vulnerabilityID": "CVE-2025-60876", "versionConstraint": "<= 1.37.0 (unknown)",
                 "cpes": ["cpe:2.3:a:busybox:busybox:*:*:*:*:*:*:*:*"] }
    }
  ],
  "artifact": {
    "id": "a6a0537c11acf05d",
    "name": "busybox",
    "version": "1.36.1-r31",
    "type": "apk",
    "locations": [ ... ]
  }
}
```

(Note: `vulnerability.id` is `CVE-…`; `cvss[].metrics.baseScore` carries the
score; `epss` and `risk` are extra grype enrichment fields available if useful.)

---

## 3. syft CycloneDX-JSON shape — RESOLVED (key surprise on version location)

Command: `syft <ref> -o cyclonedx-json` → JSON to **stdout**, exit 0 (clean
stderr).

Top-level keys: `$schema`, `bomFormat`, `specVersion`, `serialNumber`,
`version`, `metadata`, `components`, `dependencies`.

- **`bomFormat` → CONFIRMED** = `"CycloneDX"`.
- **`specVersion` → `"1.6"`** (the plan didn't pin a version; note it — the
  `metadata.tools` shape below depends on being CycloneDX ≥ 1.5).
- **`components[]` → CONFIRMED** present, array (92 entries for alpine).
  `component.type` set: `library`, `file`, `operating-system`. Each library
  component has `bom-ref`, `type`, `name`, `version`, `purl`, `cpe`, `licenses`,
  `properties[]` (syft-specific `syft:package:*` props), etc.
- **`dependencies[]` → CONFIRMED** present, array. Each entry is
  `{ "ref": "<purl/bom-ref>", "dependsOn": ["<purl>", ...] }`.

### ⚠️ KEY FINDING — where the syft version lives: `metadata.tools.components[]`

`metadata.tools` is **NOT an array**. It is an **object** containing a
`components[]` array (the modern CycloneDX 1.5+ "tools" shape). Full subtree:

```json
"metadata": {
  "tools": {
    "components": [
      {
        "type": "application",
        "author": "anchore",
        "name": "syft",
        "version": "1.44.0"
      }
    ]
  }
}
```

So the syft version is read as:
`metadata.tools.components[?(name=="syft")].version` → `"1.44.0"`.

**Plan impact:** any code/spec that expected `metadata.tools` to be a flat array
(the pre-1.5 `tools: [ { vendor, name, version } ]` shape) is **wrong** for syft
1.44 / CycloneDX 1.6. Parse `metadata.tools.components[]` and match on
`name == "syft"`. Defensive parsing should also tolerate the legacy array shape
in case a future/older syft downgrades the spec version.

### Representative `components[]` element

```json
{
  "bom-ref": "pkg:apk/alpine/alpine-baselayout@3.6.5-r0?arch=aarch64&distro=alpine-3.20.10&package-id=8d645c7d2c9ab6eb",
  "type": "library",
  "publisher": "Natanael Copa <ncopa@alpinelinux.org>",
  "name": "alpine-baselayout",
  "version": "3.6.5-r0",
  "description": "Alpine base dir structure and init scripts",
  "licenses": [{ "license": { "id": "GPL-2.0-only" } }],
  "cpe": "cpe:2.3:a:alpine-baselayout:alpine-baselayout:3.6.5-r0:*:*:*:*:*:*:*",
  "purl": "pkg:apk/alpine/alpine-baselayout@3.6.5-r0?arch=aarch64&distro=alpine-3.20.10",
  "externalReferences": [ ... ],
  "properties": [
    { "name": "syft:package:foundBy", "value": "apk-db-cataloger" },
    { "name": "syft:package:type", "value": "apk" }
  ]
}
```

### Representative `dependencies[]` element

```json
{
  "ref": "pkg:apk/alpine/alpine-baselayout@3.6.5-r0?...&package-id=8d645c7d2c9ab6eb",
  "dependsOn": [
    "pkg:apk/alpine/alpine-baselayout-data@3.6.5-r0?...&upstream=alpine-baselayout",
    "pkg:apk/alpine/busybox-binsh@1.36.1-r31?...&upstream=busybox"
  ]
}
```

---

## 4. trufflehog — NDJSON, finding fields, exit codes — RESOLVED (with caveats)

Command:
`trufflehog docker --image <ref> --json --no-update`

- **`--no-update` → CONFIRMED accepted** (the help lists `--[no-]no-update`,
  "Don't check for updates"). No error; recommended in CI to avoid the
  self-update network call.
- **`--json` emits NDJSON → CONFIRMED.** One JSON object per line; each line is
  independently parseable (whole-stream `json.load` fails — must split on
  newlines). Findings go to **stdout**; logs (info/error) go to **stderr** as
  their own JSON lines.
- **Clean image (alpine:3.20):** zero findings → **empty stdout, exit 0**.
  stderr's final log line reports `verified_secrets:0, unverified_secrets:0`.

### ⚠️ EXIT CODE — the critical fact

| Scenario                         | `--fail` flag | Exit code |
| -------------------------------- | ------------- | --------- |
| No secrets found                 | (any)         | **0**     |
| Secrets found, **no** `--fail`   | absent        | **0** ⚠️  |
| Secrets found, **with** `--fail` | present       | **183**   |

- **trufflehog exits 0 even when secrets ARE found, unless `--fail` is passed.**
  By default it just prints the findings and exits 0. To make exit code signal
  "secrets found", **`--fail` is required** (exit **183**, exactly as the plan
  guessed for the secrets-present case).
- There is also `--fail-on-scan-errors` (exit non-zero if a scan error occurs)
  and `--no-verification` / `--results=` to control verification.
- **Plan impact:** the secret analyzer must **not** rely on a non-zero exit to
  detect findings by default. Either (a) parse stdout NDJSON and count lines
  (robust, recommended — works regardless of `--fail`), or (b) pass `--fail` and
  treat exit 183 as "secrets found" / 0 as "clean" / other as error. Parsing
  stdout is safer because a private-registry pull failure (see caveat below)
  also yields exit 0 with empty stdout — indistinguishable from "clean" unless
  you also inspect stderr.

### Finding fields — CONFIRMED + extras

Top-level keys of a finding object: `SourceMetadata`, `SourceID`, `SourceType`,
`SourceName`, `DetectorType`, `DetectorName`, `DetectorDescription`,
`DecoderName`, `Verified`, `VerificationFromCache`, `Raw`, `RawV2`, `Redacted`,
`ExtraData`, `StructuredData`.

The plan's expected fields all present: `DetectorName` (e.g. `"AWS"`),
`Verified` (bool — `false` for unverified), `Redacted` (the masked secret, e.g.
`"AKIA5XYZ…"`), `Raw` (the raw secret string), `SourceMetadata`. Plus useful
extras: `DetectorDescription`, `ExtraData` (detector-specific, e.g. AWS account
ID + resource type), `RawV2`.

`SourceMetadata.Data.Docker` = `{ image, tag, layer (sha256), file }`. For a
secret baked via a `RUN echo …` Dockerfile instruction, `file` was
`image-metadata:history:0:created-by` (trufflehog scans image history/config,
not just the layer filesystem) — worth noting for how findings are located.

Representative finding (from the throwaway secret image; `Raw`/`RawV2` redacted):

```json
{
  "SourceMetadata": {
    "Data": {
      "Docker": {
        "file": "image-metadata:history:0:created-by",
        "image": "th-secret-test",
        "layer": "sha256:3f26bc2d…",
        "tag": "latest"
      }
    }
  },
  "SourceID": 1,
  "SourceType": 4,
  "SourceName": "trufflehog - docker",
  "DetectorType": 2,
  "DetectorName": "AWS",
  "DetectorDescription": "AWS (Amazon Web Services) ...",
  "DecoderName": "PLAIN",
  "Verified": false,
  "VerificationFromCache": false,
  "Raw": "<REDACTED>",
  "RawV2": "<REDACTED>",
  "Redacted": "AKIA…",
  "ExtraData": { "account": "…", "resource_type": "Access key" },
  "StructuredData": null
}
```

### ⚠️ CAVEAT — `--image` source resolution (local vs registry)

`trufflehog docker --image <ref>` interprets `<ref>` as follows (from
`trufflehog docker --help`):

- `file://<path>` → local tarball (`docker save` output).
- `docker://<ref>` → **the local Docker daemon**.
- otherwise → **a remote registry is assumed.**

A bare tag like `th-secret-test:latest` was treated as a _registry_ ref and
trufflehog tried to pull `index.docker.io/library/th-secret-test` → 401
UNAUTHORIZED, scanned 0 bytes, **exited 0** (silent miss). The same fake-secret
image scanned correctly only after prefixing `docker://`.

This is the opposite of grype/syft, where a bare tag defaults to the **local
Docker daemon**. **Plan impact:** the secret analyzer must pass
`--image docker://<ref>` for local images (or `file://` for a tarball). For a
remote private registry, use the bare ref + auth (below). Also: combine with
`--fail-on-scan-errors` so a pull/auth failure isn't silently swallowed as
"clean".

---

## 5. Registry credentials — RESOLVED (⚠️ env-var prefix discrepancy)

### grype & syft — both use the `SYFT_REGISTRY_AUTH_*` prefix

The plan assumed grype reads `GRYPE_REGISTRY_AUTH_USERNAME` /
`GRYPE_REGISTRY_AUTH_PASSWORD`. **That is wrong.** grype embeds syft/stereoscope
for image sourcing and does **not** expose any `GRYPE_REGISTRY_AUTH_*` variable
(`grype config | grep GRYPE_REGISTRY_AUTH` → 0 hits). Both tools share:

| Purpose         | Env var (grype **and** syft)      |
| --------------- | --------------------------------- |
| registry host   | `SYFT_REGISTRY_AUTH_AUTHORITY`    |
| username        | **`SYFT_REGISTRY_AUTH_USERNAME`** |
| password        | **`SYFT_REGISTRY_AUTH_PASSWORD`** |
| token (alt)     | `SYFT_REGISTRY_AUTH_TOKEN`        |
| TLS client cert | `SYFT_REGISTRY_AUTH_TLS_CERT`     |
| TLS client key  | `SYFT_REGISTRY_AUTH_TLS_KEY`      |

grype _does_ expose a few `GRYPE_REGISTRY_*` knobs that are **not** auth:
`GRYPE_REGISTRY_INSECURE_SKIP_TLS_VERIFY`, `GRYPE_REGISTRY_INSECURE_USE_HTTP`,
`GRYPE_REGISTRY_CA_CERT`. But for **basic auth username/password**, the var
names are `SYFT_REGISTRY_AUTH_USERNAME` / `SYFT_REGISTRY_AUTH_PASSWORD` for both
binaries. syft, naturally, uses the same `SYFT_REGISTRY_AUTH_*` set.

**Plan impact:** set `SYFT_REGISTRY_AUTH_USERNAME` /
`SYFT_REGISTRY_AUTH_PASSWORD` (and optionally `SYFT_REGISTRY_AUTH_AUTHORITY` =
the registry host) for **both** grype and syft subprocess calls. Do **not** use
a `GRYPE_REGISTRY_AUTH_*` prefix — it has no effect.

### trufflehog — no `*_REGISTRY_AUTH_USERNAME/PASSWORD` env pair

trufflehog `docker` authenticates differently (no basic user/pass env pair):

- `--token` / env `$DOCKER_TOKEN` — a Docker **bearer token**.
- `--registry-token` — registry access token (for private images in a
  `--namespace`).
- `--namespace` — org/user, with registry host for non-Docker-Hub
  (e.g. `ghcr.io/namespace`).
- For local images it reads the daemon via `docker://` (no auth needed) and will
  honor the normal Docker credential resolution for remote pulls.

**Plan impact / recommended approach for private registries:** simplest, most
uniform path is to **avoid trufflehog's remote pull entirely** — pull/scan the
image locally (`--image docker://<ref>`) or export a tarball and use
`--image file://<tarball>`. That sidesteps trufflehog's divergent auth model and
matches how regctl/grype/syft already have the image available. If a remote pull
is unavoidable, wire `DOCKER_TOKEN` / `--registry-token` + `--namespace`.

---

## Summary of discrepancies vs the plan's assumptions

1. **grype/syft registry auth env vars are `SYFT_REGISTRY_AUTH_USERNAME` /
   `SYFT_REGISTRY_AUTH_PASSWORD` for BOTH tools** — not the assumed
   `GRYPE_REGISTRY_AUTH_*`. grype has no `GRYPE_REGISTRY_AUTH_*` var at all.
2. **syft version lives at `metadata.tools.components[]`** (object → `components`
   array), not a flat `metadata.tools[]` array. CycloneDX `specVersion` is 1.6.
3. **grype `fix.state` emits `""` (empty)** for the unknown case in real output,
   alongside `fixed`/`not-fixed`/`wont-fix`. The literal `unknown` is in grype's
   advertised vocabulary (`--ignore-states`) but the JSON used `""`. Normalize.
4. **trufflehog exits 0 even when secrets are found** unless `--fail` is passed
   (then exit **183**). Prefer parsing stdout NDJSON line count over relying on
   exit code.
5. **trufflehog `--image <bare-tag>` assumes a REMOTE registry**, unlike
   grype/syft which default to the local daemon. Use `--image docker://<ref>`
   for local images; a failed remote pull silently yields exit 0 / empty stdout.
6. trufflehog uses `--version` (flag), while grype/syft use the `version`
   sub-command. All three print to **stdout**.
