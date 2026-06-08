# Repo Slimming (gh-pages → artifact) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink the default clone of `regis` from ~326 MB to ~35 MB by serving GitHub Pages from a build artifact instead of a `gh-pages` branch, deleting that branch, and guarding against future build-artifact commits.

**Architecture:** Three workstreams. WS3 (guardrails) + WS1 (CI rework to artifact-based Pages) land together in one PR — these are reversible and protect `main`. After that PR is merged and the live site is verified, WS2 (destructive branch deletion) runs from the CLI. `main` history is never rewritten.

**Tech Stack:** GitHub Actions (`actions/upload-pages-artifact`, `actions/deploy-pages`), Docusaurus, Git, Bash. No application code (`regis/`) changes.

**Spec:** `docs/superpowers/specs/2026-06-08-repo-slimming-gh-pages-design.md`

---

## File Structure

- `.github/workflows/cd-docs.yml` — **modify.** Replace the two `peaceiris/actions-gh-pages` deploy steps with an artifact upload in the build job + a new `deploy-pages` job. (WS1)
- `.github/workflows/ci-lint.yml` — **modify.** Add a `generated-artifacts-guard` job that fails if build artifacts are committed. (WS3)
- `.gitignore` — **modify.** Add `_site/`. (WS3)
- `docs/memory-bank/systemPatterns.md` — **modify.** Document the new Pages model. (WS3)
- Operational (no repo file): mirror backup, GitHub Pages settings flip, branch deletions. (Task 0, Task 4)

---

## Task 0: Safety backup (operational, do first)

**Files:** none (creates a local mirror outside the repo).

- [ ] **Step 1: Create a full mirror backup of origin**

This preserves every branch (including `gh-pages` and all old published doc versions) before any destructive operation.

Run:

```bash
git clone --mirror https://github.com/trivoallan/regis.git ~/regis-mirror-backup-2026-06-08.git
```

Expected: a bare mirror repo is created; `Cloning into bare repository ...` finishes without error.

- [ ] **Step 2: Verify the backup is a complete bare mirror**

Run:

```bash
git -C ~/regis-mirror-backup-2026-06-08.git rev-parse --is-bare-repository \
  && git -C ~/regis-mirror-backup-2026-06-08.git show-ref --verify refs/heads/gh-pages
```

Expected: prints `true` then a SHA line for `refs/heads/gh-pages` (proves `gh-pages` is captured).

---

## Task 1: WS3 — `.gitignore` + generated-artifacts CI guard

**Files:**

- Modify: `.gitignore`
- Modify: `.github/workflows/ci-lint.yml`

- [ ] **Step 1: Add `_site/` to `.gitignore`**

`build/` (line 6) already ignores `docs/website/build/`, and `.docusaurus` (line 42) covers the Docusaurus cache. Only the new Pages assembly dir needs adding. Under the `# Docusaurus` section, change:

```gitignore
# Docusaurus
.docusaurus
```

to:

```gitignore
# Docusaurus
.docusaurus

# GitHub Pages assembly (built in CI, never committed)
_site/
```

- [ ] **Step 2: Verify the guard logic passes on the current (clean) tree**

This is the exact command the new CI job will run. It must currently find nothing.

Run:

```bash
git ls-files -- '**/search-index.json' 'docs/v[0-9]*/**' '_site/**' 'docs/website/build/**'
```

Expected: **no output** (empty). If anything prints, stop — there is already a committed artifact to remove first.

- [ ] **Step 3: Verify the guard logic fails on a planted artifact**

Run:

```bash
mkdir -p docs/website/build && echo x > docs/website/build/index.html && git add -f docs/website/build/index.html
git ls-files -- '**/search-index.json' 'docs/v[0-9]*/**' '_site/**' 'docs/website/build/**'
git rm --cached docs/website/build/index.html && rm -rf docs/website/build
```

Expected: the middle command prints `docs/website/build/index.html` (guard would fail), then cleanup restores a clean tree.

- [ ] **Step 4: Add the `generated-artifacts-guard` job to `ci-lint.yml`**

Append this job at the end of the `jobs:` block (sibling of `workflow-action-pinning`). The `checkout` SHA matches the one already used elsewhere in this file.

```yaml
generated-artifacts-guard:
  name: No Generated Artifacts
  runs-on: ubuntu-latest
  permissions:
    contents: read
  steps:
    - name: Checkout Code
      uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

    - name: Reject committed build artifacts
      run: |
        set -euo pipefail

        matches="$(git ls-files -- '**/search-index.json' 'docs/v[0-9]*/**' '_site/**' 'docs/website/build/**')"
        if [ -n "$matches" ]; then
          echo "::error::Generated documentation artifacts must not be committed. GitHub Pages is served from a CI build artifact, not from tracked files."
          echo "$matches"
          exit 1
        fi
        echo "No generated documentation artifacts committed."
```

- [ ] **Step 5: Verify the workflow still parses and actions stay pinned**

Run:

