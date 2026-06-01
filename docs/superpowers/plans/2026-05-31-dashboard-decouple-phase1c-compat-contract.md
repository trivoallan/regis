# Phase 1c — Runtime schemaVersion Compatibility + Cross-Repo Contract Test — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `regis-dashboard` gate rendering on the report's integer `schemaVersion` at runtime, and add a cross-repo contract test so the dashboard's CI fails loudly if the core's report contract drifts beyond what this dashboard supports.

**Architecture:** A pure `checkSchemaCompat(schemaVersion)` function declares the dashboard's supported range and returns one of `ok` / `best-effort` / `unsupported`. `ReportProvider` calls it right after parsing `report.json`: `unsupported` routes to the existing error UI (no broken render); `best-effort` (missing `schemaVersion`, treated as 0) renders with a non-blocking banner; `ok` renders normally. Two layers of contract testing: an **offline** vitest test asserts the committed demo report (the core's `report.v1.json`) is `ok`, and a **live** scheduled CI job fetches the core's fixture from GitHub and re-asserts, catching drift between the two repos.

**Tech Stack:** TypeScript, React 19, vitest (introduced in 1b), GitHub Actions.

---

## Prerequisites & scope

**Depends on:** Phase 1a (standalone repo) **and** Phase 1b (vitest + the CLI). This plan runs **in the `regis-dashboard` repo**.

**This is Phase 1c of three** (see `docs/superpowers/specs/2026-05-31-dashboard-full-decouple-design.md`). It implements the spec's runtime-only compatibility model: _"Enforcement is 100% runtime, dashboard-side… The dashboard declares the schemaVersion range each release can render."_ and the cross-repo contract test: _"regis-dashboard CI fetches these fixtures (raw GitHub URL pinned to a tag) and asserts the render works."_

**Spec rules implemented here:**

- `schemaVersion` out of range → explicit message, never a silently broken render.
- `schemaVersion` absent → treat as `0`, show "predates schema versioning, best-effort" rather than crash.
- The dashboard owns all compatibility logic; the core emits and never gates.

## File structure (new/changed files)

```text
regis-dashboard/
  src/lib/
    schemaCompat.ts                 # SUPPORTED_SCHEMA_VERSION + checkSchemaCompat()  (NEW)
    __tests__/
      schemaCompat.test.ts          # unit tests for the pure function           (NEW)
      contract.test.ts              # offline: demo report (static/report.json) is ok (NEW)
  src/components/ReportProvider.tsx  # wire the check + warning state            (MODIFIED)
  vitest.config.ts                   # broaden include to src/**                  (MODIFIED)
  .github/workflows/contract.yml     # live cross-repo drift check                (NEW)
```

---

### Task 1: The `checkSchemaCompat` pure function (TDD)

**Files:**

- Create: `src/lib/schemaCompat.ts`
- Test: `src/lib/__tests__/schemaCompat.test.ts`
- Modify: `vitest.config.ts` (broaden test include beyond `src/cli/`)

- [ ] **Step 1: Broaden the vitest include**

In `vitest.config.ts` (created in 1b, currently `include: ["src/cli/__tests__/**/*.test.ts"]`), change `include` to:

```ts
    include: ["src/**/__tests__/**/*.test.ts"],
```

This keeps the CLI tests and also picks up `src/lib/__tests__/`.

- [ ] **Step 2: Write the failing tests**

`src/lib/__tests__/schemaCompat.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { checkSchemaCompat, SUPPORTED_SCHEMA_VERSION } from "../schemaCompat";

describe("checkSchemaCompat", () => {
  it("accepts a version inside the supported range", () => {
    const r = checkSchemaCompat(SUPPORTED_SCHEMA_VERSION.min);
    expect(r.mode).toBe("ok");
    expect(r.message).toBeNull();
  });

  it("treats a missing version as best-effort (predates versioning)", () => {
    const r = checkSchemaCompat(undefined);
    expect(r.mode).toBe("best-effort");
    expect(r.message).toMatch(/predates schema versioning/i);
  });

  it("treats schemaVersion 0 as best-effort", () => {
    expect(checkSchemaCompat(0).mode).toBe("best-effort");
  });

  it("rejects a version above the supported range with an explicit message", () => {
    const tooNew = SUPPORTED_SCHEMA_VERSION.max + 1;
    const r = checkSchemaCompat(tooNew);
    expect(r.mode).toBe("unsupported");
    expect(r.message).toContain(String(tooNew));
    expect(r.message).toContain(String(SUPPORTED_SCHEMA_VERSION.max));
  });

  it("uses an injectable range for testing future windows", () => {
    expect(checkSchemaCompat(2, { min: 1, max: 3 }).mode).toBe("ok");
    expect(checkSchemaCompat(4, { min: 1, max: 3 }).mode).toBe("unsupported");
  });
});
```

