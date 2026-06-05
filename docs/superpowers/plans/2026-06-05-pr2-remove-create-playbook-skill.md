# PR2 — Remove the `/create-playbook` Claude skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the product-facing `/create-playbook` Claude skill and repoint its documentation to the existing `regis bootstrap playbook` path.

**Architecture:** Deletion + doc edit. The skill is not a packaged artifact (absent from `pyproject.toml` / `MANIFEST.in`), so there is no version impact and no code/test change. The replacement path — `regis bootstrap playbook` — already exists.

**Tech Stack:** Markdown skill files, Docusaurus docs, project `CLAUDE.md`.

**Spec:** `docs/superpowers/specs/2026-06-05-feature-pruning-design.md` (§3).

**Branch:** fresh branch off the latest `main`.

---

## Task 1: Delete the skill and fix its references

**Files:**

- Delete: `.claude/skills/create-playbook/` (tree: `SKILL.md`, `references/available-rules.md`, `references/playbook-examples.md`)
- Modify: `docs/website/docs/usage/custom-playbook.md` (remove the AI-assistant section; promote the manual bootstrap path)
- Modify: `CLAUDE.md` (remove `/create-playbook` from the project-skills list, l. 64)

- [ ] **Step 1: Delete the skill tree**

Run:

```bash
git rm -r .claude/skills/create-playbook
```

- [ ] **Step 2: Rewrite the doc section in `custom-playbook.md`**

Open `docs/website/docs/usage/custom-playbook.md`. Remove the section `## Create a playbook with the AI assistant` (currently l. 14–84, ending where `## Bootstrap a skeleton manually` begins).

Promote the manual path to be the primary entry. Right after the intro paragraph (ending "…tailored to your organisation's needs."), insert a short lead-in so the page flows into the bootstrap section:

```markdown
The fastest way to start a custom playbook is to scaffold a skeleton with the
CLI, then edit it to match your policy.
```

Then ensure the next heading is `## Bootstrap a skeleton manually` (it already exists at the old l. 84). Leave the rest of the page (structure, run, dry-run sections) untouched, including any `--html` references.

- [ ] **Step 3: Remove the skill from `CLAUDE.md`**

Open `CLAUDE.md`. On line 64, the project-skills list reads:

```text
composed with project skills (`/create-playbook`, `/verify`, `/code-review`, `/init`)
```

Edit it to drop `/create-playbook`:

```text
composed with project skills (`/verify`, `/code-review`, `/init`)
```

- [ ] **Step 4: Verify no dangling references in current docs/config**

Run: `grep -rn "create-playbook" CLAUDE.md docs/website/docs/ | grep -v versioned_docs`
Expected: no matches.

Note: `docs/website/versioned_docs/**` and `docs/memory-bank/**` reference it historically — leave them intact.

- [ ] **Step 5: Build the docs to confirm no broken links**

Run the Docusaurus build for `docs/website` and confirm `custom-playbook.md` builds without broken anchors/links.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore(skills): remove the create-playbook Claude skill

The skill overlapped `regis bootstrap playbook`, which now stands as the
documented path for scaffolding a custom playbook. Removes repo coupling
to a proprietary tool for this function. Updates custom-playbook.md and
the CLAUDE.md project-skills list accordingly.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Final verification & PR

- [ ] **Step 1: Sanity-check the suite is unaffected**

Run: `pipenv run pytest --no-cov -q`
Expected: PASS (no code touched; this only confirms nothing referenced the skill from test/code paths).

- [ ] **Step 2: Run trunk**

Run: `trunk check`
Expected: green (commit any auto-fixes, e.g. Markdown table reflow).

- [ ] **Step 3: Open the PR**

Push the branch and open a PR titled `chore(skills): remove the create-playbook skill`. No version bump expected (not a packaged artifact). Note in the description that this resolves the tracked follow-up "the `/create-playbook` skill still emits `rule:`" (made moot by deletion).