```bash
python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci-lint.yml')); print('yaml ok')"
grep -REn 'uses:\s*[^[:space:]]+@(v[0-9]+|main|master|latest)\b' .github/workflows/ci-lint.yml || echo "all actions pinned by SHA"
```

Expected: `yaml ok` then `all actions pinned by SHA`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore .github/workflows/ci-lint.yml
git commit -m "ci(docs): guard against committed build artifacts"
```

---

## Task 2: WS1 — Serve Pages from an artifact in `cd-docs.yml`

**Files:**

- Modify: `.github/workflows/cd-docs.yml`

Context: today the single `build-and-deploy` job (environment `docs-production`, which gates the `REGIS_CI_*` secrets) builds the site and pushes it to `gh-pages` via two `peaceiris` steps using `keep_files: true`. We keep the build job for the secrets, have it **upload** the assembled site as a Pages artifact, and add a second job that **deploys** it under the `github-pages` environment (required by `actions/deploy-pages`, which authenticates via OIDC). The job id `build-and-deploy` is kept unchanged so branch-protection required checks keep matching.

- [ ] **Step 1: Drop the now-unused `pages: write` from the build job permissions**

The build job no longer pushes to Pages directly (the new `deploy-pages` job does). In the `build-and-deploy` job, change:

```yaml
permissions:
  contents: write
  pages: write
  pull-requests: write
```

to:

```yaml
permissions:
  contents: write
  pull-requests: write
```

- [ ] **Step 2: Replace the two `peaceiris` deploy steps with site assembly + artifact upload**

Delete both steps (`- name: Deploy docs to GitHub Pages` and `- name: Deploy root redirect to GitHub Pages`, including their `peaceiris/actions-gh-pages@...` blocks). Replace them with the two steps below. The assembly reproduces today's published layout exactly: the Docusaurus build under `/docs`, the root redirect at `/`.

```yaml
- name: Assemble Pages site
  run: |
    set -euo pipefail
    rm -rf _site
    mkdir -p _site/docs
    cp -r docs/website/build/. _site/docs/
    cp -r .github/pages-root/. _site/

- name: Upload Pages artifact
  uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
  with:
    path: _site
```

- [ ] **Step 3: Add the `deploy-pages` job**

Append this job after `build-and-deploy` (sibling under `jobs:`). It is the only place that needs `id-token: write` (OIDC) and the `github-pages` environment.

```yaml
deploy-pages:
  needs: build-and-deploy
  runs-on: ubuntu-latest
  environment:
    name: github-pages
    url: ${{ steps.deployment.outputs.page_url }}
  permissions:
    pages: write
    id-token: write
  steps:
    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128 # v5.0.0
```

- [ ] **Step 4: Verify YAML parses, actions are pinned, and no `peaceiris`/`keep_files` remain**

Run:

```bash
python -c "import yaml; d=yaml.safe_load(open('.github/workflows/cd-docs.yml')); print('jobs:', list(d['jobs'].keys()))"
grep -REn 'uses:\s*[^[:space:]]+@(v[0-9]+|main|master|latest)\b' .github/workflows/cd-docs.yml || echo "all actions pinned by SHA"
grep -nE 'peaceiris|keep_files|destination_dir|gh-pages' .github/workflows/cd-docs.yml || echo "no branch-push deploy remnants"
```

Expected: `jobs: ['build-and-deploy', 'deploy-pages']`, then `all actions pinned by SHA`, then `no branch-push deploy remnants`.

- [ ] **Step 5: Confirm `release-snapshot.yml` does not write to `gh-pages`**

Run:

```bash
grep -nE 'peaceiris|gh-pages|publish_dir|force_orphan' .github/workflows/release-snapshot.yml || echo "release-snapshot does not deploy to Pages — no change needed"
```

Expected: `release-snapshot does not deploy to Pages — no change needed`. If it does print a match, stop and adapt that workflow the same way before continuing.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/cd-docs.yml
git commit -m "ci(docs)!: deploy GitHub Pages from a build artifact instead of the gh-pages branch"
```

---

## Task 3: WS3 — Document the new model

**Files:**

- Modify: `docs/memory-bank/systemPatterns.md`

- [ ] **Step 1: Locate the CI/CD gotchas section**

Run:

```bash
grep -nE 'gh-pages|Pages|CI/CD|Trunk auto-fmt|Workflow gotchas' docs/memory-bank/systemPatterns.md | head
```

Expected: one or more line numbers near the CI/CD notes. Add the new note immediately after that section's heading.

- [ ] **Step 2: Add the Pages-model note**

Insert this paragraph in the CI/CD area:

