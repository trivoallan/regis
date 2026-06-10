# Dependabot → Renovate migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Dependabot with the Mend Renovate App on `trivoallan/regis`, driven by a shared constellation preset, with grouped+automerged version updates, draft-gated majors, and all-severity security fixes.

**Architecture:** A self-contained Renovate preset (`.github/renovate-constellation.json5`) holds the full common policy; the core repo's `.github/renovate.json5` extends it, satellites extend it by path. Majors are emitted as **draft** PRs so the existing repo-wide `repo-automerge.yml` (which arms native auto-merge on every non-draft PR) skips them. A first hygiene PR removes dead root JS surface so Renovate doesn't maintain corpses.

**Tech Stack:** Renovate (Mend hosted app), JSON5 config, GitHub Actions YAML, pnpm workspace, uv/pep621.

**PR layout:**

- **PR 1 (hygiene)** — Task 1 only. Merge first.
- **PR 2 (migration)** — Tasks 2–6. Branch from `main` _after_ PR 1 merges.
- **Manual (maintainer)** — Task 7. After PR 2 merges.
- **Cross-repo (satellites)** — Task 8. Separate repos, separate sessions.

Reference spec: `docs/superpowers/specs/2026-06-10-renovate-migration-design.md`.

---

## Task 1: Hygiene — prune dead root JS surface (PR 1)

The root `package.json` scripts filter `@regis/ui` / `@regis/dashboard`, but `apps/` no longer exists (dashboard was extracted). The CI docs build runs `pnpm run build` with `working-directory: docs/website`, so it uses the **docs** package's script, not the root's — the root scripts and the `gsd-pi`/`node-addon-api`/`node-gyp` deps are dead. An orphan npm `package-lock.json` sits in this pnpm project. Remove them before Renovate onboards, or Renovate will faithfully bump dead dependencies.

**Files:**

- Modify: `package.json` (root)
- Delete: `package-lock.json` (root)
- Modify: `pnpm-lock.yaml` (root — regenerated)
- Modify: `CLAUDE.md:24-26`
- Modify: `docs/memory-bank/techContext.md:85,88`
- Modify: `.claude/launch.json` (remove dead dashboard debug entry)

- [ ] **Step 1: Verify the dead surface (baseline)**

Run:

```bash
ls apps/ 2>/dev/null || echo "apps/ absent (expected)"
grep -rIn "gsd-pi\|node-addon-api\|node-gyp\|@regis/ui\|@regis/dashboard" . \
  | grep -vE "node_modules|pnpm-lock|package-lock|docs/superpowers|docs/website/static|versioned_docs"
```

Expected: `apps/ absent`, and matches only in `package.json`, `CLAUDE.md`, `.claude/launch.json`, `docs/memory-bank/techContext.md` (and this plan). No references in `regis/`, `tests/`, or active workflows.

- [ ] **Step 2: Rewrite root `package.json`**

Replace the whole file with (keeps the workspace-root marker, the recursive `typecheck`, and the workspace-wide security overrides; drops dead scripts and dead deps):

```json
{
  "name": "regis",
  "private": true,
  "scripts": {
    "typecheck": "pnpm -r typecheck"
  },
  "pnpm": {
    "overrides": {
      "serialize-javascript": "^7.0.5",
      "webpack": "<5.106.0"
    }
  }
}
```

- [ ] **Step 3: Delete the orphan npm lockfile**

Run: `git rm package-lock.json`
Expected: `rm 'package-lock.json'`

- [ ] **Step 4: Regenerate the root pnpm lockfile**

Run: `pnpm install --lockfile-only`
Expected: completes; `git diff --stat pnpm-lock.yaml` shows the dead packages removed from the root lock. (`docs/website/pnpm-lock.yaml` is untouched.)

- [ ] **Step 5: Verify the workspace still type-checks and the docs still build**

Run:

```bash
pnpm -r typecheck
pnpm --filter docs build
```

Expected: both succeed (the `docs` package builds Docusaurus exactly as `cd-docs.yml` does).

- [ ] **Step 6: Fix stale doc references to the removed dashboard commands**

In `CLAUDE.md`, remove the two dead lines in the Commands block:

```text
pnpm --filter @regis/dashboard start   # Launch report viewer (UI work)
pnpm --filter @regis/dashboard build   # Build viewer SPA
```

(Leave the rest of the Commands block intact.)

In `docs/memory-bank/techContext.md`, replace the dead example `pnpm --filter @regis/dashboard dev` (line ~85) with `pnpm --filter docs start` and confirm the `pnpm run build` (line ~88) reference is described as the docs build (run from `docs/website`).

