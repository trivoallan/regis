# Merge Queue Adoption — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the home-grown auto-rebase + auto-merge re-arming machinery with GitHub's native merge queue.

**Architecture:** Two phases enforced by an egg-and-chicken constraint. **Phase 1** is a single PR that adds the `merge_group` trigger to the two required-check workflows (`pytest`, `Trunk Check`), deletes `repo-autorebase.yml`, and slims `repo-automerge.yml` to a one-shot auto-merge arm. This PR merges _the old way_. **Phase 2** flips the repository ruleset (enable merge queue, drop the strict up-to-date policy) — done **after** Phase 1 has merged, so the very first merge group already has workflows that report on `merge_group`. Then a live verification checklist proves the queue works end to end.

**Tech Stack:** GitHub Actions YAML, GitHub Rulesets API (`gh api`), `actions/github-script`, GraphQL `enablePullRequestAutoMerge`.

**Spec:** [docs/superpowers/specs/2026-06-10-merge-queue-design.md](../specs/2026-06-10-merge-queue-design.md)

---

## Pre-flight facts (verified 2026-06-10, do not re-derive)

- Ruleset: id **13026107**, name `default`, target `branch`, enforcement `active`.
- Required status checks: `Trunk Check` (integration_id 15368) and `pytest` (integration_id 15368), with `strict_required_status_checks_policy: true`.
- `pull_request` rule: `required_approving_review_count: 0` → full-auto merge needs **no** human approval. `required_review_thread_resolution: true` (unresolved review threads still block — expected).
- Other rules: `deletion`, `non_fast_forward`, `required_linear_history`, `code_scanning` (CodeQL **default setup**, GitHub-managed — no workflow file).
- No `.github/settings.yml` → ruleset is **not** managed as IaC; Phase 2 edits it via the GitHub API (or UI).
- `ci-lint.yml` job `trunk` (the `Trunk Check` required check) already gates its auto-commit step with `if: github.event_name == 'pull_request'`, so it is already skipped outside PRs. The `Fail if formatting fixes were needed` step keys off that skipped step's output, so it too is inert on `merge_group`.

---

## File Structure

- **Modify** `.github/workflows/ci-test.yml` — add `merge_group:` trigger so the `pytest` required check reports on merge groups.
- **Modify** `.github/workflows/ci-lint.yml` — add `merge_group:` trigger; neutralize `Trunk Format` on `merge_group` so `trunk check` validates the real merged tree.
- **Delete** `.github/workflows/repo-autorebase.yml` — superseded by the queue's temporary branches.
- **Rewrite** `.github/workflows/repo-automerge.yml` — collapse the 105-line re-arming logic to a one-shot "enable auto-merge (= enqueue when green)".
- **Ruleset 13026107** (Phase 2, not a file) — add a `merge_queue` rule; set `strict_required_status_checks_policy: false`.

---

## Phase 1 — The migration PR (merges the old way)

### Task 1: Branch from latest main

**Files:** none (git only)

- [ ] **Step 1: Sync and branch**

The current branch already exists in a worktree. Ensure it is based on the latest `main` to avoid the auto-rebase + squash no-op trap (see CLAUDE.md "Git workflow").

Run:

```bash
git fetch origin main
git rebase origin/main
```

Expected: `Successfully rebased` or `Current branch ... is up to date`.

---

### Task 2: Add `merge_group` trigger to `ci-test.yml`

**Files:**

- Modify: `.github/workflows/ci-test.yml` (the `on:` block, lines 3-10)

- [ ] **Step 1: Edit the `on:` block**

Replace:

```yaml
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  workflow_dispatch:
```

with:

```yaml
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  merge_group:
  workflow_dispatch:
```

- [ ] **Step 2: Validate YAML parses**

Run:

```bash
python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci-test.yml')); print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Confirm the trigger landed**

Run:

```bash
grep -n "merge_group" .github/workflows/ci-test.yml
```

Expected: one line showing the `merge_group:` trigger.

---

### Task 3: Add `merge_group` trigger to `ci-lint.yml` and make `trunk check` authoritative in the queue

**Files:**

- Modify: `.github/workflows/ci-lint.yml` (the `on:` block, lines 3-8; the `Trunk Format` step)

**Why the `Trunk Format` change:** on `merge_group`, `github.head_ref` is empty and the branch is the ephemeral `gh-readonly-queue/...`. The auto-commit step is already gated to `pull_request` (so it is skipped), but `Trunk Format` (`trunk fmt`) would still rewrite the working tree before `trunk check` runs — making the check pass against a locally-reformatted tree instead of the real merged code. Skipping `fmt` on `merge_group` makes `trunk check` authoritative over the actual merge result.

- [ ] **Step 1: Edit the `on:` block**

Replace:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

with:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  merge_group:
  workflow_dispatch:
```

