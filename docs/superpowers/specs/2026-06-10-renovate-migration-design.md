# Dependabot → Renovate migration — design

**Date:** 2026-06-10
**Status:** Approved (pending spec review)
**Scope:** Replace Dependabot with the Mend Renovate App on the core repo, define a
shared constellation preset, and onboard the three satellite repos.

## Problem

Dependency automation on `trivoallan/regis` is currently reduced to a
security-only trickle:

- `.github/dependabot.yml` sets `open-pull-requests-limit: 0` on all four
  ecosystems (pip, npm, docker, github-actions) — **no version updates ever
  arrive**; dependencies only move when a human runs a manual batch (last one:
  M002/S05, 2026-04-22).
- Security updates are filtered down to critical-only by a custom workflow
  (`repo-dependabot-critical-vulns.yml`) that closes any Dependabot PR with
  CVSS < 9.0 — non-critical vulnerabilities are deliberately left unfixed.
- GitHub Actions SHA-pins are refreshed manually with `pinact`.
- Each constellation repo (`regis-gitlab`, `regis-backstage`, `regis-action`)
  would need its own `dependabot.yml`; nothing is shared.
- Dependabot-specific CI gotchas (no secrets on `pull_request`, hence
  `pull_request_target`) add complexity documented in `systemPatterns.md`.

## Goals

1. **Enable version updates** — grouped, low-noise, automerged where safe.
2. **Better ecosystem support** — mature `uv.lock` handling, pnpm workspaces,
   Docker digest pinning, GitHub Actions SHA-pin maintenance (replaces `pinact`).
3. **Constellation-wide policy** — one shared preset extended by all repos.
4. **Less CI bricolage** — delete the critical-vulns filter workflow and retire
   the Dependabot secrets gotcha.

## Non-goals

- `.trunk/trunk.yaml` linter versions (Trunk has its own upgrade mechanism).
- Per-satellite differentiated policies (native Renovate override mechanism is
  enough if a satellite ever needs one).
- A permanent CI job validating the Renovate config (the Mend app surfaces
  config errors in the Dependency Dashboard; a one-shot local validation at
  implementation time suffices).
- Keeping the critical-only security policy (superseded — see Security flow).

## Decisions

| Decision                   | Choice                                                                                                                                                                                       |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hosting                    | **Mend Renovate App** (hosted, free for public repos). Reversible to self-hosted `renovatebot/github-action` + the existing REGIS CI app without config changes.                             |
| Update policy              | Grouped weekly PRs per ecosystem; automerge patch/minor/pin/digest; majors as individual **draft** PRs requiring human action.                                                               |
| Security policy            | All severities, immediate (off-schedule), automerged. The CVSS ≥ 9.0 filter and its workflow are removed.                                                                                    |
| Shared config architecture | Preset hosted **in the core repo** (`.github/renovate-constellation.json5`); satellites extend it by path. Matches the existing "core defines the contract" pattern (e.g. `report.v1.json`). |
| Major-PR guard             | `draftPR: true` on majors. Reuses the existing exclusions (repo-automerge skips drafts, repo-autorebase has `exclude-drafts`) — zero changes to the automerge workflow.                      |

## Architecture

### Files (core repo)

| File                                                   | Role                                                                                                                                                                                            |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.github/renovate-constellation.json5`                 | **Shared preset**: full common policy (schedule, grouping, automerge, security, semantic commits). Referenced by satellites as `github>trivoallan/regis//.github/renovate-constellation.json5`. |
| `.github/renovate.json5`                               | Core repo config: extends the preset; no core-specific overrides expected.                                                                                                                      |
| `.github/dependabot.yml`                               | **Deleted.**                                                                                                                                                                                    |
| `.github/workflows/repo-dependabot-critical-vulns.yml` | **Deleted.**                                                                                                                                                                                    |
| `.github/workflows/repo-autorebase.yml`                | One-line change: `exclude-labels: dependencies`.                                                                                                                                                |

### Preset content (sketch)

```json5
// .github/renovate-constellation.json5
{
  $schema: "https://docs.renovatebot.com/renovate-schema.json",
  extends: [
    "config:best-practices", // recommended + docker:pinDigests + helpers:pinGitHubActionDigests + :configMigration + :pinDevDependencies
    "schedule:weekly",
  ],
  timezone: "Europe/Paris",
  labels: ["dependencies"], // keys the autorebase exclusion
  minimumReleaseAge: "3 days", // supply-chain guard: never take a <3-day-old release
  semanticCommits: "enabled",
  semanticCommitType: "build",
  semanticCommitScope: "deps", // → "build(deps): …"
  lockFileMaintenance: { enabled: true, automerge: true },
  osvVulnerabilityAlerts: true,
  // off-schedule, all severities; null age so fresh security fixes are not delayed
  vulnerabilityAlerts: { automerge: true, minimumReleaseAge: null },
  packageRules: [
    // workflow updates use the ci type regardless of update type → "ci(deps): …"
    { matchManagers: ["github-actions"], semanticCommitType: "ci" },
    // grouped non-major updates, automerged
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
    // majors: individual draft PRs, never automerged
    { matchUpdateTypes: ["major"], draftPR: true, automerge: false },
  ],
}
```

