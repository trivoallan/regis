---
sidebar_position: 1.6
title: Roadmap
description: Upcoming features, stability commitments, and compatibility guarantees for Regis.
---

This page helps teams building custom playbooks and integrations understand what's stable, what's coming, and what might change.

---

## Stability tiers

Regis categorizes its public interfaces into stability tiers so you can make informed decisions about what to depend on.

| Tier             | Meaning                                                                          | Examples                                                                                                                            |
| ---------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Stable**       | Will not change without a major version bump and migration guide                 | Report JSON schema (`report.schema.json`), playbook definition schema, rule evaluation fields (`passed`, `status`, `slug`, `level`) |
| **Evolving**     | May gain new fields; existing fields won't be removed without deprecation notice | Analyzer output schemas (new fields may appear), `rules_summary` structure, badge/label fields                                      |
| **Experimental** | May change or be removed in any minor release                                    | New CLI commands in their first release, undocumented internal APIs                                                                 |

### Stable API surface

The following are considered **stable** and safe to depend on in custom playbooks:

- **Playbook definition schema** — `name`, `description`, `slug`, `sections`, `rules`, `conditions`, `tiers`, `links`, `labels`, `badge_labels`, `mr_description_checklists`
- **Report JSON top-level fields** — `version`, `request`, `results`, `playbook`, `playbooks`, `rules`, `rules_summary`, `tier`, `badges`, `links`
- **Rule result fields** — `slug`, `description`, `passed`, `status`, `message`, `level`, `tags`, `analyzers`
- **Rules summary** — `score` (0-100), `total`, `passed`, `by_tag`
- **Entry point group** — `regis.analyzers` (for custom analyzer plugins)

### Evolving interfaces

- Individual **analyzer output schemas** — new fields may be added to any analyzer's output. Existing fields (e.g., `trivy.vulnerabilities.summary`) are stable within a major version.
- **CLI flags and output format** — command signatures are stable after one release cycle; output formatting (text mode) may change.

---

## Near-term (v0.25.0)

| Feature                    | Status      | Description                                                                                                                |
| -------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Project rebrand**        | In progress | Rename from `regis-cli` to `Regis` (Registry Scores) across package, CLI, docs, and branding                               |
| **`regis diff` command**   | Planned     | Compare two `report.json` files — score delta, CVE changes, rule regressions. Supports `--fail-on-regression` for CI gates |
| **Custom analyzer guide**  | Planned     | Step-by-step developer documentation for building analyzer plugins                                                         |
| **GitHub PR integration**  | Shipped     | `regis github update-pr` command posts analysis results as PR comments                                                     |
| **Reusable GitHub Action** | Shipped     | Composite action encapsulating analysis, artifact upload, and PR comment                                                   |

## Medium-term

| Feature                    | Description                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **Multi-image comparison** | Compare security posture across multiple images in a single report                 |
| **SARIF export**           | Export vulnerability findings in SARIF format for GitHub Code Scanning integration |
| **Policy versioning**      | Version playbooks independently from the CLI, with explicit compatibility ranges   |

## Deferred

| Feature                               | Reason                                          |
| ------------------------------------- | ----------------------------------------------- |
| **Tailwind v4 migration** (dashboard) | Blocked on `@headlessui/tailwindcss` v4 support |

---

## Compatibility commitments

1. **No silent breaking changes** — any change to stable fields will be announced in the changelog and accompanied by a migration guide.
2. **Deprecation window** — deprecated fields will continue to work for at least one minor version before removal.
3. **Schema validation** — `regis` validates its own report output against `report.schema.json` at generation time. If your playbook depends on a field that passes validation today, it will continue to work until the schema version changes.
4. **Analyzer output contracts** — custom playbooks that reference `results.<analyzer>.<field>` paths documented in the analyzer schemas are protected by the evolving stability tier.

---

## How to give feedback

If your team is building custom playbooks or integrations and needs clarity on stability of a specific field or feature, open a [GitHub Discussion](https://github.com/trivoallan/regis/discussions) or file an issue.
