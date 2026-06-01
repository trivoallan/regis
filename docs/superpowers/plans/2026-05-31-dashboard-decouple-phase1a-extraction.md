# Phase 1a — regis-dashboard Extraction & Standalone Bootstrap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract `apps/dashboard` from the regis monorepo into a standalone `regis-dashboard` GitHub repo that builds and deploys to its own GitHub Pages on its own, with history preserved, release-please + Conventional Commits, and no Python / no Memory Bank.

**Architecture:** `git filter-repo` re-roots `apps/dashboard/**` to the repo root with history. The Docusaurus SPA already reads `url`/`baseUrl` from env vars and fetches `report.json` at runtime, so it builds standalone with zero code changes to its data path. A committed demo `report.json` (the core's `report.v1.json` contract fixture) lets the deployed Pages site render real content. The dropped GitLab live-backend (decision: static-preview-only) means the `gitlab.tsx` page and its components are removed so the standalone bundle has no dead backend dependency.

**Tech Stack:** Docusaurus 3.10, React 19, Tremor, TailwindCSS, pnpm, Node ≥18, GitHub Actions, release-please, GitHub Pages. No Python.

---

## Scope & boundaries

This is **Phase 1a** of three Phase-1 sub-plans (see the full-decouple spec `docs/superpowers/specs/2026-05-31-dashboard-full-decouple-design.md`):

- **1a (this plan):** extraction + standalone repo that builds & deploys to Pages. Ships a working, deployable `regis-dashboard`.
- **1b (next):** the Node CLI (`render` / `serve` / `archive add|configure` / `bootstrap archive`) + the published Docker image.
- **1c:** runtime `schemaVersion` compatibility check in `ReportProvider` + cross-repo contract test (CI fetches the core's `report.v1.json`).

**Out of scope for 1a:** the CLI, the Docker image, the runtime schemaVersion gate, the GitLab proxy/webhook backend (dropped — static-preview-only decision), and any change to the **core** repo. 1a touches only the new `regis-dashboard` repo.

**Execution context:** Unlike the Phase 0 plan, this plan does **not** run in a core worktree. **Task 1 creates the working directory** (`~/src/regis-dashboard`) that every later task operates in. All paths from Task 2 onward are relative to that new repo root.

## File Structure (new repo, after Task 1 extraction)

```text
regis-dashboard/                 # was apps/dashboard/
  docusaurus.config.ts           # url/baseUrl from env (unchanged data path)
  package.json                   # @regis/dashboard → standalone (Task 2)
  tailwind.config.js
  tsconfig.json
  src/
    components/                  # SummaryView, AnalyzerPage, ReportProvider, ArchiveView, …
    pages/
      index.tsx                  # ArchiveView host
      gitlab.tsx                 # REMOVED in Task 6 (dropped feature)
    theme/Root.tsx               # ReportProvider mount
    css/
  docs/                          # index.mdx, rules.mdx, analyzers/*.mdx
  static/
    report.json                 # demo report for Pages (Task 4)
  README.md / CONTRIBUTING.md / LICENSE   # Task 5
  release-please-config.json / .release-please-manifest.json   # Task 7
  .github/workflows/ci.yml / cd-pages.yml / release-please.yml # Tasks 8-9
```

| File                                             | Responsibility                                                | Task |
| ------------------------------------------------ | ------------------------------------------------------------- | ---- |
| (whole tree)                                     | extracted, re-rooted, history preserved                       | 1    |
| `package.json`                                   | standalone metadata, no workspace assumptions                 | 2    |
| `docusaurus.config.ts`                           | GitHub-Pages `organizationName`/`projectName`/`trailingSlash` | 3    |
| `static/report.json`                             | demo report so Pages renders                                  | 4    |
| `README.md`, `CONTRIBUTING.md`, `LICENSE`        | repo docs (no Memory Bank)                                    | 5    |
| `src/pages/gitlab.tsx` + gitlab components       | **deleted** (dropped backend feature)                         | 6    |
| `release-please-config.json`, manifest           | release automation                                            | 7    |
| `.github/workflows/cd-pages.yml`                 | build + deploy Pages                                          | 8    |
| `.github/workflows/ci.yml`, `release-please.yml` | PR checks + releases                                          | 9    |

---

### Task 1: Extract `apps/dashboard` into a standalone repo with history

**Files:** none in-repo yet — this task creates the repo.

**Prerequisite:** `git-filter-repo` installed (`brew install git-filter-repo` or `pipx install git-filter-repo`). Verify: `git filter-repo --version` prints a version.

- [ ] **Step 1: Fresh mirror clone of the core**

```bash
cd ~/src
git clone https://github.com/trivoallan/regis.git regis-dashboard
cd regis-dashboard
```

- [ ] **Step 2: Re-root apps/dashboard to the repo root, dropping all other history**

```bash
git filter-repo --path apps/dashboard/ --path-rename apps/dashboard/:
```

Expected: command completes; the working tree now has `docusaurus.config.ts`, `package.json`, `src/`, `docs/`, etc. at the **root** (no `apps/dashboard/` prefix).

- [ ] **Step 3: Verify the re-root and that history survived**

```bash
ls package.json docusaurus.config.ts src docs        # all present at root
git log --oneline -- docusaurus.config.ts | head -5  # shows historical commits
test ! -d apps && echo "OK: no apps/ prefix remains"
```

Expected: files at root; `git log` lists multiple historical commits (history preserved); "OK" printed.

- [ ] **Step 4: Reset the remote and create the GitHub repo**

`filter-repo` removes `origin` by design. Create the new repo and point at it:

```bash
gh repo create trivoallan/regis-dashboard --public \
  --description "Standalone interactive viewer for regis container-security reports" \
  --disable-wiki
git remote add origin https://github.com/trivoallan/regis-dashboard.git
```

Do **not** push yet — Tasks 2–9 prepare the first real commit set. (The history from filter-repo is already committed; later tasks add commits on top.)

- [ ] **Step 5: Sanity-build the extracted SPA as-is (baseline)**

```bash
corepack enable
pnpm install
pnpm build
```

Expected: `pnpm build` succeeds and writes a `build/` directory containing `index.html` and the `report/` route. (It will warn about a missing `report.json` fetch at runtime — that is fixed in Task 4. The build itself must pass.)

If `pnpm build` fails because the project assumed a workspace root, note the exact error and proceed to Task 2 (which makes it standalone); re-run this build at the end of Task 2.

---

### Task 2: Make `package.json` standalone

**Files:**

- Modify: `package.json`

- [ ] **Step 1: Rewrite the package manifest**

The extracted `package.json` is `@regis/dashboard`, `private: true`, version `0.0.1`, with no repo metadata. Replace its top-level metadata fields (keep `scripts`, `dependencies`, `devDependencies`, `browserslist`, `engines` exactly as they are) so the head of the file reads:

```json
{
  "name": "regis-dashboard",
  "version": "0.0.0",
  "private": false,
  "description": "Standalone interactive viewer for regis container-security reports",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/trivoallan/regis-dashboard.git"
  },
  "homepage": "https://trivoallan.github.io/regis-dashboard/",
  "packageManager": "pnpm@9.0.0",
```

Notes: `private: false` (it will be a public, optionally-published package). `version: 0.0.0` — release-please owns the version from here (Task 7). Keep all `scripts`/deps unchanged.

- [ ] **Step 2: Add a `.gitignore` if absent**

Ensure `node_modules`, `build`, `.docusaurus`, and `static/report.json` patterns are ignored where appropriate. The demo report in Task 4 is committed deliberately, so do **not** ignore `static/report.json` — instead ignore only `node_modules/`, `build/`, `.docusaurus/`:

```gitignore
node_modules/
build/
.docusaurus/
*.log
```

- [ ] **Step 3: Verify standalone install + build**

```bash
rm -rf node_modules build .docusaurus
pnpm install
pnpm build
pnpm typecheck
```

Expected: install, build, and `tsc --noEmit` all succeed with no workspace-related errors.

- [ ] **Step 4: Commit**

```bash
git add package.json .gitignore
git commit -m "chore: make package standalone (rename, repo metadata, version 0.0.0)"
```

---

### Task 3: Configure Docusaurus for GitHub Pages

**Files:**

- Modify: `docusaurus.config.ts`

`docusaurus.config.ts` derives `url`/`baseUrl` from env vars (`ARCHIVE_URL`/`REPORT_URL`, `ARCHIVE_BASE_URL`/`REPORT_BASE_URL`, defaulting to `https://example.com` and `/`). GitHub Pages also needs `organizationName`, `projectName`, and (for Pages) `trailingSlash`.

- [ ] **Step 1: Add the Pages identity fields**

In `docusaurus.config.ts`, immediately after the `baseUrl:` line (~line 25), add:

```ts
  organizationName: "trivoallan",
  projectName: "regis-dashboard",
  trailingSlash: false,
```

Do **not** hardcode `url`/`baseUrl` — the env-var derivation stays (the Pages workflow sets them at build time in Task 8).

- [ ] **Step 2: Verify a Pages-style build**

Simulate the Pages build (project site served under `/regis-dashboard/`):

```bash
REPORT_URL=https://trivoallan.github.io REPORT_BASE_URL=/regis-dashboard/ pnpm build
```

Expected: build succeeds; `build/index.html` references assets under `/regis-dashboard/` (verify: `grep -o "/regis-dashboard/[^\"']*" build/index.html | head` prints matches).

- [ ] **Step 3: Commit**

```bash
git add docusaurus.config.ts
git commit -m "feat: configure Docusaurus for GitHub Pages (org/project/trailingSlash)"
```

---

### Task 4: Bake in a demo `report.json` so Pages renders

**Files:**

- Create: `static/report.json`

The SPA fetches `{baseUrl}report.json` at runtime (`src/components/ReportProvider.tsx`). Without it the deployed site shows an error state. Commit a demo report so the live Pages site renders real content. Use the core's contract fixture (it is realistic and schema-honest), which also pre-stages the 1c contract test.

- [ ] **Step 1: Copy the core's contract fixture as the demo report**

From a local checkout of the core repo (or via raw URL), copy `tests/fixtures/report.v1.json` to `static/report.json`:

```bash
curl -fsSL https://raw.githubusercontent.com/trivoallan/regis/main/tests/fixtures/report.v1.json -o static/report.json
```

Expected: `static/report.json` exists and is valid JSON: `node -e "JSON.parse(require('fs').readFileSync('static/report.json','utf8')); console.log('valid JSON')"` prints `valid JSON`.

- [ ] **Step 2: Verify the built site serves the report and the SPA loads it**

```bash
REPORT_BASE_URL=/ pnpm build
test -f build/report.json && echo "OK: report.json copied to build root"
pnpm serve --no-open &   # docusaurus serve on :3000
sleep 4
curl -fsSL http://localhost:3000/report.json | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const r=JSON.parse(d);console.log('schemaVersion', r.schemaVersion)})"
kill %1
```

Expected: "OK: report.json copied to build root"; the curl prints `schemaVersion 1`.

- [ ] **Step 3: Commit**

```bash
git add static/report.json
git commit -m "docs: add demo report.json (core report.v1 fixture) for Pages preview"
```

---

### Task 5: Repo docs — README, CONTRIBUTING, LICENSE (no Memory Bank)

**Files:**

- Create: `README.md`, `CONTRIBUTING.md`, `LICENSE`

Per the design: a single-responsibility front-end project gets a `README` + `CONTRIBUTING`, **not** a Memory Bank.

- [ ] **Step 1: Write `README.md`** with this content:

```markdown
# regis-dashboard

Standalone interactive viewer for [regis](https://github.com/trivoallan/regis)
container-security reports.

Live demo: https://trivoallan.github.io/regis-dashboard/

## What it does

Renders a regis `report.json` as an interactive Docusaurus + Tremor site:
summary, rules, per-analyzer pages, and a multi-report archive browser.

## Contract

This viewer consumes the regis report envelope identified by an integer
`schemaVersion`. The supported range is declared per release (see the runtime
compatibility check — added in a later phase). The reference report shape lives
at `trivoallan/regis:tests/fixtures/report.v1.json`.

## Develop

    corepack enable
    pnpm install
    pnpm start          # dev server with the demo report (static/report.json)
    pnpm build          # static build into build/

## Status

Extracted from the regis monorepo (`apps/dashboard`). The CLI (`render` / `serve`
/ `archive` / `bootstrap archive`) and the published Docker image are added in
Phase 1b.
```

- [ ] **Step 2: Write `CONTRIBUTING.md`**

```markdown
# Contributing

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
  (Angular type list). Releases are cut by release-please from the commit log.
- `pnpm install && pnpm build && pnpm typecheck` must pass before opening a PR.
- Feature branches → PR → `main` (protected). Rebase on latest `main`; never
  merge `main` back into a feature branch.
```

- [ ] **Step 3: Add `LICENSE`** — MIT, copyright holder `Tristan Rivoallan`, year 2026 (match the core repo's license; copy its `LICENSE` text verbatim, updating only the project reference if the core's contains one).

- [ ] **Step 4: Commit**

```bash
git add README.md CONTRIBUTING.md LICENSE
git commit -m "docs: add README, CONTRIBUTING, and LICENSE"
```

---

### Task 6: Remove the dropped GitLab live-backend feature from the SPA

**Files:**

- Delete: `src/pages/gitlab.tsx`, `src/components/GitLabMRList.tsx`, `src/components/MRComparison.tsx`, `src/components/TriggerAnalysis.tsx`
- Modify: any navbar/config reference to the `/gitlab` route in `docusaurus.config.ts`

Decision recorded in the spec: standalone is **static-preview-only**; the GitLab proxy/webhook backend is dropped. The SPA's `gitlab.tsx` page calls that backend and would be dead in the standalone build. Remove it and the three components it exclusively owns.

The exact deletion set was determined against the source: `gitlab.tsx` imports `GitLabMRList`, `TriggerAnalysis`, and `MRComparison`, and a reference scan confirms those three are imported by **nothing** other than `gitlab.tsx` (and they do not import each other). Everything else — `ArchiveView`, `ReportProvider`, `SummaryView`, `AnalyzerPage`, all `*Section` components, and the `components/Dashboard/` chart cards — is used by `index.tsx`/the docs pages and must stay.

- [ ] **Step 1: Re-confirm the deletion set is still exclusive (guard against drift since this plan was written)**

```bash
for c in GitLabMRList MRComparison TriggerAnalysis; do
  echo "$c referenced outside gitlab.tsx + its own file:"
  grep -rl "\b$c\b" src docs | grep -vE "src/components/$c.tsx|src/pages/gitlab.tsx" || echo "  (none — safe to delete)"
done
```

Expected: each prints "(none — safe to delete)". If any prints a file, that component is now shared — stop and report it before deleting.

- [ ] **Step 2: Delete the page and its three exclusive components**

```bash
git rm src/pages/gitlab.tsx \
       src/components/GitLabMRList.tsx \
       src/components/MRComparison.tsx \
       src/components/TriggerAnalysis.tsx
```

- [ ] **Step 3: Remove the navbar/config link to `/gitlab`** in `docusaurus.config.ts` (delete the navbar item whose `to`/`href` is `/gitlab`, if present — `grep -n "gitlab" docusaurus.config.ts` locates it).

- [ ] **Step 4: Verify the build is clean with no dangling references**

```bash
pnpm typecheck
pnpm build
grep -rn "gitlab" src/ docusaurus.config.ts || echo "OK: no gitlab references remain"
```

Expected: `typecheck` and `build` pass; "OK: no gitlab references remain" (or only incidental, non-code matches).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: drop GitLab live-backend page (static-preview-only)"
```

> **Out of scope (do not action here):** `src/components/PlaybookView.tsx` is referenced by nothing (not even `gitlab.tsx`) — it is **pre-existing dead code**, unrelated to the GitLab feature. Leave it; removing it is a separate cleanup, not part of this extraction.

---

### Task 7: release-please + Conventional Commits

**Files:**

- Create: `release-please-config.json`, `.release-please-manifest.json`

- [ ] **Step 1: Create `release-please-config.json`**

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "node",
  "bump-minor-pre-major": true,
  "packages": {
    ".": {
      "package-name": "regis-dashboard"
    }
  }
}
```

`bump-minor-pre-major: true` mirrors the core: pre-1.0 breaking changes bump minor, not major.

- [ ] **Step 2: Create `.release-please-manifest.json`**

```json
{
  ".": "0.0.0"
}
```

- [ ] **Step 3: Verify config is valid JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('release-please-config.json','utf8'));JSON.parse(require('fs').readFileSync('.release-please-manifest.json','utf8'));console.log('OK')"
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add release-please-config.json .release-please-manifest.json
git commit -m "ci: add release-please config (node, bump-minor-pre-major)"
```

---

### Task 8: GitHub Pages deploy workflow

**Files:**

- Create: `.github/workflows/cd-pages.yml`

- [ ] **Step 1: Write the Pages workflow**

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
        env:
          REPORT_URL: https://trivoallan.github.io
          REPORT_BASE_URL: /regis-dashboard/
      - uses: actions/upload-pages-artifact@v3
        with:
          path: build
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Enable Pages (source = GitHub Actions)**

```bash
gh api -X POST repos/trivoallan/regis-dashboard/pages -f build_type=workflow 2>/dev/null || \
  echo "Enable Pages → Settings → Pages → Source: GitHub Actions (if the API call 409s, it is already enabled)"
```

- [ ] **Step 3: Commit (do not push yet — Task 10 pushes everything)**

```bash
git add .github/workflows/cd-pages.yml
git commit -m "ci: add GitHub Pages deploy workflow"
```

---

### Task 9: PR-check + release-please workflows

**Files:**

- Create: `.github/workflows/ci.yml`, `.github/workflows/release-please.yml`

- [ ] **Step 1: Write `ci.yml` (build + typecheck on PRs)**

```yaml
name: CI

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm build
```

- [ ] **Step 2: Write `release-please.yml`**

```yaml
name: release-please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/release-please.yml
git commit -m "ci: add PR build check and release-please workflows"
```

---

### Task 10: Push, verify Pages deploy, protect main

**Files:** none (infra)

- [ ] **Step 1: Push the prepared history**

```bash
git push -u origin main
```

Expected: push succeeds (the repo was empty on the remote; the filter-repo history + Tasks 2–9 commits land).

- [ ] **Step 2: Verify the Pages deploy ran and the live site renders**

```bash
gh run watch --exit-status   # waits for the cd-pages run to finish green
```

Then load `https://trivoallan.github.io/regis-dashboard/` and confirm:

- the summary page renders (not the "No report loaded" error state),
- `https://trivoallan.github.io/regis-dashboard/report.json` returns the demo report with `schemaVersion: 1`.

```bash
curl -fsSL https://trivoallan.github.io/regis-dashboard/report.json | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log('live schemaVersion', JSON.parse(d).schemaVersion))"
```

Expected: `live schemaVersion 1`.

- [ ] **Step 3: Protect `main`**

```bash
gh api -X PUT repos/trivoallan/regis-dashboard/branches/main/protection \
  -F "required_status_checks[strict]=true" \
  -F "required_status_checks[contexts][]=build" \
  -F "enforce_admins=false" \
  -F "required_pull_request_reviews[required_approving_review_count]=0" \
  -F "restrictions=" 2>&1 | tail -3 || \
  echo "If the API shape errors, set branch protection via Settings → Branches: require the CI 'build' check."
```

- [ ] **Step 4: Final verification checklist**

- [ ] `pnpm install && pnpm build && pnpm typecheck` pass locally on a fresh clone.
- [ ] No `gitlab`/backend references remain (`grep -rn gitlab src/`).
- [ ] Pages site is live and serves the demo `report.json`.
- [ ] `git log` in the new repo shows preserved `apps/dashboard` history plus the Task 2–9 commits.
- [ ] release-please opened (or is ready to open) a release PR on the next push.

---

## Self-review notes (reconciled against the spec & decisions)

- **Spec Phase-1 "git filter-repo of apps/dashboard, history preserved"** → Task 1.
- **Spec Phase-1 "new-repo CI: pnpm build → dedicated GitHub Pages"** → Tasks 3, 4, 8, 10.
- **Spec Phase-1 "release-please + Conventional Commits"** → Tasks 7, 9.
- **Spec Phase-1 "Settings App / GitHub config (same pattern as core)"** → Task 1 Step 4 + Task 10 Step 3 (repo creation + branch protection via `gh`; a Settings-App `.github/settings.yml` can be added in 1b alongside the rest of CI — noted, not blocking 1a).
- **Spec "No Memory Bank — README + CONTRIBUTING suffice"** → Task 5 (explicitly no memory-bank).
- **Decision: static-preview-only (GitLab backend dropped)** → Task 6 removes `gitlab.tsx` and its exclusive components.
- **Deferred to 1b/1c (correctly NOT here):** the `render`/`serve`/`archive`/`bootstrap` CLI, the Docker image, and the runtime `schemaVersion` compatibility gate. 1a ships a deployable site that renders a baked-in demo report; the CLI that feeds _arbitrary_ reports is 1b.

## Risks / watch-points

- **`pnpm-lock.yaml`**: `filter-repo` re-roots only `apps/dashboard/`, which historically had **no** lockfile (the lockfile lived at the monorepo root and is excluded). Task 2's `pnpm install` generates a fresh `regis-dashboard` lockfile — commit it (add to the Task 2 commit if `pnpm install` created it). CI uses `--frozen-lockfile`, so the lockfile **must** be committed or CI fails.
- **`tsconfig.json` extends `@docusaurus/tsconfig`**: that dep is already in `devDependencies`, so standalone typecheck works. If `tsconfig.json` references a monorepo-root path, fix it in Task 2.
- **Demo report drift**: Task 4 pins the demo to the core's `report.v1.json` at _fetch time_. Phase 1c formalizes this as a CI-fetched contract test; until then the demo is a static snapshot — acceptable.
- **`gitlab.tsx` shared components**: Task 6 must not delete components also used by `index.tsx`/docs pages. The Step-1 inventory + the `grep -rl "<Component"` guard prevents over-deletion.
