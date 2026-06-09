# README Slimming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 199-line `README.md` with a ~50-line front door that pitches Regis and redirects to the canonical documentation site, removing stale and duplicated content.

**Architecture:** Single-file documentation change. The README becomes an orientation page; the published doc site (<https://trivoallan.github.io/regis/>) remains the source of truth. No code, no tests — verification is done with `wc`, `grep`, and `trunk`.

**Tech Stack:** Markdown, GitHub-flavored. Trunk markdownlint (`MD034` forbids bare URLs) runs on commit via the pre-commit hook.

**Spec:** [docs/superpowers/specs/2026-06-09-readme-slimming-design.md](../specs/2026-06-09-readme-slimming-design.md)

---

## Task 1: Rewrite README.md as a front door

**Files:**

- Modify (full replace): `README.md`

**Context the executor needs:**

- The repo root contains `coverage-badge.svg` and `image-size-badge.svg`, referenced relatively by the badges. Keep both badge lines verbatim — they are refreshed automatically by CI.
- The hero image asset exists at `.github/assets/report-overview.png`.
- The interactive example link is pinned to `0.14.0` in the current README; reuse it verbatim (updating the example version is out of scope — see follow-up note at the end of this plan).
- All five documentation URLs below resolve to existing pages under `docs/website/docs/` (verified: `usage/getting-started.md`, `concepts/introduction.md`, `usage/analyze-image.md`, `reference/cli.md`).
- Trunk's pre-commit hook will reject bare URLs (`MD034`). Every URL in prose must be either a Markdown link `[text](url)` or wrapped in angle brackets `<url>`. The content below already complies.

- [ ] **Step 1: Replace the entire contents of `README.md` with this exact text**

```markdown
# Regis

> **Registry Scores** — Container Security & Policy-as-Code Orchestration

![Coverage](./coverage-badge.svg)
[![Docker Image Size](./image-size-badge.svg)](https://github.com/trivoallan/regis/pkgs/container/regis)

Regis provides unified container analysis, custom playbooks, and highly customizable interactive reports for production-ready CI/CD.

[![Dashboard Overview](.github/assets/report-overview.png)](https://trivoallan.github.io/regis/regis/0.14.0/_attachments/examples/alpine/index.html)

**[Explore the interactive example report →](https://trivoallan.github.io/regis/regis/0.14.0/_attachments/examples/alpine/index.html)**

## Key Features

- **Unified Registry Inspection** — Fast, multi-arch metadata extraction from any OCI-compliant registry using `regctl`.
- **Pluggable Analyzer Ecosystem** — Orchestrates industry-standard tools like `Trivy`, `regctl`, `Hadolint`, and `Dockle` to gather comprehensive security insights.
- **Policy-as-Code Playbooks** — Define compliance and security rules (e.g., "no critical vulnerabilities", "maximum image age") using flexible `jsonLogic` evaluations.
- **Hybrid Reporting** — Simultaneously generates machine-readable JSON for automation and rich, interactive HTML dashboards for human review.
- **CI/CD Native** — Designed to integrate seamlessly into GitHub Actions or GitLab CI pipelines with first-class support for MR/PR reporting.
- **Efficient Caching** — Reuse existing analysis results to speed up repeated evaluations and report regeneration.

## Documentation

Full documentation lives at **[trivoallan.github.io/regis](https://trivoallan.github.io/regis/)**:

- 🚀 [Getting Started](https://trivoallan.github.io/regis/docs/usage/getting-started) — install Regis and run your first analysis.
- 📚 [Concepts](https://trivoallan.github.io/regis/docs/concepts/introduction) — analyzers, playbooks, rules, and scoring.
- 🛠️ [Usage Guides](https://trivoallan.github.io/regis/docs/usage/analyze-image) — analyze images, manage scanner tools, configure registries.
- 📖 [CLI Reference](https://trivoallan.github.io/regis/docs/reference/cli) — every command and flag.

## GitHub Action

Run Regis in CI with the [**regis-security-analysis**](https://github.com/marketplace/actions/regis-security-analysis) GitHub Action. It is maintained in its own repository — [**trivoallan/regis-action**](https://github.com/trivoallan/regis-action) (`uses: trivoallan/regis-action@v1`) — where you will find its inputs, outputs, and usage examples.

## License

MIT
```

- [ ] **Step 2: Verify the README is short enough**

Run: `wc -l README.md`
Expected: a number ≤ 60 (the content above is ~40 lines).

- [ ] **Step 3: Verify all stale and duplicated content is gone**

Run:

```bash
grep -niE "regis-dashboard|breaking change|image variants|built-in analyzers|## inputs|## outputs|version pinning|cycloneddx|pip-audit|supply chain integrity" README.md || echo "CLEAN: no forbidden strings"
```

Expected: `CLEAN: no forbidden strings` (no matches).

- [ ] **Step 4: Verify the documentation links are well-formed and resolve to existing source pages**

Run:

```bash
grep -oE "https://trivoallan.github.io/regis/docs/[a-z/-]+" README.md
for p in usage/getting-started concepts/introduction usage/analyze-image reference/cli; do
  test -f "docs/website/docs/$p.md" && echo "OK  $p" || echo "MISSING  $p"
done
```

Expected: the four doc URLs printed, then four `OK` lines (no `MISSING`).

- [ ] **Step 5: Commit (the Trunk pre-commit hook auto-formats and runs markdownlint)**

```bash
git add README.md
git commit -m "docs(readme): slim README into a front door that redirects to the docs site

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds. If the hook reports an `MD034` bare-URL issue, wrap the offending URL in angle brackets `<...>` or as a Markdown link, then re-stage and re-commit. If the hook auto-formats the file, the commit may need to be re-run after `git add README.md`.

---

## Follow-up (out of scope for this plan)

The interactive example link is pinned to `regis/0.14.0/...`, an old version. Updating it to the current release (or a `latest` alias) is a separate concern — flag it as a background task rather than fixing it here.
