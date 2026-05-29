# Design — Replace skopeo with regctl

- **Date:** 2026-05-29
- **Status:** Approved for planning
- **Driver:** Docker image size (drop the skopeo apt layer — the remaining size
  dominator per `docs/memory-bank/progress.md`) **and** behaviour/maintenance
  (cleaner auth model, fewer moving parts).
- **Decision:** Replace the `skopeo` external binary with **`regctl`**
  (regclient/regclient). Rename the analyzer slug `skopeo` → **`oci`**.
  Redesign the analyzer output schema. This is a **breaking change**.

## 1. Why regctl (vs crane, vs static skopeo)

Three Go-binary candidates were compared on the dimensions that matter to Regis
(see the brainstorm transcript for the full table). Summary:

| Criterion                                      | Winner                                                                                          |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Disk footprint (primary driver)                | **regctl** — ~12 MB bare binary vs crane's ~40 MB uncompressed (from a 16.5 MB tarball)         |
| Inline per-command credentials / thread-safety | **regctl** — `--host "reg=…,user=…,pass=…"` maps 1:1 to skopeo `--creds`; no shared login state |
| Single-shot `image inspect`                    | **regctl** — fewer subprocess calls per platform                                                |
| Future OCI 1.1 (referrers / SBOM discovery)    | **regctl**                                                                                      |
| Bus factor / ecosystem                         | crane (Google-backed) — the one axis where crane wins                                           |
| Multi-arch / `--platform`, output parsing      | tie                                                                                             |

Static skopeo was rejected: upstream actively refuses to ship static binaries
(libgpgme/CGO), leaving only a single-maintainer third-party distributor or a
DIY Go build in CI — fragility for no upside over regctl.

regctl is chosen because it wins the primary driver (size) **and** fits Regis's
parallel `ThreadPoolExecutor` + inline-credentials architecture better than
crane. The bus-factor concern is accepted as a tradeoff.

Verified versions at design time: regctl `v0.11.5`, crane `v0.21.6`.

## 2. Scope

Two call sites use skopeo today; both are rewritten:

- `regis/analyzers/skopeo.py` → renamed to `regis/analyzers/oci.py`
  (`SkopeoAnalyzer` → `OciAnalyzer`). Uses `inspect --raw` (index detection),
  `inspect` (+ `--override-os/--override-arch`), `inspect --config` (the `User`
  field), and `list-tags`.
- `regis/analyzers/freshness.py` — uses `inspect --config --override-os linux
--override-arch amd64` to read `created`. Rewritten to call regctl; **kept as
  a separate analyzer** (the chosen scope was "evaluate the tools honestly", not
  "consolidate freshness into the inspect analyzer").

A shared subprocess wrapper is introduced so the credential injection and
`FileNotFoundError` handling live in exactly one place:

- **New module `regis/utils/regctl.py`** exposing
  `run_regctl(client: RegistryClient, args: list[str]) -> str`.
  Both analyzers call it. This factors only the process invocation — it does not
  merge the analyzers.

## 3. Command mapping

| skopeo call today                            | regctl replacement                                                                                                                                                                   |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `skopeo inspect --raw <ref>`                 | `regctl manifest get <ref> --format raw-body`                                                                                                                                        |
| `skopeo inspect <ref>` (+ os/arch overrides) | `regctl image inspect <ref> --platform <os/arch>` → OCI config blob: `created`, `config.Labels`, `config.User`, `config.Env`, `config.ExposedPorts`, `architecture`, `os`, `variant` |
| `skopeo inspect --config` (User field)       | absorbed by `image inspect` above — the separate `--config` call is no longer needed                                                                                                 |
| layer count + size                           | `regctl manifest get <ref> --platform <os/arch>` → `layers[]` (count + `size`) and `config.size`                                                                                     |
| `skopeo list-tags docker://<repo>`           | `regctl tag ls <repo>` → default newline-per-tag output, parsed with `splitlines()`                                                                                                  |

### Per-platform call count

skopeo today makes **2 calls per platform** (`inspect` + `inspect --config`).
regctl makes **2 calls per platform**: `image inspect` (config: user/env/ports/
labels/created/os/arch) and `manifest get` (layers count, sizes, platform
digest). Net-neutral on call count; the multi-arch fan-out
(`ThreadPoolExecutor` over index entries) is preserved unchanged.