```markdown
### Docs hosting — Pages served from an artifact (no `gh-pages` branch)

The published documentation site is deployed from a **GitHub Actions build
artifact** (`actions/upload-pages-artifact` + `actions/deploy-pages` in
`cd-docs.yml`), **not** from a `gh-pages` branch. There is intentionally no
`gh-pages` branch: it previously accumulated every deploy commit under
`keep_files: true` and grew the default clone to ~326 MB. The Docusaurus build
output is **never committed** — `ci-lint.yml`'s `generated-artifacts-guard` job
fails any PR that tracks `**/search-index.json`, `docs/v*/**`, `_site/**`, or
`docs/website/build/**`. Only the latest 3 doc versions + `next` are served
(matching `release-snapshot.yml`'s 3-version source pruning). GitHub Pages
**Source** must be set to _GitHub Actions_ in repo Settings → Pages.
```

- [ ] **Step 3: Commit**

```bash
git add docs/memory-bank/systemPatterns.md
git commit -m "docs(memory-bank): record artifact-based Pages model"
```

---

## Task 4: Land WS1+WS3 and flip the Pages source (operational)

**Files:** none (PR + GitHub settings + live verification).

- [ ] **Step 1: Set GitHub Pages source to GitHub Actions**

In the browser: repo **Settings → Pages → Build and deployment → Source → "GitHub Actions"**. This can be done before merge; the new `deploy-pages` job fails until it is set.

- [ ] **Step 2: Open the PR for the WS1+WS3 commits**

```bash
git push -u origin HEAD
gh pr create --base main --title "ci(docs): serve Pages from artifact, drop gh-pages branch growth" \
  --body "Implements docs/superpowers/specs/2026-06-08-repo-slimming-gh-pages-design.md (WS1 + WS3). WS2 branch deletion follows after the live site is verified."
```

Expected: a PR URL is printed.

- [ ] **Step 3: Merge after CI is green, then verify the live site**

After merge, the `CD / Docs` workflow runs. Verify in the browser at the published URL:

- the documentation site loads under `…/regis/docs/`;
- the root `…/regis/` redirect works;
- the version dropdown shows the 3 current versions + `next`.

Also confirm the deploy no longer touches the branch:

```bash
git ls-remote origin 'refs/heads/gh-pages'
```

Expected after a post-merge docs run: `gh-pages` still exists (old branch, now stale) but received **no new commit** from this run — confirm via the Actions log that the `deploy-pages` job ran instead of a branch push. (The branch itself is removed in Task 5.)

---

## Task 5: WS2 — Delete `gh-pages` and dead branches (operational, destructive)

**Files:** none (remote/local ref deletions). **Pre-condition:** Task 4 complete, live site verified, Task 0 backup confirmed.

- [ ] **Step 1: Delete the `gh-pages` branch on origin**

```bash
git push origin --delete gh-pages
```

Expected: `- [deleted]   gh-pages`. This is the ~8.5 GB win — new clones stop fetching it immediately.

- [ ] **Step 2: Delete dead experiment / merged branches on origin**

Delete only after eyeballing each. The first two are already merged into `main`; the others are dead experiments.

```bash
git push origin --delete claude/pip-audit-error-resolution-EMrSz
git push origin --delete copilot/fix-failing-checks
git push origin --delete caca       || echo "caca not on origin (local-only) — skip"
git push origin --delete nodogfood  || echo "nodogfood not on origin (local-only) — skip"
```

Expected: `[deleted]` lines (or the skip message for local-only branches).

> Note: leave `origin/docs/latest-generated` alone — it is auto-recreated by `cd-docs.yml`'s `create-pull-request` step and its unique objects are negligible (it is `main` + a few generated files). Deleting it yields no lasting size benefit.

- [ ] **Step 3: Prune merged local branches**

```bash
git branch -D caca nodogfood 2>/dev/null || true
git branch --merged main | grep -E 'tritri/' | xargs -r -n1 git branch -d
```

Expected: merged `tritri/*` branches are deleted; any still-unmerged or checked-out-in-a-worktree ones are skipped by `git branch -d` (safe — it refuses non-merged).

- [ ] **Step 4: Verify a fresh clone is small**

A clone only transfers **reachable** objects, so deleting `gh-pages` shrinks new clones immediately — even before GitHub's server-side `gc`.

```bash
tmp="$(mktemp -d)"
git clone --bare https://github.com/trivoallan/regis.git "$tmp/regis.git"
du -sh "$tmp/regis.git"
rm -rf "$tmp"
```

Expected: `.git` size around **~35–50 MB** (down from ~326 MB). If it is still large, re-check that `gh-pages` was actually deleted on origin (`git ls-remote origin 'refs/heads/gh-pages'` should print nothing).

- [ ] **Step 5: Record completion**

No commit needed (operational task). Note in the PR / tracking that server-side disk reclamation completes after GitHub's automatic `gc` (typically a few days); client clone size is already reduced.

---

## Self-Review notes

- **Spec coverage:** WS1 → Task 2; WS2 → Task 5; WS3 → Tasks 1 (gitignore+guard) & 3 (doc); backup → Task 0; manual Pages setting → Task 4 Step 1; verification → Task 4 Step 3 + Task 5 Step 4; rollback → backup (Task 0) + revertable workflow PR (Task 4). All spec sections mapped.
- **Old-version risk** (spec "Risques"): accepted; old versions preserved in the Task 0 mirror.
- **Naming consistency:** job ids `build-and-deploy` (kept) and `deploy-pages` (new) used identically across Task 2 steps; guard patterns identical in Task 1 Step 2/4 and the systemPatterns note.
