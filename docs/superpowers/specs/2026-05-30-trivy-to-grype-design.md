# Replace Trivy with Grype + Syft + TruffleHog — Design

> **Status:** Approved design (brainstorming output). Next step: implementation
> plan via `superpowers:writing-plans`.
> **Date:** 2026-05-30
> **Author:** Tristan Rivoallan (with Claude)

## 1. Goal

Replace the single `trivy` external binary with three capability-focused tools:

- **grype** — CVE / vulnerability scanning
- **syft** — SBOM generation (CycloneDX)
- **trufflehog** — secret detection

The migration also corrects a naming-debt: analyzers are renamed from the tool
they wrap (`trivy`) to the **capability** they provide (`cve`, `secrets`,
`sbom`). This follows the pattern set by the just-merged `skopeo → oci` rename
(v0.32.0) and the existing `sbom` analyzer, which is already named after its
capability rather than its backend.

This is a **breaking change** (provider names and report variable prefixes
change). Pre-1.0, it bumps **0.32.0 → 0.33.0** via the existing
`bump-minor-pre-major: true` in `release-please-config.json`.

### Why capability-named providers

1. **Consistency** — `SbomAnalyzer` is already named after its capability;
   `TrivyAnalyzer` was the exception.
2. **Future-proofing** — swapping grype for another scanner later is a
   no-op for user playbooks.
3. **Decoupling** — today `TrivyAnalyzer` does CVE _and_ secrets in one pass.
   Splitting by capability lets `--skip secrets` work independently of
   `--skip cve`.

## 2. Scope

In scope:

- New `CveAnalyzer` (`name="cve"`, backend grype) — replaces the vuln half of
  `TrivyAnalyzer`.
- New `SecretsAnalyzer` (`name="secrets"`, backend trufflehog) — replaces the
  secrets half of `TrivyAnalyzer`.
- `SbomAnalyzer` (`name="sbom"`) — backend swapped trivy → syft, surface mostly
  unchanged.
- Delete `regis/analyzers/trivy.py`.
- Three thin wrappers: `regis/utils/{grype,syft,trufflehog}.py`.
- New output schemas: `cve.schema.json`, `secrets.schema.json`; updated
  `sbom.schema.json`. Delete `trivy.schema.json`.
- Default playbook, dashboard, docs, Dockerfile, `regis doctor`, CI updates.
- Tests (TDD with real fixtures from a spike).

Out of scope (YAGNI):

- A `regis playbook migrate` command. User migration is documented (manual
  find/replace) in the CHANGELOG / What's New note instead.
- Chaining grype to consume syft's SBOM (`grype sbom:<path>`). Analyzers stay
  **independent and parallel**, matching today's `ThreadPoolExecutor` model.
  Cost: grype re-catalogs the image (work syft also does), accepted for
  simplicity and robustness.

## 3. Architecture & components

```text
regis/analyzers/
  cve.py        # CveAnalyzer (name="cve")          backend grype
  secrets.py    # SecretsAnalyzer (name="secrets")  backend trufflehog  [NEW]
  sbom.py       # SbomAnalyzer (name="sbom")         backend syft (internal swap)
  trivy.py      # DELETED

regis/utils/
  grype.py       # _run_grype(image, creds, platform) -> dict        (grype JSON)
  syft.py        # _run_syft(image, creds, platform) -> dict          (CycloneDX-JSON)
  trufflehog.py  # _run_trufflehog(image, creds) -> list[dict]        (NDJSON -> list)
```

**Principles:**

- One utils wrapper per tool, mirroring `regis/utils/regctl.py`:
  `shutil.which` → credential injection → `subprocess.run` → parse →
  `AnalyzerError`. Unit-testable by patching `regis.utils.<tool>.subprocess`
  and `.shutil`.
- Each analyzer remains a `BaseAnalyzer` implementing
  `analyze` / `validate` / `default_rules`, registered via
  `project.entry-points."regis.analyzers"` in `pyproject.toml` as `cve`,
  `secrets`, `sbom`.
- Independent / parallel execution — no CVE↔SBOM coupling; the existing
  `ThreadPoolExecutor` (default 4 workers) is untouched. Each thread keeps its
  own `RegistryClient`.

**Credentials:** grype and syft both read registry auth from
`~/.docker/config.json` and tool-specific env vars. The wrappers inject
credentials following the same precedence as today (passed creds > env vars).
The exact env var names (`GRYPE_*` / `SYFT_*` vs Docker-standard
`REGISTRY_AUTH_*`) are confirmed by the spike (§8).