Layer digests/sizes and the platform manifest digest come from the **manifest**,
not the config — hence the manifest call is still required per platform.

### Reference format

regctl takes refs as `registry/repo:tag` (or `registry/repo@sha256:…`) with **no
`docker://` scheme prefix**. The current `docker://` prefixing is removed.
regctl normalizes Docker Hub internally; the existing
`registry-1.docker.io → docker.io` workaround is expected to be unnecessary but
will be confirmed during implementation (see Open Questions).

## 4. Authentication

`run_regctl` injects credentials inline, per command, which is thread-safe and
maps 1:1 to skopeo's `--creds`:

```sh
regctl --host "reg=<client.registry>,user=<username>,pass=<password>" <subcommand> …
```

- When `client.username`/`client.password` are absent: omit `--host`; regctl
  falls back to anonymous access and `~/.docker/config.json`. The existing
  `DOCKER_AUTH_CONFIG` flow (`regis/registry/auth.py`) continues to work because
  regctl reads the Docker config automatically.
- No `regctl registry login` step and no shared mutable config file — each
  worker thread passes its own `--host` string.

**Edge case (flagged):** regctl's `--host` value is comma-separated `key=val`
pairs, so a password containing a comma would break parsing. Mitigation decided
during implementation: if a credential contains a comma, fall back to a
per-invocation `REGCTL_CONFIG` pointing at a generated config file, or
`registry login --pass-stdin` into a temp config dir. The common case
(comma-free tokens) uses the inline `--host` form.

## 5. Schema redesign (`oci`)

The analyzer output schema is redesigned (chosen: "free to redesign"). File
renamed `regis/schemas/analyzer/skopeo.schema.json` →
`regis/schemas/analyzer/oci.schema.json`; `title`/`const`/`$id` updated to
`oci`.

Changes vs the current schema:

- **Fix the latent bug:** the current schema's `platforms[]` items omit `size`,
  `exposed_ports`, and `env`, yet the rules reference them (they pass only
  because `additionalProperties` is not `false` on the item). The new schema
  declares them explicitly:
  - `size` (integer, bytes — `config.size` + Σ `layers[].size`)
  - `exposed_ports` (array of strings)
  - `env` (array of strings)
  - alongside the existing `architecture`, `os`, `variant`, `digest`,
    `created`, `labels`, `layers_count`, `user`.
- **Drop the raw `inspect` dump** (skopeo-specific blob) in favour of the
  normalized per-platform fields. The top-level `inspect` object is removed.
- Keep top-level `analyzer` (= `"oci"`), `repository`, `tag`, `platforms`,
  `tags`.

## 6. Naming / rename (`skopeo` → `oci`)

The analyzer slug becomes tool-agnostic so a future tool swap needs no further
rename. Touch points:

- `pyproject.toml` entry point: `skopeo = …:SkopeoAnalyzer` →
  `oci = regis.analyzers.oci:OciAnalyzer`.
- `regis/analyzers/oci.py`: `name = "oci"`, `schema_file = "analyzer/oci.schema.json"`.
- `default_rules()` JSON Logic paths: `results.skopeo.*` → `results.oci.*`
  (all 8 rules). **Rule slugs are unchanged** — they are already tool-agnostic
  (`user-blacklist`, `max-size`, `layers-count`, `tag-blacklist`,
  `platforms-count`, `exposed-ports-whitelist`, `required-labels`,
  `env-blacklist`).
- `regis/playbooks/default/playbook.yaml`: `provider: skopeo` → `provider: oci`
  (2 occurrences).
- Dashboard: `apps/dashboard/src/components/AnalyzerSection.tsx` and
  `Dashboard/AnalyzerCoverageCard.tsx` references to `skopeo`.
- `regis/rules/evaluator.py`: the `env_contains` doc-comment example path.
- Docs: rename `docs/website/docs/reference/rules/skopeo/` → `…/rules/oci/`,
  update `results.skopeo.*` in `concepts/playbooks.md`, `concepts/rules.md`, the
  analyzer reference, schema reference, troubleshooting, custom-playbook, and
  the `create-playbook` skill's reference list.