- [ ] **Step 3: Run to verify failure**

Run: `pnpm test -- schemaCompat`
Expected: FAIL — module `../schemaCompat` not found.

- [ ] **Step 4: Implement `src/lib/schemaCompat.ts`**

```ts
/** The schemaVersion range this dashboard release can render.
 *  Bump `max` when the dashboard adds support for a new report schemaVersion. */
export const SUPPORTED_SCHEMA_VERSION = { min: 1, max: 1 } as const;

export interface SchemaRange {
  min: number;
  max: number;
}

export interface CompatResult {
  mode: "ok" | "best-effort" | "unsupported";
  /** Non-null for best-effort (warning) and unsupported (error); null for ok. */
  message: string | null;
}

/** Decide whether this dashboard can render a report of the given schemaVersion.
 *  - undefined / 0  → best-effort (report predates schema versioning)
 *  - within [min,max] → ok
 *  - otherwise      → unsupported (explicit, actionable message) */
export function checkSchemaCompat(
  schemaVersion: number | undefined,
  range: SchemaRange = SUPPORTED_SCHEMA_VERSION,
): CompatResult {
  const v = schemaVersion ?? 0;
  if (v === 0) {
    return {
      mode: "best-effort",
      message:
        "This report predates schema versioning (no schemaVersion field); rendering is best-effort.",
    };
  }
  if (v < range.min || v > range.max) {
    return {
      mode: "unsupported",
      message:
        `This report uses schemaVersion ${v}; this dashboard supports ${range.min}–${range.max}. ` +
        `Use a newer regis-dashboard image, or regenerate the report with a compatible regis version.`,
    };
  }
  return { mode: "ok", message: null };
}
```

- [ ] **Step 5: Run to verify pass**

Run: `pnpm test -- schemaCompat`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add src/lib/schemaCompat.ts src/lib/__tests__/schemaCompat.test.ts vitest.config.ts
git commit -m "feat(compat): add checkSchemaCompat with declared supported range"
```

---

### Task 2: Wire the compat check into `ReportProvider`

**Files:**

- Modify: `src/components/ReportProvider.tsx`

The current provider (recon'd) has:

- a `ReportData` interface (with `version?: string`, no `schemaVersion`),
- a context `{ report, loading, error, reportUrl }`,
- a fetch `.then((data) => { if (Array.isArray(data)) {…return;} setReport(data); setError(null); setLoading(false); })`.

We add a `schemaVersion` field, a `warning` channel, and call `checkSchemaCompat` between the array guard and `setReport`.

- [ ] **Step 1: Add `schemaVersion` to `ReportData`**

In the `ReportData` interface, add (next to `version?: string;`):

```ts
  schemaVersion?: number;
```

- [ ] **Step 2: Add `warning` to the context type, default, and `useReport`**

Change the `ReportContextValue` interface (currently `{ report, loading, error, reportUrl }`) to add:

```ts
warning: string | null;
```

Update the `createContext<ReportContextValue>({ … })` default to include `warning: null,`.

- [ ] **Step 3: Add warning state and import the checker**

At the top of `ReportProvider.tsx`, add the import:

```ts
import { checkSchemaCompat } from "../lib/schemaCompat";
```

Inside `ReportProvider`, alongside the existing `useState` calls, add:

```ts
const [warning, setWarning] = useState<string | null>(null);
```

- [ ] **Step 4: Insert the compat check and route the three outcomes**

Replace the post-array-guard block (currently the three lines `setReport(data); setError(null); setLoading(false);` immediately after the `if (Array.isArray(data)) { … return; }`) with:

```ts
const compat = checkSchemaCompat(data.schemaVersion);
if (compat.mode === "unsupported") {
  setError(compat.message);
  setReport(null);
  setLoading(false);
  return;
}
setWarning(compat.mode === "best-effort" ? compat.message : null);
setReport(data);
setError(null);
setLoading(false);
```

- [ ] **Step 5: Surface `warning` in the provider output (non-blocking banner)**

Change the provider return so the warning renders above children and `warning` is exposed in context:

```tsx
return (
  <ReportContext.Provider
    value={{ report, loading, error, warning, reportUrl }}
  >
    {warning && (
      <div
        role="status"
        style={{
          background: "#fef3c7",
          color: "#92400e",
          padding: "0.5rem 1rem",
          fontSize: "0.875rem",
          borderBottom: "1px solid #f59e0b",
        }}
      >
        {warning}
      </div>
    )}
    {children}
  </ReportContext.Provider>
);
```

- [ ] **Step 6: Verify typecheck + build**

```bash
pnpm typecheck
pnpm build
```

Expected: both pass. (No new unit test here — the logic under test is `checkSchemaCompat`, covered in Task 1; this task is the wiring, validated by typecheck/build and the contract test in Task 3.)

- [ ] **Step 7: Commit**

```bash
git add src/components/ReportProvider.tsx
git commit -m "feat(compat): gate rendering on report schemaVersion in ReportProvider"
```

---

### Task 3: Offline contract test against the committed demo report

**Files:**

- Create: `src/lib/__tests__/contract.test.ts`

The demo `static/report.json` committed in Phase 1a **is** the core's `report.v1.json`. Asserting it is `ok` guarantees the dashboard's `SUPPORTED_SCHEMA_VERSION` includes the core's current contract — deterministically, offline, on every test run.

- [ ] **Step 1: Write the test**

`src/lib/__tests__/contract.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { checkSchemaCompat } from "../schemaCompat";

