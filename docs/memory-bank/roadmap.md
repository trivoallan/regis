# Regis Roadmap

> Last updated: 2026-04-20 · Current version: v0.28.6

## Status Overview

v0.28.6 shipped · 2 items in Now · 3 in Next · 2 in Later · 1 blocked

---

## Now (v0.29.x — "Playbook Completeness")

| Item                       | Description                                                                                                                                                                                                                                                                                                      | Status      |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Playbook bundle format** | Evolve playbooks from a single YAML file to a directory bundle: `playbook.yaml` + `README.md` + `inputs.schema.json`. A new `InputsAnalyzer` validates non-image inputs (project IDs, security doc URLs, etc.) against the schema; results flow into the report and are usable in rules, labels, and checklists. | Not Started |
| **Policy versioning**      | Version playbooks independently with compatibility ranges. Needs a design spike before scheduling. Semver. Autorealease with release please ou équivalent ? décider des keywords                                                                                                                                 | Not Started |

---

## Next (1–3 months)

| Item                        | Description                                                                                                                                                | Status      |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **`regis diff`**            | Compare two `report.json` files; surface CVE delta and rule regressions. Foundational primitive for CI regression gating.                                  | Not Started |
| **SARIF export**            | Export findings in SARIF format for GitHub Code Scanning integration. Expands GitHub-native security workflows.                                            | Not Started |
| **Custom analyzer guide**   | Developer documentation for building custom analyzer plugins. Capitalizes on the existing plugin architecture.                                             | Not Started |
| **Playbook creation skill** | Claude Code skill (OMC) that guides users through creating a Regis playbook interactively — bundle structure, rules, `inputs.schema.json`, and publishing. | Not Started |

---

## Later (3–6+ months)

| Item                       | Description                                        | Notes                                                         |
| -------------------------- | -------------------------------------------------- | ------------------------------------------------------------- |
| **Multi-image comparison** | Compare security posture across a fleet of images. | Builds on `regis diff` primitives                             |
| **Tailwind v4 migration**  | Migrate dashboard to Tailwind v4.                  | **Blocked** — waiting on `@headlessui/tailwindcss` v4 support |
