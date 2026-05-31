---
sidebar_position: 9
tags:
  - tools
  - cache
  - air-gapped
---

# Managing Analyzer Tools

The default `regis:latest` image is **slim** — only the regis CLI and `regctl` are baked in. Scanner binaries (`grype`, `syft`, `trufflehog`, `hadolint`, `dockle`) are downloaded on first use to a local cache, verified against pinned sha256s (and cosign signatures when available).

## When are tools fetched?

- **Lazy** (default): the first analyzer that needs a tool downloads it, verifies its sha256 (and cosign signature when the manifest declares one), and caches it under `$XDG_CACHE_HOME/regis/tools/`.
- **Explicit pre-warm**: run `regis bootstrap tools` (recommended in CI for clean logs and predictable timing).
- **Status check**: `regis bootstrap tools --check` or `regis doctor`.

## Cache location

Resolved in order:

1. `$REGIS_CACHE_DIR` (explicit override)
2. `$XDG_CACHE_HOME/regis/tools/`
3. `~/.cache/regis/tools/`

Layout: `<cache>/<tool>/<version>/linux-<arch>/<tool>`.

## Air-gapped environments

Two options:

1. **Pull the full image** — `ghcr.io/trivoallan/regis:latest-full` bakes all scanners in (≈ 484 MB). Use this when the build environment cannot reach `github.com/releases`.
2. **Configure a local mirror** — set `REGIS_TOOLS_MIRROR` to a base URL serving `<mirror>/<tool>/<version>/<tool>_<version>_linux_<arch>{ext}`. The lazy fetcher consults the mirror instead of GitHub.

## Environment variables

| Variable               | Effect                                                   |
| :--------------------- | :------------------------------------------------------- |
| `REGIS_CACHE_DIR`      | Override cache root.                                     |
| `REGIS_TOOLS_MIRROR`   | Base URL alternative to GitHub releases.                 |
| `REGIS_OFFLINE`        | `1` → never fetch over the network; cache-only.          |
| `REGIS_REQUIRE_COSIGN` | `1` → fail when cosign verification cannot be performed. |

## Signature verification

When the `cosign` binary is on `$PATH` and the manifest declares an issuer/identity for a tool, regis runs `cosign verify-blob` against the signature published next to the release URL. Best-effort by default — install cosign and set `REGIS_REQUIRE_COSIGN=1` to enforce.

## CI cache examples

### GitHub Actions

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/regis/tools
    key: regis-tools-${{ hashFiles('regis/tools/manifest.yaml') }}
- run: |
    docker run -v "$HOME/.cache/regis:/home/regis/.cache/regis" \
      ghcr.io/trivoallan/regis:latest analyze $IMAGE
```

### GitLab CI

```yaml
cache:
  key:
    files: [regis/tools/manifest.yaml]
  paths: [.regis-cache/]
script:
  - docker run -v "$PWD/.regis-cache:/home/regis/.cache/regis" \
    ghcr.io/trivoallan/regis:latest analyze $IMAGE
```

## Image variants

| Tag                             | Base               | Size     | Use case                                |
| :------------------------------ | :----------------- | :------- | :-------------------------------------- |
| `:latest`, `:VERSION`           | python:3.11-alpine | ≈ 156 MB | Default — networked CI, dev             |
| `:latest-full`, `:VERSION-full` | python:3.11-alpine | ≈ 484 MB | Air-gapped or rate-limited environments |

Both run as `regis:1001`. To debug the slim image, use Alpine's bundled BusyBox shell:

```bash
docker run --rm -it --entrypoint /bin/sh ghcr.io/trivoallan/regis:latest
```