- [ ] **Step 2: Gate `Trunk Format` off on `merge_group`**

Replace:

```yaml
- name: Trunk Format
  run: ${{ env.TRUNK_PATH }} fmt
```

with:

```yaml
- name: Trunk Format
  if: github.event_name != 'merge_group'
  run: ${{ env.TRUNK_PATH }} fmt
```

- [ ] **Step 3: Validate YAML parses**

Run:

```bash
python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci-lint.yml')); print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Confirm both edits landed**

Run:

```bash
grep -n "merge_group\|if: github.event_name != 'merge_group'" .github/workflows/ci-lint.yml
```

Expected: the `merge_group:` trigger line **and** the `if:` on `Trunk Format`.

---

### Task 4: Delete `repo-autorebase.yml`

**Files:**

- Delete: `.github/workflows/repo-autorebase.yml`

- [ ] **Step 1: Remove the workflow**

Run:

```bash
git rm .github/workflows/repo-autorebase.yml
```

Expected: `rm '.github/workflows/repo-autorebase.yml'`

---

### Task 5: Slim `repo-automerge.yml` to a one-shot auto-merge arm

**Files:**

- Rewrite: `.github/workflows/repo-automerge.yml`

**Why:** with the queue active, "enable auto-merge" means "add to the merge queue once required checks pass." There is no longer any force-push `synchronize` from auto-rebase to desync the armed state, so the disable/re-enable/direct-merge dance and the `workflow_run` re-arming are all unnecessary. The `autorelease: pending` exclusion is dropped — release PRs flow through the queue (spec choice A).

- [ ] **Step 1: Replace the file contents**

Write `.github/workflows/repo-automerge.yml` with exactly:

```yaml
name: Repo / Auto-merge

# Arm native auto-merge once when a PR opens or becomes ready. With the merge
# queue enabled on `main`, an armed PR is added to the queue automatically as
# soon as the required checks pass — the queue owns serialization, so no
# re-arming logic is needed. Release-please PRs flow through the queue like any
# other PR (no `autorelease: pending` exclusion).
on:
  pull_request_target:
    types: [opened, ready_for_review]

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

permissions:
  contents: read

jobs:
  automerge:
    runs-on: ubuntu-latest
    steps:
      - name: Generate GitHub App token
        id: generate-token
        uses: actions/create-github-app-token@1b10c78c7865c340bc4f6099eb2f838309f1e8c3 # v3.1.1
        with:
          client-id: ${{ secrets.REGIS_CI_APP_ID }}
          private-key: ${{ secrets.REGIS_CI_APP_PRIVATE_KEY }}

      - name: Enable auto-merge (enqueues when checks pass)
        uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea # v7.0.1
        with:
          github-token: ${{ steps.generate-token.outputs.token }}
          script: |
            const pr = context.payload.pull_request;
            if (pr.draft) {
              core.info(`#${pr.number}: draft, skipping`);
              return;
            }
            try {
              await github.graphql(
                `mutation ($id: ID!) {
                  enablePullRequestAutoMerge(input: { pullRequestId: $id, mergeMethod: SQUASH }) {
                    clientMutationId
                  }
                }`,
                { id: pr.node_id },
              );
              core.info(`#${pr.number}: auto-merge enabled (will enqueue when green)`);
            } catch (e) {
              // A PR that is already CLEAN with no pending checks rejects
              // enablement ("Pull request is in clean status"); enqueue it.
              core.info(`#${pr.number}: enable failed (${e.message})`);
              throw e;
            }
```

- [ ] **Step 2: Validate YAML parses**

Run:

```bash
python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/repo-automerge.yml')); print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Confirm the re-arming machinery is gone**

Run:

```bash
grep -c "workflow_run\|disablePullRequestAutoMerge\|merge_method: 'squash'\|autorelease: pending" .github/workflows/repo-automerge.yml
```

Expected: `0`

---

### Task 6: Lint the workflows (if `actionlint` is available)

**Files:** none

- [ ] **Step 1: Run actionlint when present**

Run:

```bash
command -v actionlint >/dev/null && actionlint .github/workflows/ci-test.yml .github/workflows/ci-lint.yml .github/workflows/repo-automerge.yml || echo "actionlint not installed — skipping (YAML already validated)"
```

Expected: no findings, or the skip message.

---

### Task 7: Commit Phase 1

