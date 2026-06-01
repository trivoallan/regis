# Decision Log

> Supplemental file: this records historical decisions that complement the core Memory Bank files.

## 2026-06-01: Playbook Format — Kubernetes-Style apiVersion/kind/metadata/spec Envelope

- **Decision**: Playbooks adopt the Kubernetes resource envelope — `apiVersion: regis.trivoallan.dev/v1alpha1`, `kind: Playbook`, `metadata`, `spec`. The integer `schemaVersion` is replaced by `apiVersion` (the version mechanism). Metadata is Backstage-style: `metadata.name` (machine id, RFC-1123), `metadata.title` (display name), `metadata.description`, and the bundle SemVer → `metadata.labels["app.kubernetes.io/version"]`. `tiers`/`rules`/`badges`/`integrations`/`links` move under `spec`; evaluation semantics are unchanged.
- **Rationale**: ecosystem familiarity — Kubernetes, Backstage, and GitOps tooling all share this envelope; `apiVersion` is the idiomatic version channel (keeping the integer `schemaVersion` alongside would be redundant). `v1alpha1` deliberately signals that the format may still churn before v1.
- **Implementation choice (approach A)**: clean break (pre-v1) — the loader rejects the old flat format and `regis playbook upgrade` migrates it (dropping deprecated `pages`/`sections`/`sidebar`). The loader validates against a new `v1alpha1` JSON Schema, then **normalizes** the envelope back into the historical flat dict, so the ~12 downstream consumers (evaluator, GitLab integration, report) are untouched. The typed-model and propagate-the-envelope alternatives were deferred.
- **Scope (YAGNI)**: a single `kind` (`Playbook`); multi-kind decomposition (`RuleSet`/`Tier`/…) and a CRD/operator were explicitly deferred.
- **Distinct concept preserved**: the report's playbook audit field `schema_version` → `api_version`, but the report-envelope integer `schemaVersion` (`REPORT_SCHEMA_VERSION`, the dashboard contract) is unchanged — do not conflate them.
- **References**: `docs/superpowers/specs/2026-06-01-playbook-kubernetes-kinds-design.md`; plan `docs/memory-bank/plans/playbook-kubernetes-kinds-plan.md`; PR #640 (breaking `feat(playbook)!`, pre-major bump 0.33 → 0.34). Evolves the 2026-05-31 playbook-versioning work (the integer `schemaVersion` introduced there is replaced here).

## 2026-06-01: Dashboard Full Decouple — Core Stops Shipping the Dashboard