In `.claude/launch.json`, remove the debug configuration whose `runtimeArgs` are `["--filter", "@regis/dashboard", "dev"]`. If it is the only configuration, leave a valid empty `configurations: []`.

- [ ] **Step 7: Commit**

```bash
git add package.json pnpm-lock.yaml CLAUDE.md docs/memory-bank/techContext.md .claude/launch.json
git commit -m "build(deps): remove dead root JS workspace surface

Drop the root package.json scripts and dependencies left over from the
extracted dashboard (@regis/ui, @regis/dashboard filters match nothing
since apps/ was removed), delete the orphan npm package-lock.json in this
pnpm project, and refresh the stale dashboard command references in docs.
Clears the corpse surface before onboarding Renovate."
```

(Trunk's pre-commit hook may reformat; re-add and amend if so.)

---

## Task 2: Add the constellation preset (PR 2)

**Files:**

- Create: `.github/renovate-constellation.json5`

- [ ] **Step 1: Create the shared preset**

Create `.github/renovate-constellation.json5`:

```json5
{
  $schema: "https://docs.renovatebot.com/renovate-schema.json",
  // config:best-practices = config:recommended + docker:pinDigests
  // + helpers:pinGitHubActionDigests + :configMigration + :pinDevDependencies
  extends: ["config:best-practices", "schedule:weekly"],
  timezone: "Europe/Paris",
  labels: ["dependencies"], // keys the repo-autorebase exclusion
  minimumReleaseAge: "3 days", // supply-chain guard: never take a <3-day-old release
  semanticCommits: "enabled",
  semanticCommitType: "build",
  semanticCommitScope: "deps", // → "build(deps): …"
  lockFileMaintenance: { enabled: true, automerge: true },
  osvVulnerabilityAlerts: true,
  // Off-schedule, all severities; null age so fresh security fixes are never delayed.
  vulnerabilityAlerts: { automerge: true, minimumReleaseAge: null },
  packageRules: [
    // Workflow bumps use the ci type regardless of update type → "ci(deps): …".
    { matchManagers: ["github-actions"], semanticCommitType: "ci" },
    // Grouped non-major updates, automerged once CI is green.
    {
      matchManagers: ["pep621"],
      matchUpdateTypes: ["minor", "patch", "pin", "digest"],
      groupName: "python dependencies (non-major)",
      automerge: true,
    },
    {
      matchManagers: ["npm"],
      matchUpdateTypes: ["minor", "patch", "pin", "digest"],
      groupName: "js dependencies (non-major)",
      automerge: true,
    },
    {
      matchManagers: ["github-actions"],
      matchUpdateTypes: ["minor", "patch", "pin", "digest"],
      groupName: "github actions (non-major)",
      automerge: true,
    },
    {
      matchManagers: ["dockerfile"],
      matchUpdateTypes: ["minor", "patch", "pin", "digest"],
      groupName: "docker base images (non-major)",
      automerge: true,
    },
    // Majors: individual DRAFT PRs, never automerged. Draft is the only signal
    // repo-automerge.yml respects, so this is what stops a major from merging.
    { matchUpdateTypes: ["major"], draftPR: true, automerge: false },
  ],
}
```

- [ ] **Step 2: Validate the preset**

Run: `npx --yes --package renovate renovate-config-validator .github/renovate-constellation.json5`
Expected: `Config validated successfully` (no errors). If the validator rejects `draftPR` inside `packageRules` on the installed version, fall back to the labelled-major mechanism documented in the spec (add `addLabels: ["needs-review"]` to the major rule and an extra `!contains(... 'needs-review')` exclusion in `repo-automerge.yml`) and re-validate.

- [ ] **Step 3: Commit**

```bash
git add .github/renovate-constellation.json5
git commit -m "ci(deps): add shared Renovate constellation preset

Define the common dependency policy once: weekly grouped updates with
automerge for non-majors, draft PRs for majors, all-severity security
fixes off-schedule, and a 3-day release-age supply-chain guard. Extended
by the core repo and the satellite repos."
```

---

## Task 3: Add the core repo Renovate config (PR 2)

**Files:**

- Create: `.github/renovate.json5`

- [ ] **Step 1: Create the core config**

Create `.github/renovate.json5`:

```json5
{
  $schema: "https://docs.renovatebot.com/renovate-schema.json",
  extends: ["local>trivoallan/regis//.github/renovate-constellation.json5"],
}
```

- [ ] **Step 2: Validate the core config**

Run: `npx --yes --package renovate renovate-config-validator .github/renovate.json5`
Expected: `Config validated successfully`. (The validator resolves the `local>` preset reference.)

- [ ] **Step 3: Commit**

```bash
git add .github/renovate.json5
git commit -m "ci(deps): onboard the core repo to Renovate

Extend the shared constellation preset; no core-specific overrides."
```

---

## Task 4: Remove Dependabot (PR 2)

**Files:**

- Delete: `.github/dependabot.yml`
- Delete: `.github/workflows/repo-dependabot-critical-vulns.yml`

- [ ] **Step 1: Delete the Dependabot config and its critical-vulns filter workflow**

Run:

```bash
git rm .github/dependabot.yml .github/workflows/repo-dependabot-critical-vulns.yml
```

Expected: both files staged for deletion.

- [ ] **Step 2: Confirm no other workflow references the deleted pieces**

Run: `grep -rIn "dependabot-critical\|dependabot/fetch-metadata\|dependabot\[bot\]" .github/`
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git commit -m "ci(deps): remove Dependabot in favour of Renovate

Drop the version-update-disabled Dependabot config and the custom
critical-only filter workflow; Renovate now fixes all-severity
vulnerabilities off-schedule with automerge."
```

---

## Task 5: Wire the autorebase exclusion (PR 2)

`repo-autorebase.yml` force-pushes open PR branches when `main` advances. A third-party force-push makes Renovate treat its branch as externally edited and stop maintaining it, so Renovate-labelled PRs must be excluded; Renovate rebases its own branches via its default `rebaseWhen`.

**Files:**

- Modify: `.github/workflows/repo-autorebase.yml`

- [ ] **Step 1: Add `exclude-labels` to the rebase step**

In `.github/workflows/repo-autorebase.yml`, change the `peter-evans/rebase` step's `with:` block from:

```yaml
with:
  token: ${{ steps.generate-token.outputs.token }}
  exclude-drafts: true
```

to:

```yaml
with:
  token: ${{ steps.generate-token.outputs.token }}
  exclude-drafts: true
  exclude-labels: dependencies
```

- [ ] **Step 2: Verify the workflow still parses**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/repo-autorebase.yml')); print('YAML OK')"`
Expected: `YAML OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/repo-autorebase.yml
git commit -m "ci: stop auto-rebasing Renovate PRs

Exclude 'dependencies'-labelled PRs from repo auto-rebase; Renovate
rebases its own branches, and a third-party force-push would make it
abandon them."
```

---

## Task 6: Update memory bank and docs (PR 2)

**Files:**

- Modify: `docs/memory-bank/systemPatterns.md` (Dependabot gotcha)
- Modify: `docs/memory-bank/techContext.md` (tooling list)
- Modify: `docs/memory-bank/businessLogic.md:25`
- Modify: `docs/memory-bank/security.md:20`
- Modify: `docs/website/docs/usage/tools-management.md:101`
- Modify: `docs/memory-bank/activeContext.md` + `docs/memory-bank/progress.md` (changelog entries)

- [ ] **Step 1: Replace the Dependabot-secrets gotcha in `systemPatterns.md`**

Replace the bullet (line ~73):

```text
- **Dependabot PRs + secrets**: workflows triggered by Dependabot via `pull_request` run with read-only `GITHUB_TOKEN` and no secrets. Use `pull_request_target` for any workflow that must act on Dependabot PRs (safe when no PR code is checked out).
```

with:

```text
- **Renovate PRs**: Renovate branches live in the repo (not forks), so plain `pull_request` workflows get secrets and a writable token normally — no `pull_request_target` dance needed. Renovate config lives in `.github/renovate.json5` (extends the shared `.github/renovate-constellation.json5` preset); majors arrive as draft PRs so `repo-automerge.yml` skips them, and `repo-autorebase.yml` excludes the `dependencies` label so Renovate rebases its own branches.
```

- [ ] **Step 2: Update the tooling list in `techContext.md`**

In the dependency/CI tooling section, add a line noting Renovate (Mend hosted app) as the dependency-update mechanism for the constellation, replacing any Dependabot mention. Example bullet to add near the pnpm/uv lines:

```text
- Renovate (Mend hosted app) — dependency updates across the constellation, driven by the shared `renovate-constellation.json5` preset (replaces Dependabot + manual `pinact` runs).
```

- [ ] **Step 3: Update the two passing Dependabot mentions**

In `docs/memory-bank/businessLogic.md` line ~25, change:

```text
- Release workflows may behave differently for Dependabot or protected branches.
```

to:

```text
- Release workflows may behave differently for bot-authored (Renovate) or protected branches.
```

In `docs/memory-bank/security.md` line ~20, change:

```text
- Dependabot-related workflow behavior is handled carefully in CI
```

to:

```text
- Renovate-related workflow behavior (automerge, autorebase exclusion) is handled carefully in CI
```

- [ ] **Step 4: Correct the tools-management note**

In `docs/website/docs/usage/tools-management.md` line ~101, change:

```text
Tool versions and sha256s live in `regis/tools/manifest.yaml`. Renovate / Dependabot do not auto-update this file (Dependabot lacks regex-manager support). The bump workflow is manual:
```

to:

```text
Tool versions and sha256s live in `regis/tools/manifest.yaml`. Renovate does not auto-update this file out of the box (per-arch sha256 pins need a bespoke custom manager, not yet configured). The bump workflow is manual:
```

- [ ] **Step 5: Add changelog entries to the memory bank**

Prepend a dated entry to the "Recent Changes" list in `docs/memory-bank/activeContext.md` and to "Completed (Recent)" in `docs/memory-bank/progress.md`, summarising: Dependabot → Renovate (Mend app), shared constellation preset, grouped+automerged non-majors, draft majors, all-severity security automerge, critical-vulns filter workflow removed, autorebase `dependencies` exclusion, root JS hygiene (PR 1). Reference the spec and this plan path. Use the existing entries' format and the `[2026-06-10]` date stamp.

- [ ] **Step 6: Verify no stale Dependabot references remain in active docs**

Run: `grep -rIln -i "dependabot" docs/memory-bank/ docs/website/docs/ README.md | grep -v versioned_docs`
Expected: no matches (specs/plans under `docs/superpowers/` legitimately keep the word and are out of this grep).

- [ ] **Step 7: Commit**

```bash
git add docs/
git commit -m "docs(ci): document the Renovate migration

Update the memory bank gotcha + tooling notes, the two passing Dependabot
references, and the tools-management note; record the migration in
activeContext/progress."
```

---

## Task 7: Manual maintainer steps (after PR 2 merges)

> Not agent-executable — these require GitHub UI / org-admin rights. Listed for the maintainer.

- [ ] Install the **Mend Renovate App** (<https://github.com/apps/renovate>) on `trivoallan/regis`, `regis-gitlab`, `regis-backstage`, `regis-action`.
- [ ] In `trivoallan/regis` → Settings → Code security: **disable "Dependabot security updates"** (the PR bot) but **keep "Dependabot alerts"** enabled — Renovate's `vulnerabilityAlerts` consumes those alerts.
- [ ] Confirm the **Dependency Dashboard** issue appears on `trivoallan/regis` with no config errors.
- [ ] Watch the first onboarding/pin PR: it should pin Dockerfile `FROM` digests and GitHub Actions SHAs, titled `build(deps):` / `ci(deps):`, labelled `dependencies`.

---

## Task 8: Satellite onboarding (cross-repo, separate sessions)

> Applied in each satellite repo on its own branch/PR after PR 2 merges. Each is a single new file. Satellites have no automerge/autorebase workflows of their own, so the preset's `automerge: true` rides on Renovate's `platformAutomerge` (GitHub native auto-merge), which their branch protection already supports.

For **each** of `trivoallan/regis-gitlab`, `trivoallan/regis-backstage`, `trivoallan/regis-action`:

- [ ] Create `.github/renovate.json5` (or `renovate.json5` at root, per repo convention):

```json5
{
  $schema: "https://docs.renovatebot.com/renovate-schema.json",
  extends: ["github>trivoallan/regis//.github/renovate-constellation.json5"],
}
```

- [ ] Validate: `npx --yes --package renovate renovate-config-validator .github/renovate.json5`
- [ ] Commit with `ci(deps): onboard <repo> to the shared Renovate preset` and open a PR.

---

## Self-review notes

- **Spec coverage:** hosting/Mend (Task 7), update policy + grouping + automerge + draft majors (Task 2), security all-severity (Task 2), shared preset in core (Task 2), core config (Task 3), Dependabot removal incl. critical-vulns workflow (Task 4), autorebase integration (Task 5), automerge "no change" (verified — majors are drafts), docs/memory updates incl. secrets-gotcha obsolescence (Task 6), hygiene PR (Task 1), satellite onboarding (Task 8), validation criteria (Tasks 2/3 validator + Task 7 dashboard). All spec sections map to a task.
- **draftPR-in-packageRules** confirmed supported (renovatebot/renovate discussion #31648); Task 2 Step 2 carries the documented label-based fallback if the installed validator disagrees.
- **No placeholders:** every config/file step shows full content; every command has expected output.