Exact option names/values to be finalized against the Renovate docs during
implementation (notably `draftPR` placement inside `packageRules`; fallback if
unsupported there: a `needs-review` label on majors plus one extra exclusion in
`repo-automerge.yml`, mirroring the `autorelease: pending` clause).

### Detected update surfaces (core)

- `pyproject.toml` + `uv.lock` (pep621 manager — single root project, the
  nominal uv case).
- pnpm workspaces: root (`pnpm-workspace.yaml` → `docs/website`) and
  `docs/website` itself.
- `Dockerfile`: 5 `FROM` lines gain `@sha256` digest pins
  (`python:3.11-alpine`, `curlimages/curl`).
- `.github/workflows/*.yml`: SHA-pinned actions maintained automatically
  (replaces manual `pinact` runs — process note added to docs).

## Security flow

- `vulnerabilityAlerts` + `osvVulnerabilityAlerts`: a vulnerability in any
  dependency triggers an **immediate** fix PR (outside the weekly schedule),
  all severities, automerged when CI is green.
- Rationale for dropping critical-only: the filter existed to cap review load;
  automerge absorbs that load, and fixing all severities is a strictly better
  posture for a supply-chain-focused project.
- **Prerequisite**: GitHub _Dependabot alerts_ (detection) stay **enabled** —
  they feed Renovate's `vulnerabilityAlerts`. Only _Dependabot security
  updates_ (the PR bot) is turned off in repo settings.

## Integration with existing automation

| Actor                 | Interaction                                                                                         | Action                                                                                       |
| --------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `repo-autorebase.yml` | A third-party rebase makes Renovate treat its branch as externally modified and stop maintaining it | Add `exclude-labels: dependencies`; Renovate rebases its own branches (`rebaseWhen` default) |
| `repo-automerge.yml`  | Arms native auto-merge (squash) on every non-draft PR without `autorelease: pending`                | **No change**: non-majors benefit from the existing re-arming; majors are drafts, skipped    |
| Release Please        | `build(deps)` / `ci(deps)` commits are changelog-hidden and trigger no version bump                 | None                                                                                         |
| Branch protection     | Required checks (CI / Test, CI / Lint) gate Renovate PRs like any other                             | None                                                                                         |
| Secrets gotcha        | Renovate PRs come from repo branches (not forks): plain `pull_request` workflows get secrets        | Update `systemPatterns.md` (Dependabot gotcha obsolete)                                      |

## Rollout

1. **Hygiene PR (separate, first)**: purge dead root JS surface — scripts
   referencing `@regis/ui`/`@regis/dashboard` (apps/ is empty), unused root
   dependencies (`gsd-pi`, `node-addon-api`, `node-gyp` — verify no real
   usage), orphan npm `package-lock.json` in a pnpm project. Otherwise
   Renovate will faithfully maintain the corpses.
2. **Core PR**: add `renovate.json5` + `renovate-constellation.json5`; delete
   `dependabot.yml` + `repo-dependabot-critical-vulns.yml`; add
   `exclude-labels` to the autorebase; update memory bank
   (`systemPatterns.md`, `techContext.md`) and any docs mentioning
   Dependabot/pinact. Validate config locally with
   `npx --package renovate renovate-config-validator`.
3. **Manual (maintainer)**: install the Mend Renovate App on all four repos;
   in core repo settings disable _Dependabot security updates_ (keep
   _alerts_).
4. **Satellite PRs** (one 3-line file each, after the core PR merges):

   ```json5
   // renovate.json5
   {
     $schema: "https://docs.renovatebot.com/renovate-schema.json",
     extends: ["github>trivoallan/regis//.github/renovate-constellation.json5"],
   }
   ```

   Satellites have no automerge/autorebase workflows; the preset's automerge
   rides on `platformAutomerge` (GitHub native auto-merge), which their
   existing branch protections already support.

## Validation criteria

1. Dependency Dashboard appears as a pinned issue with no config errors.
2. First weekly slot produces grouped per-ecosystem PRs with conformant
   `build(deps):` / `ci(deps):` titles.
3. A non-major PR merges **on its own** after green CI; a major PR arrives
   **as draft** and is not automerged.
4. Autorebase skips `dependencies`-labelled PRs on the next push to `main`.
5. Dockerfile and workflows receive digest pins via the initial pinning PR.

## Risks & mitigations

- **Renovate uv edge cases**: `lockFileMaintenance` on `uv.lock` has open bug
  reports (renovatebot/renovate discussion #37685); our single-root-project
  layout is the nominal case. Mitigation: disable `lockFileMaintenance` for
  the pep621 manager only if it misbehaves.
- **Large first wave** (months of frozen deps): contained by grouping and the
  default `prConcurrentLimit` (10).
- **Third-party runner** (Mend executes the bot): acceptable for public
  repos; reversible to self-hosted without config changes.