describe("contract: committed demo report", () => {
  it("static/report.json is renderable by this dashboard (mode 'ok')", () => {
    const report = JSON.parse(
      readFileSync(resolve(__dirname, "../../../static/report.json"), "utf8"),
    );
    expect(typeof report.schemaVersion).toBe("number");
    const compat = checkSchemaCompat(report.schemaVersion);
    expect(compat.mode).toBe("ok");
  });
});
```

(Adjust the relative path if `src/lib/__tests__/` is not three levels under the repo root — `resolve(__dirname, ...)` should point at `<repo>/static/report.json`.)

- [ ] **Step 2: Run to verify pass**

Run: `pnpm test -- contract`
Expected: PASS — the demo report's `schemaVersion` (1) is within `SUPPORTED_SCHEMA_VERSION`.

If it FAILS because `static/report.json` is missing, Phase 1a Task 4 was not completed — stop and report (this plan depends on it).

- [ ] **Step 3: Commit**

```bash
git add src/lib/__tests__/contract.test.ts
git commit -m "test(compat): offline contract test against committed demo report"
```

---

### Task 4: Live cross-repo drift check (CI)

**Files:**

- Create: `.github/workflows/contract.yml`

The offline test (Task 3) only guards the _committed snapshot_. This workflow fetches the **live** core fixture from GitHub and re-asserts compat, so if the core bumps `schemaVersion` beyond this dashboard's range, the dashboard repo gets a failing signal (scheduled + on every push).

- [ ] **Step 1: Add a tiny assertion script** — `scripts/check-contract.mjs`:

```js
// Fetches the core's report.v1 fixture and asserts this dashboard supports its schemaVersion.
import { readFileSync } from "node:fs";

const fixtureUrl =
  process.env.CORE_FIXTURE_URL ??
  "https://raw.githubusercontent.com/trivoallan/regis/main/tests/fixtures/report.v1.json";

// Read the dashboard's supported range straight from source (single source of truth).
// (Do not shadow the global URL constructor — it is needed for the import.meta.url resolve.)
const srcPath = new URL("../src/lib/schemaCompat.ts", import.meta.url);
const src = readFileSync(srcPath, "utf8");
const min = Number(/min:\s*(\d+)/.exec(src)?.[1]);
const max = Number(/max:\s*(\d+)/.exec(src)?.[1]);

const res = await fetch(fixtureUrl);
if (!res.ok) {
  console.error(
    `Failed to fetch core fixture: ${res.status} ${res.statusText}`,
  );
  process.exit(2);
}
const report = await res.json();
const v = report.schemaVersion ?? 0;

if (v < min || v > max) {
  console.error(
    `DRIFT: core report.v1 schemaVersion=${v} is outside this dashboard's supported range ${min}-${max}. ` +
      `Bump SUPPORTED_SCHEMA_VERSION.max in src/lib/schemaCompat.ts and add render support.`,
  );
  process.exit(1);
}
console.log(
  `OK: core schemaVersion ${v} is within supported range ${min}-${max}.`,
);
```

- [ ] **Step 2: Add the workflow** — `.github/workflows/contract.yml`:

```yaml
name: Cross-repo contract

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1" # weekly Monday 06:00 UTC — catches core drift between PRs
  workflow_dispatch:

permissions:
  contents: read

jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: node scripts/check-contract.mjs
```

- [ ] **Step 3: Local dry-run**

```bash
node scripts/check-contract.mjs
```

Expected: prints `OK: core schemaVersion 1 is within supported range 1-1.` (requires network and that the core `main` has `tests/fixtures/report.v1.json` — i.e. PR #630 is merged. If the fixture 404s, this exits 2 — see watch-points.)

- [ ] **Step 4: Commit**

```bash
git add scripts/check-contract.mjs .github/workflows/contract.yml
git commit -m "ci: add live cross-repo schemaVersion drift check"
```

---

### Task 5: Wire the contract test into PR CI + document the bump procedure

**Files:**

- Modify: `.github/workflows/ci.yml`, `README.md`

- [ ] **Step 1: Ensure `pnpm test` (now including schemaCompat + contract) runs in PR CI**

`pnpm test` already runs in `ci.yml` (added in Phase 1b Task 10). Confirm the contract + compat tests are picked up by the broadened vitest `include`:

```bash
pnpm test 2>&1 | grep -E "schemaCompat|contract"
```

Expected: both test files appear and pass. No CI change needed if 1b already added `pnpm test`; if not, add it.

- [ ] **Step 2: Document the compatibility contract in the README**

Replace the README "Contract" section (from Phase 1a) with the concrete mechanism:

```markdown
## Report compatibility

This dashboard renders regis reports identified by an integer `schemaVersion`.
The supported range is declared in `src/lib/schemaCompat.ts`
(`SUPPORTED_SCHEMA_VERSION`). At runtime:

- in range → renders normally;
- no `schemaVersion` (legacy report) → renders best-effort with a banner;
- out of range → shows an explicit upgrade message instead of a broken view.

When the core ships a new report `schemaVersion`, bump
`SUPPORTED_SCHEMA_VERSION.max` and add any needed render handling. The
`Cross-repo contract` workflow fails if the core drifts past the supported range.
```

- [ ] **Step 3: Verify the whole suite**

```bash
pnpm install
pnpm typecheck
pnpm test
pnpm build
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml README.md
git commit -m "docs(compat): document schemaVersion contract and bump procedure"
```

---

## Self-review notes (reconciled against the spec)

- **Spec "enforcement 100% runtime, dashboard-side"** → Task 2 (`ReportProvider` calls `checkSchemaCompat` at fetch time; no build-time gate, no core involvement).
- **Spec "dashboard declares the supported range per release"** → `SUPPORTED_SCHEMA_VERSION` in `schemaCompat.ts` (Task 1), surfaced in the README bump procedure (Task 5).
- **Spec "out of range → explicit message, never silently broken"** → Task 1 `unsupported` message + Task 2 routing to the existing error UI (report stays null).
- **Spec "absent → treat as 0, best-effort"** → Task 1 `best-effort` branch + Task 2 non-blocking banner.
- **Spec "cross-repo contract test: CI fetches the fixture and asserts"** → Task 4 live drift workflow; Task 3 adds an offline deterministic guard against the committed snapshot.
- **Spec "core has zero compat logic"** → respected: nothing in this plan touches the core; all logic is dashboard-side.

## Risks / watch-points

- **Contract workflow gated on PR #630:** `scripts/check-contract.mjs` fetches `…/regis/main/tests/fixtures/report.v1.json`, which only exists once Phase 0 (PR #630) is merged to the core's `main`. Until then the live check exits 2 (fetch failure). The **offline** test (Task 3) does not depend on the core and passes immediately. Consider pinning the fetch URL to a tag once the core cuts the release that includes the fixture.
- **Range parsed by regex in the drift script:** `check-contract.mjs` greps `min:`/`max:` out of `schemaCompat.ts` to avoid a TS build step in CI. If that literal's formatting changes, the regex must still match — the `as const` object keeps `min: 1, max: 1` on one logical line; keep it greppable, or replace the script with a compiled import if it becomes fragile.
- **Warning banner styling:** Task 2 uses inline styles to avoid coupling to Tailwind/Tremor theme internals during extraction. A follow-up can restyle it with the design system; functionally it satisfies the spec's "show a message rather than crash."
- **`schemaVersion` typing:** the core emits an integer; `checkSchemaCompat` coerces `undefined`→0 but does not guard against non-numeric junk (e.g. a string). The core schema enforces integer, so a malformed value would already fail upstream; `ReportProvider`'s existing JSON-parse/`content-type` guards cover gross corruption.