- **Frozen:** `docs/website/versioned_docs/version-v0.31.0/**` are immutable
  snapshots — not touched.

## 7. Dockerfile & tooling

- **`tools-fetcher` stage:** add regctl using the bare-binary pattern (same as
  hadolint — download + `chmod +x`, no tar):
  ```dockerfile
  ARG REGCTL_VERSION
  RUN case "$TARGETARCH" in \
        amd64|arm64) regctl_arch="$TARGETARCH" ;; \
        *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
      esac && \
      curl -sSfL "https://github.com/regclient/regclient/releases/download/v${REGCTL_VERSION}/regctl-linux-${regctl_arch}" \
        -o /tools/regctl && \
      chmod +x /tools/regctl
  ```
  (asset names: `regctl-linux-amd64`, `regctl-linux-arm64`).
- **Final stage:** `COPY --from=tools-fetcher /tools/regctl /usr/local/bin/regctl`.
- **Remove `skopeo`** from the runtime apt install (`Dockerfile:113`); keep
  `ca-certificates`. This is the size win.
- Define `ARG REGCTL_VERSION` (pinned) alongside the existing
  `HADOLINT_VERSION`/`DOCKLE_VERSION` args; wire it into the build args / CI as
  those are.

## 8. Doctor & install docs

- `regis/commands/doctor.py`: `_REQUIRED_TOOLS` — replace `("skopeo",
"--version")` with `("regctl", "version")` (regctl uses `version`, not
  `--version` — confirm exact invocation during implementation).
- Remove `skopeo` and add `regctl` to the "required external binaries on PATH"
  lists: `CLAUDE.md`, project README, docs site install/usage pages, and the
  `create-playbook` skill.

## 9. Tests

Rewrite the subprocess mocks from skopeo CLI shapes to regctl outputs:

- `tests/test_skopeo_analyzer.py` + `tests/test_analyzer_skopeo.py` → renamed to
  `test_oci_analyzer.py` (consolidate if they overlap); mock `run_regctl` /
  regctl JSON outputs.
- `tests/test_versioning.py`, `tests/test_size.py` — update any skopeo-output
  fixtures they depend on.
- `tests/commands/test_doctor.py` — expect `regctl` instead of `skopeo`.
- `tests/test_analyzers.py`, `tests/test_coverage_*` — update analyzer-name
  references (`skopeo` → `oci`) and patch targets.
- Patch targets follow the project rule: patch at the new module location
  (`regis.utils.regctl.subprocess`, `regis.analyzers.oci.*`,
  `regis.analyzers.freshness.*`), not `regis.cli.*`.
- Maintain ≥ 90 % coverage (full-suite gate).

## 10. Versioning & rollout

- **Breaking change.** Conventional commit `feat(analyzers)!:` (or
  `build(deps)!` for the Dockerfile portion if split). `bump-minor-pre-major`
  keeps it at 0.32.x → **0.33.0** (not 1.0.0).
- **No backward-compat alias** for `results.skopeo.*` or `provider: skopeo`
  (consistent with "free to redesign" + pre-v1). Migration is documented: users
  with custom playbooks change `provider: skopeo` → `provider: oci` and any
  custom rules referencing `results.skopeo.*` → `results.oci.*`.
- Consider the `whats-new` label on the PR (user-facing breaking change); the
  `## Summary` is harvested into the What's New page.

## 11. Open questions (confirm during implementation)

1. **Docker Hub host handling** — verify regctl accepts `docker.io/library/...`
   and whether the `registry-1.docker.io → docker.io` normalization is still
   needed.
2. **`regctl image inspect` field coverage** — confirm the config blob exposes
   `config.ExposedPorts`, `config.Env`, `config.Labels`, `config.User` in the
   expected shape across registries; confirm `--platform` resolution on
   single-arch vs index images.
3. **Comma-in-password** — decide the fallback path (per-invocation
   `REGCTL_CONFIG` file vs `registry login --pass-stdin`) and implement it.
4. **`regctl version` exit code/format** — confirm the doctor invocation.
5. **`tag ls` pagination** — confirm regctl returns the full tag list (or how to
   page) for large repositories.