**Files:** none (git)

- [ ] **Step 1: Stage and commit**

Trunk's pre-commit hook may auto-format — if it does, re-stage and commit the result (see CLAUDE.md).

Run:

```bash
git add .github/workflows/ci-test.yml .github/workflows/ci-lint.yml .github/workflows/repo-automerge.yml
git rm --cached --ignore-unmatch .github/workflows/repo-autorebase.yml
git commit -m "ci: adopt native merge queue, retire auto-rebase

Add the merge_group trigger to the two required checks (pytest, Trunk
Check), delete repo-autorebase.yml, and collapse repo-automerge.yml to a
one-shot auto-merge arm. The repository ruleset is switched to merge-queue
mode in a follow-up step, after this PR merges, so the first merge group
already has workflows reporting on merge_group.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: a commit with 3 modified + 1 deleted workflow.

- [ ] **Step 2: Delete the plan from the branch before pushing**

Plans must not land on `main` (they break the "No Execution Plans" guard). Remove this plan from the branch before the PR merges (specs survive, plans are ephemeral):

```bash
git rm docs/superpowers/plans/2026-06-10-merge-queue.md
git commit -m "chore: drop execution plan before merge"
```

Expected: plan removed. (Keep a copy outside the repo if you still need it during execution.)

- [ ] **Step 3: Push and open the PR**

Run:

```bash
git push -u origin "$(git branch --show-current)"
gh pr create --fill --base main
```

Expected: PR URL printed.

- [ ] **Step 4: Let the PR merge the OLD way**

This PR still merges under the current rules (auto-rebase + auto-merge are still live until it lands). Confirm it merges to `main` before starting Phase 2.

Run:

```bash
gh pr view --json state,mergedAt
```

Expected: `"state": "MERGED"` with a non-null `mergedAt`. **Do not start Phase 2 until this is MERGED.**

---

## Phase 2 — Ruleset cutover (after Phase 1 is merged)

> ⚠️ **Outward-facing repository config change.** Confirm with the maintainer before applying. This changes how every PR merges. The change is reversible (Task 10).

### Task 8: Enable the merge queue and drop the strict policy on ruleset 13026107

**Files:** none (GitHub Rulesets API)

**Approach:** dump the live ruleset, transform it with `jq` (add a `merge_queue` rule, flip `strict_required_status_checks_policy` to `false`), and `PUT` it back. The dump-transform-PUT keeps every other rule byte-for-byte intact.

- [ ] **Step 1: Dump the current ruleset and back it up**

Run:

```bash
gh api repos/trivoallan/regis/rulesets/13026107 > /tmp/ruleset.before.json
cp /tmp/ruleset.before.json /tmp/ruleset.backup.json
jq '.rules | map(.type)' /tmp/ruleset.before.json
```

Expected: a list including `"required_status_checks"` and **not** `"merge_queue"`.

- [ ] **Step 2: Build the updated ruleset payload**

Run:

```bash
jq '
  {name, target, enforcement, conditions, rules, bypass_actors}
  | .rules = (
      [ .rules[]
        | if .type == "required_status_checks"
          then .parameters.strict_required_status_checks_policy = false
          else . end ]
      + [{
          type: "merge_queue",
          parameters: {
            merge_method: "SQUASH",
            grouping_strategy: "ALLGREEN",
            max_entries_to_build: 5,
            min_entries_to_merge: 1,
            max_entries_to_merge: 5,
            min_entries_to_merge_wait_minutes: 5,
            check_response_timeout_minutes: 60
          }
        }]
    )
' /tmp/ruleset.before.json > /tmp/ruleset.after.json
jq '.rules | map(.type)' /tmp/ruleset.after.json
jq '.rules[] | select(.type=="required_status_checks") | .parameters.strict_required_status_checks_policy' /tmp/ruleset.after.json
```

Expected: the type list now includes `"merge_queue"`, and the strict policy prints `false`.

- [ ] **Step 3: Apply the updated ruleset**

Run:

```bash
gh api --method PUT repos/trivoallan/regis/rulesets/13026107 --input /tmp/ruleset.after.json > /tmp/ruleset.applied.json
echo "applied:"; jq '.rules[] | select(.type=="merge_queue") | .parameters' /tmp/ruleset.applied.json
```

Expected: the response echoes the `merge_queue` parameters. If the API rejects the payload, fall back to the UI: **Repo → Settings → Rules → `default` ruleset → enable "Merge queue" (Squash, ALLGREEN) and uncheck "Require branches to be up to date before merging" → Save.**

- [ ] **Step 4: Verify the live ruleset**

Run:

```bash
gh api repos/trivoallan/regis/rulesets/13026107 \
  --jq '{merge_queue: (.rules[]|select(.type=="merge_queue")|.parameters.merge_method), strict: (.rules[]|select(.type=="required_status_checks")|.parameters.strict_required_status_checks_policy)}'
