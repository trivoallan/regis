# Image-size reduction — round 3: lazy-loaded scanner binaries + distroless runtime

**Date**: 2026-05-31
**Status**: Draft (brainstorm validated)
**Sprint**: 1 (19 mai → 2 juin 2026)
**Successor of**: round 2 (`docs/memory-bank/activeContext.md` [2026-05-29], deferred items)

## Context

After PR #620 (`feat(analyzer)!: replace trivy with grype/syft/trufflehog`) the runtime image regressed by ~114 MiB. Measured amd64 size: **~372 MiB** (CI ceiling raised from 220 MB → 385 MB). The three new Go binaries dominate:

| Component                 | Size (amd64, extracted) |
| ------------------------- | ----------------------- |
| grype + syft + trufflehog | ~260 MB                 |
| `python:3.14-slim` base   | ~80 MB                  |
| python build artefacts    | ~38 MB                  |
| venv (regis + deps)       | ~29 MB                  |
| dockle                    | ~25 MB                  |
| regctl                    | ~12 MB                  |

Round 2 (#608) already pulled the obvious low-hanging fruit (git/jq removed, FastAPI/Uvicorn made optional, venv `__pycache__` pruning). Going further requires architectural changes.

## Goal

**Get the default published image under 200 MB extracted (amd64)** without amputating any feature.

## Approach (chosen out of 4 options)

**Lazy load scanner binaries at runtime**, ship two image variants:

- **`regis:0.33.0` (slim, also `:latest`)** — Python+regis+regctl baked, all other scanners fetched on demand to a cache. Target ~110-120 MB.
- **`regis:0.33.0-full` (also `:latest-full`)** — current behaviour, all scanners baked. Target unchanged ~370 MB.

Switch runtime base from `python:3.14-slim` (~80 MB Debian) to **`gcr.io/distroless/python3-debian12:nonroot`** (~25 MB, Python 3.11, glibc, no shell). Project requires `python>=3.10` (pyproject.toml) so the downgrade is compatible.

**Lazy fetch is the dominant lever** (~260 MB saved). The distroless switch adds ~50 MB more and aligns image surface with security-tool hygiene. Both decisions stand on their own; the lazy fetch alone already clears the target.

### Rejected alternatives

| Option                       | Reason rejected                                                                                                   |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| UPX-pack scanners in place   | User chose lazy-load instead (cleaner separation, avoids UPX startup cost on every scan, no SBOM opacity concern) |
| Chainguard Wolfi base        | Free tier ships only `:latest` (no fixed tags) → reproducibility regression; vendor lock-in on cgr.io             |
| `python:3.14-alpine` (musl)  | Risk on Python wheels (cryptography, lxml via cffi)                                                               |
| Status quo + venv-prune only | Insufficient — cannot reach <200 MB while keeping 260 MB of Go binaries baked                                     |

## Architecture

### Two-variant build, one Dockerfile

Single Dockerfile, `--build-arg VARIANT=slim|full` selects the final stage.

```dockerfile
# syntax=docker/dockerfile:1.7
ARG VARIANT=slim

FROM node:25-slim AS frontend-builder        # unchanged
FROM python:3.11-slim AS python-builder      # was 3.14-slim — ABI-aligned with distroless runtime
FROM curlimages/curl:8.10.1 AS tools-fetcher # unchanged (still always built; copies are conditional)

FROM gcr.io/distroless/python3-debian12:nonroot AS final-slim
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/regctl /usr/local/bin/regctl
ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    REGIS_VARIANT=slim \
    HOME=/home/nonroot
WORKDIR /home/nonroot
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["regis", "list"]
ENTRYPOINT ["regis"]
CMD ["--help"]

FROM gcr.io/distroless/python3-debian12:nonroot AS final-full
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/grype     /usr/local/bin/grype
COPY --from=tools-fetcher /tools/syft      /usr/local/bin/syft
COPY --from=tools-fetcher /tools/trufflehog /usr/local/bin/trufflehog
COPY --from=tools-fetcher /tools/hadolint  /usr/local/bin/hadolint
COPY --from=tools-fetcher /tools/dockle    /usr/local/bin/dockle
COPY --from=tools-fetcher /tools/regctl    /usr/local/bin/regctl
ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    REGIS_VARIANT=full \
    HOME=/home/nonroot
WORKDIR /home/nonroot
ENTRYPOINT ["regis"]
CMD ["--help"]

FROM final-${VARIANT} AS final
```

**Distroless notes**:

- No shell, no apt. Healthcheck uses exec form (`CMD ["regis", "list"]`); Docker treats non-zero exit as unhealthy automatically.
- User is `nonroot:nonroot` (uid 65532) instead of the current `regis:1001` — **breaking change for any user mounting volumes with explicit ownership**.
- `ca-certificates` shipped by distroless; the `apt-get install` step disappears from the runtime layer.
- Pin the base image by **digest** in the Dockerfile (not tag) for reproducibility; monthly bump via CI workflow.
- Optional `:0.33.0-debug` variant based on `:debug` tag (busybox shell, ~5 MB extra) — decision deferred to writing-plans.

### Lazy fetch flow (slim only)

```text
analyzer.analyze()
    └─ ensure_tool('grype')
         ├─ tool on PATH? ─ yes ─→ return path  (full image, dev host)
         └─ no
              └─ ToolFetcher.ensure('grype')
                   ├─ cache hit + sha256 ok? ─ yes ─→ return path
                   └─ no
                        ├─ download from REGIS_TOOLS_MIRROR or manifest URL
                        ├─ verify sha256 (fail → ToolFetchError)
                        ├─ verify cosign (best-effort unless REGIS_REQUIRE_COSIGN)
                        ├─ atomic write to cache
                        └─ return path
```

Same analyzer code runs in slim, full, and dev environments: the fetcher is a no-op when the binary is already on PATH.

## Components

### 1. Tools manifest — `regis/tools/manifest.yaml`

Single source of truth for tool versions, URLs, and checksums.

```yaml
schema_version: 1
tools:
  grype:
    version: "0.112.0"
    url_template: "https://github.com/anchore/grype/releases/download/v{version}/grype_{version}_linux_{arch}.tar.gz"
    archive: tar.gz
    member: grype
    cosign:
      issuer: "https://token.actions.githubusercontent.com"
      identity_regex: "^https://github.com/anchore/grype/.+"
    sha256:
      amd64: "abc123..."
      arm64: "def456..."
  syft: { ... }
  trufflehog: { ... }
  hadolint:
    version: "2.12.0"
    url_template: "https://github.com/hadolint/hadolint/releases/download/v{version}/hadolint-Linux-{arch_alt}"
    archive: none
    arch_alt:
      amd64: x86_64
      arm64: arm64
    cosign: null # hadolint releases not signed
    sha256: { ... }
  dockle: { ... }
  regctl: { ... } # listed for bootstrap --all and -full builds; baked in slim
```

Validated at module import against `regis/schemas/tools-manifest.schema.json`.

### 2. Fetcher module — `regis/tools/fetcher.py`

```python
class ToolFetchError(RegisError): ...

class ToolFetcher:
    def __init__(
        self,
        cache_dir: Path | None = None,
        mirror: str | None = None,
        verify_cosign: bool = False,
        offline: bool = False,
    ) -> None: ...

    def ensure(self, name: str) -> Path:
        """Return local path; fetch if absent or stale."""

    def fetch_all(self, names: list[str] | None = None) -> dict[str, Path]: ...

    def status(self) -> list[ToolStatus]:
        """Per-tool: name, version, cached, path, sha256_ok."""
```

**Cache layout** (per-version, per-arch):

```text
$cache_dir/
  manifest.lock.json        # snapshot of versions resolved (audit trail)
  grype/0.112.0/linux-amd64/grype
  syft/1.44.0/linux-amd64/syft
  ...
```

**Cache resolution** (first match wins):

1. `$REGIS_CACHE_DIR`
2. `$XDG_CACHE_HOME/regis/tools/`
3. `~/.cache/regis/tools/`

**URL resolution**:

1. `$REGIS_TOOLS_MIRROR` → `{mirror}/{tool}/{version}/{tool}_{version}_linux_{arch}.tar.gz`
2. Manifest `url_template`

**Concurrency**: parallel `ensure()` calls from `ThreadPoolExecutor` workers serialized via `fcntl.flock` on `{path}.lock`.

**Atomic write**: download to `*.partial`, sha256 check, then `os.rename()` to final.

**Cosign**: best-effort. Binary present + manifest has cosign block → verify. Binary absent → log INFO, continue (or hard-fail if `REGIS_REQUIRE_COSIGN=1`).

### 3. Analyzer integration — `regis/utils/process.py`

New helper `ensure_tool(name) -> Path` complements `require_tool(name)`:

- If `name` in manifest → delegate to module-level `ToolFetcher`
- Else (or if on PATH) → fall back to current `require_tool` behaviour

Analyzers in `regis/analyzers/{cve,sbom,secrets,hadolint,dockle,oci}.py` switch their lookup to `ensure_tool` for the binaries they need.

### 4. CLI surface — `regis/commands/bootstrap.py`

New subcommand:

```bash
regis bootstrap tools                    # fetch all tools in manifest
regis bootstrap tools --analyzer cve     # fetch tools for one analyzer
regis bootstrap tools --tool grype       # fetch one specific tool
regis bootstrap tools --check            # validate cache without downloading
```

Output: one line per tool with ✓/✗/⏩ status, timing, bytes downloaded. Respects `--quiet`.

### 5. Doctor extension — `regis/commands/doctor.py`

New "Tools" section listing, per manifest entry:

- target version
- resolved path (cache hit / PATH hit / MISSING)
- sha256 ✓/✗ if cache hit
- cosign ✓/⏩/✗

### 6. Environment variables

| Var                    | Effect                                             |
| ---------------------- | -------------------------------------------------- |
| `REGIS_CACHE_DIR`      | Override cache root                                |
| `REGIS_TOOLS_MIRROR`   | Base URL alternative (air-gapped / internal proxy) |
| `REGIS_REQUIRE_COSIGN` | `1` → fail if cosign verification impossible       |
| `REGIS_OFFLINE`        | `1` → forbid any network fetch, cache-only         |

Added to the `REGIS_*` table in `docs/website/docs/usage/configuration.md`.

## CI/CD

### `cd-docker.yml` — matrix build

`strategy.matrix.variant: [slim, full]`. Buildx multi-arch (amd64+arm64). Tags published per release:

- `:0.33.0`, `:latest`, `:0.33.0-slim` (slim is the default)
- `:0.33.0-full`, `:latest-full`

SBOM via `anchore/sbom-action` attached to GitHub release for each variant (preserves PR #618 fix).

### `ci-image-size.yml` — per-variant gates

```yaml
strategy:
  matrix:
    variant: [slim, full]
    include:
      - variant: slim
        ceiling: 150MB
      - variant: full
        ceiling: 400MB
```

If slim exceeds 150 MB → investigate (likely a new baked dependency).

### New workflow `ci-tools-manifest.yml`

- Trigger: PR touching `regis/tools/manifest.yaml` + weekly schedule (`cron: '0 6 * * 1'`)
- Per tool: download URL, compute sha256, compare to manifest, fail on mismatch
- Best-effort cosign verification if block present
- Catches retracted releases, drift, tampering

### New workflow `ci-tools-fetch-smoke.yml`

- Build slim image, run `regis bootstrap tools --check` (cache empty → all MISSING)
- Run `regis bootstrap tools` (full download)
- Run `regis analyze` against a fixed test image (e.g. `alpine:3.20`)
- Annotate PR with cold-fetch duration + warm-analyze duration
- Detects fetcher runtime regressions (timeouts, sha drift, mirror breakage)

### Renovate / Dependabot

Custom regex manager on `manifest.yaml` proposes version bumps per tool. Semver versioning template. Major bumps require manual review.

## Tests

**Unit** (`tests/tools/`):

- `test_manifest.py`: schema, parsing, URL templating, arch resolution
- `test_fetcher.py`:
  - Cache hit / cache miss
  - sha256 mismatch → `ToolFetchError`, partial removed
  - Atomic write interruption → no corrupt file
  - Concurrent `ensure('grype')` from 2 threads → single download (flock)
  - `REGIS_TOOLS_MIRROR` overrides manifest URL
  - `REGIS_OFFLINE=1` + cache miss → error, no network attempt
  - Cosign absent + manifest signed → log INFO; with `REGIS_REQUIRE_COSIGN=1` → fail
- `test_ensure_tool.py`: tool already on PATH → bypass fetcher

Mocks via `responses` or `pytest-httpserver`. **No real network in local suite.**

**Integration** (`tests/integration/`):

- `test_lazy_load_e2e.py` (`slow`, `requires_network`): temp cache, minimal `regis analyze`, assert each used binary appears in cache
- Real smoke run in `ci-tools-fetch-smoke.yml` on the published slim image

**Coverage**: maintain ≥90% global; `fetcher.py` targets ~95% (security-critical path).

## Migration & breaking changes

| Audience                                    | Impact                                                                               | Mitigation                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `docker pull ghcr.io/.../regis:latest` user | `:latest` is now slim. First run +5-30 s for downloads (persistent cache via volume) | Release note + What's New entry                                      |
| Local dev (`pipenv run regis`)              | None (tools already on host PATH)                                                    | —                                                                    |
| GitHub Actions / GitLab CI user             | First job in ephemeral container re-downloads each run (~30 s)                       | Doc: mount `~/.cache/regis/tools` as CI cache, or use `:latest-full` |
| Air-gapped user                             | Slim variant broken                                                                  | Doc: use `:latest-full` or configure `REGIS_TOOLS_MIRROR`            |
| Volume-mount user (uid 1001)                | Ownership broken (new uid 65532)                                                     | Doc + Compose/Kubernetes examples                                    |

**Breaking changes** (Release Please will bump 0.32 → 0.33 with `bump-minor-pre-major: true`):

1. `:latest` no longer ships scanners by default (lazy fetch).
2. Runtime user uid 1001 → 65532 (distroless `nonroot`).
3. No shell in image — `docker run --entrypoint sh ...` broken (use `:debug` variant if published, or `:latest-full`).

**Communication**:

- `whats-new` label on the main PR → auto-generated What's New page
- Dedicated CHANGELOG section via Release Please (`feat!:` commit)
- README update with a "lazy by default" note

## Rollback plan

If a critical regression hits post-release:

1. Manual retag of `:latest` → `:latest-full` on ghcr.io (immediate)
2. Patch Dockerfile in the next version to make `full` the default until fix lands
3. User caches persist → no re-download after rollback

## Risks & mitigations

| Risk                                                                                        | Likelihood                     | Mitigation                                                                                                                 |
| ------------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Venv compiled on `python:3.11-slim` Debian 12 not runnable on `distroless/python3-debian12` | Low (same Debian/glibc/Python) | Day-0 POC: `docker build && docker run regis:slim regis list` before any other work                                        |
| Cold-start CI surprise (30 s download on first run)                                         | Medium                         | Doc: cache mount examples; recommend `-full` for short pipelines                                                           |
| GitHub releases availability / rate limits                                                  | Low                            | Retry with exponential backoff in fetcher; `REGIS_TOOLS_MIRROR` for self-hosted                                            |
| Cosign optional → users skip verification                                                   | Medium                         | Log INFO clearly; document `REGIS_REQUIRE_COSIGN=1` in security guide                                                      |
| Distroless debugging friction                                                               | Medium                         | Optional `:debug` variant (decision in writing-plans); document `docker run --entrypoint /busybox/sh ...:debug` if shipped |

## Out of scope

- UPX-packing remaining binaries (not needed once target is met)
- Switching builder stage off Debian (keep `python:3.11-slim` for max wheel compat)
- Custom-built `distroless/cc-debian12` + bundled Python 3.14 (deferred to a future sprint if <100 MB becomes a goal)
- Replacing or splitting analyzers (`regis` modularity is orthogonal to image size)

## Success criteria

- [ ] `regis:0.33.0` (slim, amd64) ≤ 150 MB extracted in CI
- [ ] `regis:0.33.0-full` (amd64) ≤ 400 MB extracted in CI
- [ ] `regis bootstrap tools` succeeds in <60 s in CI smoke job
- [ ] `regis analyze` end-to-end on `alpine:3.20` succeeds with empty cache (lazy fetch path)
- [ ] All sha256 in manifest verified by `ci-tools-manifest.yml` (initial + weekly)
- [ ] ≥90 % global coverage; ≥95 % on `regis/tools/fetcher.py`
- [ ] Air-gapped guide published (`docs/website/docs/usage/tools-management.md`)
- [ ] What's New entry + CHANGELOG breaking notice on release

## Next step

Hand off to `writing-plans` to produce the step-by-step implementation plan.
