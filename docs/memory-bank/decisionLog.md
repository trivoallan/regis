# Decision Log

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
