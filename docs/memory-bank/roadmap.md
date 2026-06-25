# Regis Roadmap

> Supplemental file: this is a planning artifact that complements the core Memory Bank files.

> Last updated: 2026-06-25 · Current version: v0.37.x · Stage: pre-v1

## Positioning

Container security & policy-as-code, with a pivot toward **supply-chain
provenance**: Regis verdicts (SARIF, with `result.kind` discriminating policy
from vulnerability) are consumable as signed attestations at a registry's front
door.

Format: **Now / Next / Later** — no hard dates (avoids false precision).

## Memory Bank Alignment

- Keep items synchronized with `docs/memory-bank/projectbrief.md` and `progress.md`.
- Treat `decisionLog.md` and `roadmap.md` as supplemental planning history, not the primary operational context.

---

## Recently shipped

| Item                                                                           | Status |
| ------------------------------------------------------------------------------ | ------ |
| Hexagonal migration (ports & adapters, enforced by import-linter)              | Done   |
| SARIF output of playbook verdicts (`result.kind` policy/vuln) + `ruleset_hash` | Done   |
| Multi-arch container images (linux/amd64 + arm64)                              | Done   |
| Dependency automation → Renovate                                               | Done   |
| GitLab CI-native integration extracted to a dedicated template                 | Done   |
| Playbook format → Kubernetes-style envelope (`apiVersion` / `kind`)            | Done   |
| Container image size reduction (slim/full variants, lazy tool fetch)           | Done   |

---

## Now — committed / in progress

| Item                                                                                                 | Status   | Ref        |
| ---------------------------------------------------------------------------------------------------- | -------- | ---------- |
| Fix the getting-started install (Docker → `ghcr.io`, `pip` → `uv`)                                   | On Track | PR #812    |
| Per-run registry cache + syft → grype SBOM handoff (scan performance)                                | Planned  | issue #806 |
| Refactor the `analyze.py` command + tighten `utils/` layering                                        | Planned  | issue #807 |
| Project health: `SECURITY.md`, `CONTRIBUTING.md`, issue templates                                    | Planned  | issue #810 |
| **Playbook bundle format** (`playbook.yaml` + `README.md` + `inputs.schema.json` + `InputsAnalyzer`) | Planned  | sprint     |
| Docs site finishing (branding, navigation, SEO) + stop versioned snapshots                           | Planned  | sprint     |

---

## Next — planned (~1-3 months)

| Item                                                                                                                             | Note                                                       |
| -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Provenance integration**: Regis verdicts → signed attestations at a registry's front door (houba)                              | SARIF contract already conforms; depends on houba maturity |
| **Native Harbor** support (`RegistryProvider` abstraction)                                                                       | generic product feature                                    |
| Reusable playbook archetypes: image-admission gate · continuous catalog compliance · tiered progression (bronze → silver → gold) | built on the bundle format                                 |
| Distribution: `uv tool install` + a non-colliding PyPI distribution name                                                         | follows from the install fix (#809)                        |
| Documentation i18n pipeline (automated translation)                                                                              | generic                                                    |

---

## Later — directional (~3-6+ months)

| Item                                                        | Note                  |
| ----------------------------------------------------------- | --------------------- |
| Multi-image / fleet posture comparison (`regis diff`)       | directional           |
| Playbook/policy versioning with compatibility ranges        | design spike required |
| Org-level score aggregation + reporting                     | directional           |
| Developer guide: writing custom analyzers                   | directional           |
| Self-scan in CI (Regis analyzes its own image each release) | maturity signal       |
| Import / merge an existing image catalog                    | design spike required |

---

## Risks & dependencies

- **houba maturity (pre-prod)** paces the provenance-integration timeline. Mitigation: the SARIF contract is **frozen**, so Regis can integrate against a stable interface while houba hardens.
- **Capacity**: Now already carries 6 items; Next / Later are directional, not committed. Anything added to Now means something else comes off (zero-sum against capacity).
- **Blocked dependencies**: the dashboard Tailwind v4 migration is **cut** (the standalone dashboard was abandoned; visibility now rides `report.json` + provenance tooling).