- **Decision**: Extract `apps/dashboard` into a standalone `regis-dashboard` repo. The core stops shipping the dashboard entirely; the two projects link only through a versioned `report.json` + integer `schemaVersion` contract, checked **100% at runtime, dashboard-side**. The core carries zero compatibility logic — it emits the current `schemaVersion` and never gates.
- **Supersedes**: the OCI-artifact-via-`ToolFetcher` + build-time-pin approach (PR #628, closed). That reuse was thin — four of `ToolFetcher`'s five reasons to exist (lazy slim, mirror, offline, doctor integration) were opted out, leaving essentially "uses ghcr."
- **Rationale**: decouple release cadences; remove Node/pnpm/Docusaurus from the Python wheel/image build path; the radical cut removes more complexity than the split adds.
- **Scope decision**: standalone `serve` is **static-preview-only** — the `regis dashboard serve` GitLab MR proxy + webhook/SSE backend (`regis/server/`) is dropped, not reimplemented in Node; `gitlab.tsx` and its three exclusive components are removed during extraction.
- **Sequencing**: Phase 0 (`schemaVersion` contract, shipped — PR #630) → Phase 1 (new repo: 1a extraction, 1b CLI+Docker, 1c runtime compat+contract — planned, PR #632) → Phase 2 (core removal, blocked until Phase 1 is live) → Phase 3 (docs). Phase 0 is a breaking schema change (`feat(schema)!`) → pre-major minor bump 0.32 → 0.33.
- **References**: `docs/superpowers/specs/2026-05-31-dashboard-full-decouple-design.md`; plans under `docs/superpowers/plans/2026-05-31-dashboard-decouple-phase1{a,b,c}-*.md`; PRs #630, #632.

## 2026-04-21: Consolidate Memory Bank Under `docs/memory-bank/`

- **Decision**: Keep `docs/memory-bank/` as the single source of truth for Memory Bank content.
- **Rationale**: The repository already stores active context, progress, and planning history under `docs/memory-bank/`, so consolidating there avoids duplicated state.
- **Follow-up**: Maintain `RULES.md`, `activeContext.md`, `progress.md`, and related files under `docs/memory-bank/`.

## 2026-02-20: Handle Skopeo Architecture Mismatch

- **Decision**: Avoid high-level `skopeo inspect` on image indexes when the local architecture doesn't match the remote index.
- **Rationale**: Prevent "no image found" errors (exit status 1) when analyzing multi-arch images on local dev machines (e.g., Apple Silicon).

## 2026-02-20: Automated Docs Publishing

- **Decision**: Implement GitHub Actions workflow to build and publish Antora site to GitLab Pages.
- **Rationale**: Automate documentation deployment to ensure it stays up-to-date with the code.

## 2026-02-20: Cookiecutter Template for Consumer Repos

- **Decision**: Create a Cookiecutter template to bootstrap new repositories for `regis` users.
- **Rationale**: Facilitate adoption and standardize the setup for image analysis projects, including CI/CD and security policies.

## 2026-02-20: Fix Missing Playbook Values

- **Decision**: Update `evaluate` in `engine.py` to add type checking and safety guards for playbook links.
- **Decision**: Integrate GitHub Actions metadata into the template workflow using `regis --meta`.
- **Rationale**: Prevent `AttributeError` crashes when link URLs are null or missing in playbook definitions. Improved metadata integration ensures better traceability in CI/CD.
- 2026-03-05: Migrated CI linting from Super-Linter to Trunk to unify local and CI linting experience and improve performance.

## 2026-03-21: Docusaurus Navbar Swizzle for Identity Badges

- **Decision**: Swizzle `Navbar/Logo` instead of using a `ComponentTypes` custom navbar item.
- **Rationale**: `ComponentTypes` approach with `@theme-original` imports fails at TypeScript level. `Navbar/Logo` swizzle using `@docusaurus/Link` and `useDocusaurusContext` is stable and avoids TS errors.

## 2026-03-21: Per-Analyzer MDX Pages Instead of Tabs

- **Decision**: Create 12 individual MDX pages in `docs/analyzers/` with a sidebar category, rather than a single page with tabs.
- **Rationale**: Enables direct linking to analyzer pages (used by analyzer badges in rules tables), allows Docusaurus to handle navigation naturally, and avoids URL-state management complexity.

## 2026-03-21: `bootstrap archive-repo` — Full Automation via `gh` / `glab`

- **Decision**: Add `bootstrap archive-repo` as a new subcommand of the `bootstrap` group that wraps cookiecutter scaffold + `pnpm install` + git init + remote repo creation + Pages activation in a single command.
- **Rationale**: `bootstrap archive` leaves the user with manual steps (create repo, push, enable Pages). Automating these via `gh` / `glab` subprocess calls reduces friction for first-time setup.
- **Key choices**:
  - Platform detected from scaffolded files (`.github/` vs `.gitlab-ci.yml`) after cookiecutter runs; can be forced early via `--platform` flag passed as `extra_context`.
  - `glab repo create` uses `--public` / `--private` flags (not `--visibility=`).
  - GitLab remote uses HTTPS (`https://gitlab.com/...`) not SSH to avoid host-key prompts.
  - Idempotent: if `glab/gh repo create` fails, checks whether repo already exists and continues if so.

## 2026-03-21: `ARCHIVE_BASE_URL` Derivation from `CI_PAGES_URL`

- **Decision**: Derive `ARCHIVE_BASE_URL` from `CI_PAGES_URL` in GitLab CI using Node.js URL parsing (`new URL(...).pathname`), rather than hardcoding `/${CI_PROJECT_NAME}/`.
- **Rationale**: `CI_PROJECT_NAME` is only the leaf name; for projects in subgroups the Pages URL path includes the full subgroup chain. Custom domains also diverge from the default `gitlab.io` pattern. `CI_PAGES_URL` is always authoritative.
- **Override**: Both platforms expose `ARCHIVE_BASE_URL` as an overridable CI/CD variable for custom domain setups.

## 2026-03-21: Adopt OCI Image Labels

- **Decision**: Add standard OCI labels (`org.opencontainers.image.*`) to the project's `Dockerfile`.
- **Rationale**: Improve discoverability and integration with GitHub Packages registry, ensuring the image description and source repository are automatically linked on the package page.