```

Expected: `{"merge_queue":"SQUASH","strict":false}`

---

### Task 9: Live verification (prove the queue works)

**Files:** none

- [ ] **Step 1: Single trivial PR through the queue**

Create a one-line change on a throwaway branch, open a PR, and let `repo-automerge.yml` arm it.

```bash
git checkout -b mq-smoke-1 origin/main
printf '\n<!-- merge-queue smoke 1 -->\n' >> README.md
git add README.md && git commit -m "test: merge queue smoke 1"
git push -u origin mq-smoke-1
gh pr create --fill --base main
```

Expected: PR opened; within ~1 min `gh pr view mq-smoke-1 --json autoMergeRequest` shows auto-merge enabled.

- [ ] **Step 2: Confirm the merge group runs the required checks**

Watch the queue. Once the PR enters the queue, a `merge_group` run of `CI / Test` and `CI / Lint` must appear.

```bash
gh run list --event merge_group --limit 5
```

Expected: rows for `CI / Test` and `CI / Lint` triggered by `merge_group`, both succeeding. **If a run never appears and the PR sits in the queue, that is the "stuck group" failure — a required check is not reporting on `merge_group`; revisit Tasks 2-3.**

- [ ] **Step 3: Confirm squash-merge + linear history**

Run:

```bash
gh pr view mq-smoke-1 --json state,mergedAt
git fetch origin main && git log --oneline origin/main -3
```

Expected: PR `MERGED`; `main` advanced by a single squash commit (linear history preserved).

- [ ] **Step 4: Two concurrent PRs — speculative test, no branch force-push**

```bash
git checkout -b mq-smoke-2 origin/main
printf '\n<!-- smoke 2 -->\n' >> README.md && git add README.md && git commit -m "test: smoke 2"
git push -u origin mq-smoke-2 && gh pr create --fill --base main

git checkout -b mq-smoke-3 origin/main
printf '\n<!-- smoke 3 -->\n' >> README.md && git add README.md && git commit -m "test: smoke 3"
git push -u origin mq-smoke-3 && gh pr create --fill --base main
```

Record each branch head, then after both merge confirm the local heads were never rewritten by a bot:

```bash
git fetch origin
git rev-parse origin/mq-smoke-2 origin/mq-smoke-3 2>/dev/null || echo "branches deleted on merge (expected)"
```

Expected: both PRs merge in queue order; neither PR branch received a force-push from `repo-autorebase` (it no longer exists). `gh run list --event merge_group` shows the speculative groups.

- [ ] **Step 5: CodeQL default setup does not stall the queue**

CodeQL is GitHub default setup (no workflow file) and supports merge queue natively, but confirm it is not blocking groups.

```bash
gh run list --event merge_group --limit 10
```

Expected: no merge group is stuck waiting on a code-scanning check. If one is, open **Settings → Code security → Code scanning** and confirm default setup is enabled for merge queue (or add `merge_group` to the analysis triggers).

- [ ] **Step 6: First release-please PR post-cutover**

This is validated opportunistically on the next release PR (not a step you force now). When the next `release-please` PR opens, confirm it is auto-armed, traverses the queue, merges, and tags. Note the result in `docs/memory-bank/progress.md`.

---

### Task 10: Rollback procedure (only if verification fails)

**Files:** none

- [ ] **Step 1: Restore the ruleset**

Run:

```bash
gh api --method PUT repos/trivoallan/regis/rulesets/13026107 --input /tmp/ruleset.backup.json
```

Expected: the merge queue rule removed, strict policy back to `true`.

- [ ] **Step 2: Restore the workflows**

Run:

```bash
git revert --no-edit <phase-1-merge-commit-sha>
```

Expected: `repo-autorebase.yml` and the original `repo-automerge.yml` restored; PR branches were never modified by the queue, so no data is lost.

---

## Post-cutover housekeeping

- [ ] Update `docs/memory-bank/systemPatterns.md` and `progress.md`: the auto-rebase + auto-merge re-arming gotchas are obsolete; record that merge is now queue-driven (Squash, ALLGREEN, strict policy off).
- [ ] Review whether the existing memory note "Le bot auto-rebase réécrit les branches de PR" should be marked resolved.
- [ ] Delete the smoke branches/PRs if any artifacts remain.
