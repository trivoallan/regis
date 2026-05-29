# regctl probe notes — locking down output shapes

- **Date:** 2026-05-29
- **regctl version:** v0.11.5 (`darwin/arm64`, VCSRef `2bc542b`)
- **Probe image:** `docker.io/library/alpine:3.20` (multi-arch index), plus
  `docker.io/library/nginx:1.27` for a richer config blob.
- **Fixtures captured:** `tests/fixtures/regctl/`

These answers resolve the spec's Open Questions and lock the command strings and
parsing for the implementation tasks.

## Resolved Open Questions

### Q1 — Docker Hub host handling → RESOLVED, no normalization needed at the tool level

`regctl manifest get docker.io/library/alpine:3.20 …` and
`regctl tag ls docker.io/library/alpine` both work directly. No `docker://`
prefix; no `registry-1.docker.io` rewrite required for regctl. The
`image_ref()` helper still normalizes `registry-1.docker.io → docker.io`
defensively (some `RegistryClient`s carry that host), which is harmless.

### Q2 — `image inspect` field coverage → RESOLVED

`regctl image inspect <ref> --platform <os/arch>` **with no `--format`** already
emits valid JSON (the OCI image config). Top-level keys:
`architecture`, `os`, `created`, `config`, `history`, `rootfs`.

- `created` — top-level (e.g. `2026-04-16T23:53:26.803599608Z`).
- `architecture` / `os` — top-level.
- `config.User` — `null` when unset → analyzer maps to `""`.
- `config.Env` — list of `KEY=VALUE` strings.
- `config.ExposedPorts` — dict like `{"80/tcp": {}}` (nginx) or `null` (alpine)
  → analyzer maps to `list(keys())` → `["80/tcp"]` / `[]`.
- `config.Labels` — dict (nginx: `{"maintainer": "…"}`) or `null` →
  analyzer maps to `… or {}`.
- `history` — list of `{created, created_by, comment?}` (used by hadolint).

**Plan impact:** drop the `--format '{{jsonPretty .}}'` flag from every
`image inspect` call — the default output is already JSON. (Simpler subprocess
args, no Go-template quoting.)

### Q4 — `regctl version` for doctor → RESOLVED

`regctl version` (no `--`) exits 0 and prints to stdout. First line:
`VCSTag:     v0.11.5`. doctor's `_get_version` takes `splitlines()[0]`, so it
shows the `VCSTag:` line. Use `("regctl", "version")` in `_REQUIRED_TOOLS`.

### Q5 — `tag ls` pagination → RESOLVED (for this size)

`regctl tag ls docker.io/library/alpine` returned 214 tags as newline-separated
plain text (one tag per line). `splitlines()` parses it. No pagination flag
needed at this scale; very large repos untested but regctl handles paging
internally.

### Q6 — `RepoTags` semantics (versioning) → RESOLVED

skopeo's `inspect.RepoTags` is the full repository tag list — the same data
`regctl tag ls <repo>` returns. versioning can derive `repo_tags`/`aliases`
from the single `tag ls` call and drop the second registry call. ✓

### Q3 — comma-in-password → unchanged

Not exercised by public images. The wrapper's design stands: inline `--host`
for comma-free creds, temp `DOCKER_CONFIG` fallback otherwise.

## New finding — attestation manifests must be filtered (multi-arch)

`manifest get … --format raw-body` on the index returns
`mediaType: application/vnd.oci.image.index.v1+json` with **16** `manifests`
entries: **8 real platforms + 8 buildkit attestation manifests**. Attestations
have `platform: {os: "unknown", architecture: "unknown"}` and annotation
`vnd.docker.reference.type: attestation-manifest`.

The **old skopeo code did not filter these** (it iterated all entries), so
`platforms-count` would have over-counted. Since the `oci` analyzer is being
rewritten and the schema redesigned, the rewrite **filters out entries whose
`platform.os`/`platform.architecture` is missing or `"unknown"`** before
fan-out. Filter confirmed to isolate exactly the 8 real platforms.

**Plan impact:** Task 4 `analyze()` multi-arch branch adds:
```python
entries = [
    e for e in manifest.get("manifests", [])
    if (e.get("platform", {}).get("architecture") not in (None, "unknown"))
    and (e.get("platform", {}).get("os") not in (None, "unknown"))
]
```

## Confirmed command strings (final)

| Purpose | Command (args after `regctl [--host …]`) |
| --- | --- |
| raw index / raw manifest | `manifest get <ref> --format raw-body` |
| per-platform manifest (layers, sizes) | `manifest get <ref> --platform <os/arch> --format raw-body` |
| per-platform config blob | `image inspect <ref> --platform <os/arch>` (no `--format`) |
| tag list | `tag ls <registry>/<repo>` (newline text) |
| version (doctor) | `version` |

Digest refs work for both `image inspect` and `manifest get`
(`<registry>/<repo>@sha256:…`); adding `--platform` alongside a digest ref is
accepted (no conflict).