**TruffleHog image access:** `trufflehog docker --image <ref> --json` pulls via
the registry (no Docker daemon required), consistent with grype/syft. The spike
confirms the exact invocation and whether daemon access is needed.

## 4. Data flow & output schemas

Design rule: **keep business field names stable** (`critical_count`,
`fixed_count`, …) so only the provider prefix changes in JSON Logic conditions
(`results.trivy.critical_count` → `results.cve.critical_count`).

### 4.1 `cve.schema.json` (backend grype, `grype <ref> -o json`)

| Field                 | Grype source                         | Note                                                                                                                                                  |
| --------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `analyzer`            | const `"cve"`                        |                                                                                                                                                       |
| `repository`, `tag`   | —                                    |                                                                                                                                                       |
| `scanner_version`     | `descriptor.version`                 | renamed from `trivy_version`                                                                                                                          |
| `vulnerability_count` | `len(matches)`                       |                                                                                                                                                       |
| `critical_count`      | `severity == "Critical"`             |                                                                                                                                                       |
| `high_count`          | `severity == "High"`                 |                                                                                                                                                       |
| `medium_count`        | `severity == "Medium"`               |                                                                                                                                                       |
| `low_count`           | `severity == "Low"`                  |                                                                                                                                                       |
| `negligible_count`    | `severity == "Negligible"`           | **NEW** — grype-only bucket                                                                                                                           |
| `unknown_count`       | `severity == "Unknown"`              |                                                                                                                                                       |
| `fixed_count`         | `matches where fix.state == "fixed"` |                                                                                                                                                       |
| `targets[]`           | grouped by `artifact.type`           | grype is flat; we re-synthesize pseudo-targets per artifact type (apk, deb, python, npm, …) to preserve the `targets[]` shape and dashboard rendering |

Each target keeps `Target` (the artifact type label), `Vulnerabilities[]`
(`VulnerabilityID`, `PkgName`, `InstalledVersion`, `FixedVersion`, `Severity`,
`Title`, `Description`).

### 4.2 `secrets.schema.json` (backend trufflehog, NDJSON)

`analyzer: "secrets"`, `repository`, `tag`, `scanner_version`,
`secrets_count`, `verified_count` (secrets trufflehog verified live — value-add
over trivy), `findings[]` with `DetectorName`, `Verified`, `Redacted`, `layer`.

Raw secret values are **never** stored — only redacted matches.

### 4.3 `sbom.schema.json` (backend syft, `syft <ref> -o cyclonedx-json`)

Nearly unchanged — syft emits the same CycloneDX structure trivy did. Fields
`has_sbom`, `sbom_format`, `sbom_version`, `total_components`,
`component_types`, `total_dependencies`, `licenses`, `copyleft_licenses`,
`components[]` stay identical. Add `scanner_version` (syft).

## 5. Migration & breaking changes

### Default playbook (`regis/playbooks/default/playbook.yaml`)

- `provider: trivy, rule: cve-count` → `provider: cve, rule: count`
  (slugs `cve-critical`, `cve-high` preserved)
- `provider: trivy, rule: fix-available` → `provider: cve, rule: fix-available`
- `provider: sbom, …` unchanged

Rule slugs inside `CveAnalyzer.default_rules()`: `count` (ex-`cve-count`),
`fix-available`. `SecretsAnalyzer.default_rules()`: `detected` (ex-`secret-scan`,
still opt-in — not in the default playbook).

JSON Logic variable migration: `results.trivy.*` → `results.cve.*`;
`results.trivy.secrets_count` → `results.secrets.secrets_count` (the
`secrets_count` field name is preserved per the "keep business field names
stable" rule; only the provider prefix changes).

### Dashboard (`apps/dashboard`) — 7 touch points

- `TrivySection.tsx` → `CveSection.tsx` (+ renamed interfaces)
- `AnalyzerSection.tsx`: `case "trivy"` → `case "cve"`, add `case "secrets"`
- `AnalyzerCoverageCard.tsx`: label map `trivy: "Trivy"` →
  `cve: "Vulnerabilities"`, `secrets: "Secrets"`
- `VulnerabilityChart.tsx`: "Detected by Trivy" → "Detected by Grype"
- `SummaryView.tsx`: `report.results?.trivy` → `report.results?.cve`
- `docs/analyzers/trivy.mdx` → `cve.mdx`, add `secrets.mdx`
- new `SecretsSection.tsx`

### Docs site (`docs/website`)

Update trivy references in `techContext`, `externalIntegrations`, analyzer
pages.

### Versioning & comms

- Breaking pre-1.0 → **0.33.0** (Release Please infers from `feat!:` /
  `BREAKING CHANGE:` footer; `bump-minor-pre-major: true` already set).
- `whats-new` label on the PR; `## Summary` documents the manual migration
  mapping (find/replace `provider: trivy` → `provider: cve`,
  `results.trivy` → `results.cve`, add the `secrets` provider).

### Project docs

`CLAUDE.md` required-binaries line: `trivy, regctl, hadolint, dockle` →
`grype, syft, trufflehog, regctl, hadolint, dockle`.

## 6. Infrastructure

### Dockerfile

In the `tools-fetcher` stage, replace the trivy install block (l.61) with three
pinned static-binary fetches, mirroring hadolint/dockle/regctl. `COPY --from`
the three into `/usr/local/bin` (replaces l.136).

Image impact: −trivy (~160 MB) +grype/syft/trufflehog (~120 MB). Modest net
reduction; re-measure the `ci-image-size.yml` ceiling (currently 220 MB, cites
trivy ~160 MB) after building.

### `regis doctor` (`commands/doctor.py`)

Replace `("trivy", "--version")` with `("grype", "version")`,
`("syft", "version")`, `("trufflehog", "--version")` — exact invocations
confirmed by the spike.

### CI

- `cd-docs.yml` (l.123): install grype/syft/trufflehog instead of trivy.
- `ci-image-size.yml`: update comments and re-evaluate the ceiling after
  measurement.

## 7. Error handling

Mirror the existing `AnalyzerError` contract, per wrapper:

- Binary missing → `AnalyzerError("<tool> executable not found in PATH")`
- `CalledProcessError` → `AnalyzerError("<tool> failed: {stderr}")`
- Invalid JSON/NDJSON → `AnalyzerError("<tool> produced invalid output: …")`
- **trufflehog NDJSON**: parse line-by-line, ignore blank lines. A non-zero
  exit code when secrets are found is **expected** (trufflehog may exit 183 on
  findings) — must not be treated as an error. Confirmed by the spike.

## 8. Testing strategy (TDD)

- **Spike first** (Task 1, mirroring the regctl spike): capture real fixtures in
  `tests/fixtures/{grype,syft,trufflehog}/` against a stable public image
  (e.g. `alpine:3.20`). Resolves invocations, output shapes, exit codes,
  credential env vars empirically — so later TDD uses real shapes, not guesses.
- **Wrappers**: `test_grype.py`, `test_syft.py`, `test_trufflehog.py` — patch
  `regis.utils.<tool>.subprocess` + `.shutil`, assert against fixtures.
- **Analyzers**: `test_analyzer_cve.py`, `test_analyzer_secrets.py`,
  `test_analyzer_sbom.py` (reworked) — patch the wrapper, assert the mapping
  (severity counts incl. `negligible_count`, artifact-type-grouped targets,
  `verified_count`).
- **Rename** `test_trivy.py` / `test_analyzer_trivy.py` → cve / secrets.
- **Playbook regression**: `test_playbook_engine.py`, `test_rules_config.py` —
  fixtures `results.trivy` → `results.cve` / `results.secrets`.
- **Dashboard**: component tests if present; otherwise
  `pnpm --filter @regis/dashboard build` as a guard.
- Gate: `pipenv run pytest` ≥ 90 % coverage before PR.

## 9. Patch targets (Regis-specific)

Per CLAUDE.md "Test patch targets" — patch at the source module:

- `regis.utils.grype.{subprocess,shutil}`,
  `regis.utils.syft.{subprocess,shutil}`,
  `regis.utils.trufflehog.{subprocess,shutil}`
- `regis.commands.analyze.{RegistryClient,_discover_analyzers}` (unchanged)
- `regis.commands.doctor` tool list

## 10. Open questions for the spike

1. Exact version sub-command per tool (`version` vs `--version`).
2. Credential env vars: `GRYPE_*` / `SYFT_*` vs Docker-standard.
3. TruffleHog exit code on findings (expected non-zero?) and exact `docker`
   sub-command / daemon requirement.
4. Grype `fix.state` values (`fixed`, `not-fixed`, `wont-fix`, `unknown`) →
   confirm `fixed_count` logic.
5. Pinned versions for grype / syft / trufflehog static binaries.
