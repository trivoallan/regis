# Phase 1b — regis-dashboard CLI & Docker Image — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a TypeScript CLI (`regis-dashboard`) to the standalone repo with `render`, `serve`, `archive add`, `archive configure`, and `bootstrap archive` commands, plus a published Docker image — porting the behavior currently in the Python core's `regis/report/docusaurus.py`, `regis/commands/archive.py`, `regis/commands/dashboard.py` (export), `regis/archive/store.py`, and the `archive` cookiecutter.

**Architecture:** A `commander`-based CLI compiled with `tsc` to `dist/`. Pure data logic (archive summary, archive store, archives.json config) lives in `src/cli/lib/` as side-effect-free functions, unit-tested with `vitest` against the core's `report.v1.json` fixture. The `render`/`serve` commands are thin wrappers that stage `report.json` into `static/`, set `REPORT_BASE_URL`, and shell out to the project's own `docusaurus build`/`serve`. The Docker image bundles the dashboard source + `node_modules` + the compiled CLI so `docker run regis-dashboard render /data/report.json` works offline.

**Tech Stack:** TypeScript, commander, vitest, Docusaurus 3.10 (the repo's own build), pnpm, Node ≥18, Docker (node:20-alpine), GitHub Actions, GHCR.

---

## Prerequisites & scope

**Depends on:** Phase 1a complete (the standalone `regis-dashboard` repo exists, builds, and deploys). This plan runs **in that repo**, not in a core worktree.

**This is Phase 1b of three** (see `docs/superpowers/specs/2026-05-31-dashboard-full-decouple-design.md`). 1a = extraction; **1b (this) = CLI + Docker**; 1c = runtime `schemaVersion` compat + cross-repo contract test. 1b introduces `vitest`, which 1c reuses.

**Ported behavior — source of truth in the core repo** (read these for exact semantics; do not import them — reimplement in TS):

- `regis/archive/store.py` → `add_to_archive`, `_make_summary`, `_calculate_status`, `_safe_segment`, `_load_json_array`.
- `regis/commands/archive.py` → `archive add` / `archive configure` CLI behavior + `_load_archives_config` / `_write_archives_config`.
- `regis/report/docusaurus.py` → `_build_from_source` (the `render` flow: stage report.json into `static/`, set `REPORT_BASE_URL`, run the build, ensure `report.json` lands at output root).
- `regis/commands/dashboard.py` → `export` (`-a Name:path` → `archives.json`) and the dropped `serve` (we keep only static preview).
- `regis/cookiecutters/archive/` → the 5 files `bootstrap archive` emits.

**Out of scope (1c):** the runtime `schemaVersion` gate in `ReportProvider`, the cross-repo contract test. **Dropped (decision):** the GitLab proxy / webhook backend — `serve` is static-preview-only.

## File structure (new files in the repo)

```text
regis-dashboard/
  src/cli/
    index.ts                  # commander entry; registers all commands; bin target
    lib/
      summary.ts              # makeSummary() + calculateStatus()  (port of _make_summary/_calculate_status)
      archiveStore.ts         # addToArchive()                     (port of add_to_archive)
      archivesConfig.ts       # load/add/remove/list/write archives.json (port of archive.py)
      paths.ts                # safeSegment(), tsSafe()            (port of _safe_segment + timestamp normalisation)
    commands/
      render.ts               # render <report> -o -A --base-url
      serve.ts                # serve <report> -p
      archiveAdd.ts           # archive add <report> -A --print-path
      archiveConfigure.ts     # archive configure -o --add --remove --list
      bootstrapArchive.ts     # bootstrap archive --platform
    templates/archive/        # the 5 cookiecutter files, de-jinja'd (raw GH expressions kept verbatim)
      .github/workflows/analyze.yml
      .github/workflows/preview.yml
      .github/workflows/.nojekyll
      gitlab-ci.yml           # written out as .gitlab-ci.yml
      regis-post-install.md   # written out as .regis-post-install.md
  src/cli/__tests__/
    summary.test.ts
    archiveStore.test.ts
    archivesConfig.test.ts
    bootstrapArchive.test.ts
  tsconfig.cli.json           # CLI build config (CommonJS/Node, outDir dist)
  vitest.config.ts
  Dockerfile
  .dockerignore
  .github/workflows/cd-docker.yml
```

`package.json` gains: `"bin": { "regis-dashboard": "dist/cli/index.js" }`, scripts `build:cli`, `test`, and devDeps `commander`, `vitest`, `@types/node`.

---

### Task 1: CLI scaffolding — commander entry, build, test runner

**Files:**

- Modify: `package.json`
- Create: `tsconfig.cli.json`, `vitest.config.ts`, `src/cli/index.ts`

- [ ] **Step 1: Add deps and scripts**

```bash
pnpm add commander
pnpm add -D vitest @types/node
```

In `package.json`, add to `scripts`:

```json
    "build:cli": "tsc -p tsconfig.cli.json",
    "test": "vitest run",
    "test:watch": "vitest"
```

and add at top level:

```json
  "bin": { "regis-dashboard": "dist/cli/index.js" },
```

- [ ] **Step 2: Create `tsconfig.cli.json`**

```json
{
  "compilerOptions": {
    "target": "ES2021",
    "module": "CommonJS",
    "moduleResolution": "Node",
    "outDir": "dist",
    "rootDir": "src",
    "esModuleInterop": true,
    "strict": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "declaration": false
  },
  "include": ["src/cli/**/*.ts"],
  "exclude": ["src/cli/__tests__/**", "node_modules"]
}
```

- [ ] **Step 3: Create `vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["src/cli/__tests__/**/*.test.ts"],
    environment: "node",
  },
});
```

- [ ] **Step 4: Create `src/cli/index.ts` (commander root)**

```ts
#!/usr/bin/env node
import { Command } from "commander";
import { registerRender } from "./commands/render";
import { registerServe } from "./commands/serve";
import { registerArchiveAdd } from "./commands/archiveAdd";
import { registerArchiveConfigure } from "./commands/archiveConfigure";
import { registerBootstrapArchive } from "./commands/bootstrapArchive";

const program = new Command();
program
  .name("regis-dashboard")
  .description("Render and serve regis container-security reports")
  .version("0.0.0");

registerRender(program);
registerServe(program);
registerArchiveAdd(program);
registerArchiveConfigure(program);
registerBootstrapArchive(program);

program.parseAsync(process.argv);
```

- [ ] **Step 5: Create command stubs so the build compiles**

For each of the five command modules, create a minimal stub now (they are filled in by later tasks). Example `src/cli/commands/render.ts`:

```ts
import { Command } from "commander";
export function registerRender(program: Command): void {
  program
    .command("render")
    .description("(implemented in Task 6)")
    .action(() => {
      throw new Error("not implemented");
    });
}
```

Create the analogous `registerServe`, `registerArchiveAdd`, `registerArchiveConfigure`, `registerBootstrapArchive` stubs.

- [ ] **Step 6: Verify it builds and runs**

```bash
pnpm build:cli
node dist/cli/index.js --help
```

Expected: help text lists `render`, `serve`, `archive add`/`configure` (added in Task 5), `bootstrap`. (Sub-grouped commands appear once their parent is registered.)

- [ ] **Step 7: Commit**

```bash
git add package.json pnpm-lock.yaml tsconfig.cli.json vitest.config.ts src/cli
git commit -m "feat(cli): scaffold regis-dashboard CLI (commander + vitest)"
```

---

### Task 2: Port the archive summary logic (TDD)

**Files:**

- Create: `src/cli/lib/paths.ts`, `src/cli/lib/summary.ts`
- Test: `src/cli/__tests__/summary.test.ts`

Port of `_make_summary` + `_calculate_status` + the timestamp/segment helpers from `regis/archive/store.py`.

- [ ] **Step 1: Write the failing tests**

`src/cli/__tests__/summary.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { makeSummary, calculateStatus } from "../lib/summary";

const baseReport = {
  request: {
    registry: "registry-1.docker.io",
    repository: "library/nginx",
    tag: "1.27",
    digest: "sha256:abc",
    timestamp: "2026-05-31T12:00:00+00:00",
  },
  rules_summary: { score: 100, passed: ["a"], total: ["a"] },
  results: {
    cve: { critical_count: 0, high_count: 1, medium_count: 4, low_count: 12 },
  },
  rules: [{ slug: "a", passed: true, level: "Gold" }],
};

describe("makeSummary", () => {
  it("flattens a report into the manifest summary row", () => {
    const s = makeSummary(
      baseReport,
      "registry-1.docker.io/library/nginx/1.27/x/report.json",
    );
    expect(s.id).toBe(
      "registry-1.docker.io/library/nginx/1.27/2026-05-31T12-00-00",
    );
    expect(s.registry).toBe("registry-1.docker.io");
    expect(s.repository).toBe("library/nginx");
    expect(s.tag).toBe("1.27");
    expect(s.score).toBe(100);
    expect(s.rules_passed).toBe(1);
    expect(s.rules_total).toBe(1);
    expect(s.cve_critical).toBe(0);
    expect(s.cve_high).toBe(1);
    expect(s.path).toBe(
      "registry-1.docker.io/library/nginx/1.27/x/report.json",
    );
    expect(s.status).toBe("pass");
  });

  it("derives status from the highest-severity failing rule", () => {
    expect(
      calculateStatus({ rules: [{ passed: false, level: "warning" }] }),
    ).toBe("warning");
    expect(
      calculateStatus({
        rules: [
          { passed: false, level: "critical" },
          { passed: false, level: "info" },
        ],
      }),
    ).toBe("critical");
    expect(
      calculateStatus({ rules: [{ passed: true, level: "critical" }] }),
    ).toBe("pass");
    expect(calculateStatus({})).toBe("pass");
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `pnpm test -- summary`
Expected: FAIL — module `../lib/summary` not found.

- [ ] **Step 3: Implement `src/cli/lib/paths.ts`**

```ts
/** Replace characters unsafe for directory names (port of _safe_segment). */
export function safeSegment(value: string): string {
  return value.replace(/\//g, "_").replace(/\\/g, "_").replace(/:/g, "_");
}

/** Normalise an ISO timestamp to a filesystem-safe id fragment.
 *  "2026-05-31T12:00:00+00:00" -> "2026-05-31T12-00-00"  (no suffix)
 *  Pass suffix "Z" to mirror the archive directory naming. */
export function tsSafe(timestamp: string, suffix = ""): string {
  const noFrac = timestamp.split(".")[0];
  return noFrac.replace(/:/g, "-").replace(/\+/g, "") + suffix;
}
```

- [ ] **Step 4: Implement `src/cli/lib/summary.ts`**

```ts
import { tsSafe } from "./paths";

type Report = Record<string, any>;

const LEVEL_RANK: Record<string, number> = { critical: 1, warning: 2, info: 3 };
const RANK_LEVEL: Record<number, string> = {
  1: "critical",
  2: "warning",
  3: "info",
};

/** Port of _calculate_status: highest-severity failing rule level, else "pass". */
export function calculateStatus(report: Report): string {
  const rules: Report[] = report.rules ?? [];
  if (rules.length === 0 && !report.rules_summary) return "pass";
  let maxRank = 99;
  for (const r of rules) {
    if (!r.passed) {
      const lvl = String(r.level ?? "info").toLowerCase();
      const rank = LEVEL_RANK[lvl] ?? 3;
      if (rank < maxRank) maxRank = rank;
    }
  }
  return RANK_LEVEL[maxRank] ?? "pass";
}

/** Port of _make_summary: flat manifest row from a full report. */
export function makeSummary(report: Report, path: string): Report {
  const req: Report = report.request ?? {};
  const registry = req.registry ?? "unknown";
  const repository = req.repository ?? "unknown";
  const tag = req.tag ?? "unknown";
  const timestamp = req.timestamp ?? new Date().toISOString();
  const id = `${registry}/${repository}/${tag}/${tsSafe(timestamp)}`;

  const rs: Report = report.rules_summary ?? {};
  const passedRaw = rs.passed ?? 0;
  const totalRaw = rs.total ?? 0;
  const rulesPassed = Array.isArray(passedRaw)
    ? passedRaw.length
    : Number(passedRaw || 0);
  const rulesTotal = Array.isArray(totalRaw)
    ? totalRaw.length
    : Number(totalRaw || 0);
  const score = Number(rs.score ?? 0) | 0;

  const pb = report.playbook ?? (report.playbooks ?? [{}])[0];
  const tier =
    report.tier ?? (pb && typeof pb === "object" ? pb.tier : null) ?? null;

  const results: Report = report.results ?? {};
  const cve: Report = results.cve ?? {};
  const freshness: Report = results.freshness ?? {};
  const sbom: Report = results.sbom ?? {};
  const scorecard: Report = results.scorecarddev ?? {};

  return {
    id,
    timestamp,
    registry,
    repository,
    tag,
    digest: req.digest ?? null,
    score,
    tier,
    rules_passed: rulesPassed,
    rules_total: rulesTotal,
    cve_critical: cve.critical_count ?? null,
    cve_high: cve.high_count ?? null,
    cve_medium: cve.medium_count ?? null,
    cve_low: cve.low_count ?? null,
    age_days: freshness.age_days ?? null,
    sbom_component_count: sbom.component_count ?? null,
    scorecard_score: scorecard.score ?? null,
    status: calculateStatus(report),
    path,
  };
}
```

- [ ] **Step 5: Run to verify pass**

Run: `pnpm test -- summary`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add src/cli/lib/paths.ts src/cli/lib/summary.ts src/cli/__tests__/summary.test.ts
git commit -m "feat(cli): port archive summary + status logic"
```

---

### Task 3: Port the archive store (TDD)

**Files:**

- Create: `src/cli/lib/archiveStore.ts`
- Test: `src/cli/__tests__/archiveStore.test.ts`

Port of `add_to_archive` + `_load_json_array` from `regis/archive/store.py`.

- [ ] **Step 1: Write the failing tests**

`src/cli/__tests__/archiveStore.test.ts`:

```ts
import { describe, it, expect, beforeEach } from "vitest";
import { mkdtempSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { addToArchive } from "../lib/archiveStore";

function report(tag: string, ts: string) {
  return {
    request: {
      registry: "r",
      repository: "repo",
      tag,
      digest: "sha256:x",
      timestamp: ts,
    },
    rules_summary: { score: 90, passed: [], total: [] },
    rules: [],
  };
}

describe("addToArchive", () => {
  let dir: string;
  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), "arch-"));
  });

  it("writes report.json under registry/repo/tag/timestampZ and a manifest", () => {
    const p = addToArchive(report("1.0", "2026-05-31T10:00:00+00:00"), dir);
    expect(p).toContain(join("r", "repo", "1.0"));
    expect(p.endsWith("report.json")).toBe(true);
    expect(existsSync(p)).toBe(true);

    const manifest = JSON.parse(
      readFileSync(join(dir, "manifest.json"), "utf8"),
    );
    expect(manifest).toHaveLength(1);
    expect(manifest[0].tag).toBe("1.0");
    expect(manifest[0].path).toMatch(/^r\/repo\/1\.0\/.*\/report\.json$/);

    // data.json mirrors manifest.json
    const data = JSON.parse(readFileSync(join(dir, "data.json"), "utf8"));
    expect(data).toEqual(manifest);
  });

  it("replaces an entry with the same id and sorts by timestamp desc", () => {
    addToArchive(report("1.0", "2026-05-30T10:00:00+00:00"), dir);
    addToArchive(report("2.0", "2026-05-31T10:00:00+00:00"), dir);
    // re-add 1.0 with same timestamp → same id → replaced, not duplicated
    addToArchive(report("1.0", "2026-05-30T10:00:00+00:00"), dir);

    const manifest = JSON.parse(
      readFileSync(join(dir, "manifest.json"), "utf8"),
    );
    expect(manifest).toHaveLength(2);
    expect(manifest[0].tag).toBe("2.0"); // newest first
    expect(manifest[1].tag).toBe("1.0");
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `pnpm test -- archiveStore`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/cli/lib/archiveStore.ts`**

```ts
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { join, relative, sep, posix } from "node:path";
import { makeSummary } from "./summary";
import { safeSegment, tsSafe } from "./paths";

type Report = Record<string, any>;

function loadJsonArray(path: string): Report[] {
  if (!existsSync(path)) return [];
  try {
    const data = JSON.parse(readFileSync(path, "utf8"));
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

/** Port of add_to_archive. Returns the absolute path to the written report.json. */
export function addToArchive(
  report: Report,
  archiveDir: string,
  pretty = true,
): string {
  mkdirSync(archiveDir, { recursive: true });
  const req: Report = report.request ?? {};
  const registry = safeSegment(req.registry ?? "unknown");
  const repository = safeSegment(req.repository ?? "unknown");
  const tag = safeSegment(req.tag ?? "unknown");
  const timestamp = req.timestamp ?? new Date().toISOString();
  const tsDir = tsSafe(timestamp, "Z");

  const reportDir = join(archiveDir, registry, repository, tag, tsDir);
  mkdirSync(reportDir, { recursive: true });
  const reportPath = join(reportDir, "report.json");

  const indent = pretty ? 2 : undefined;
  writeFileSync(reportPath, JSON.stringify(report, null, indent), "utf8");

  // relative posix path for the manifest
  const relativePath = relative(archiveDir, reportPath)
    .split(sep)
    .join(posix.sep);
  const summary = makeSummary(report, relativePath);

  const manifestPath = join(archiveDir, "manifest.json");
  let manifest = loadJsonArray(manifestPath).filter((e) => e.id !== summary.id);
  manifest.push(summary);
  manifest.sort((a, b) =>
    String(b.timestamp ?? "").localeCompare(String(a.timestamp ?? "")),
  );

  writeFileSync(manifestPath, JSON.stringify(manifest, null, indent), "utf8");
  writeFileSync(
    join(archiveDir, "data.json"),
    JSON.stringify(manifest, null, indent),
    "utf8",
  );

  return reportPath;
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pnpm test -- archiveStore`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/cli/lib/archiveStore.ts src/cli/__tests__/archiveStore.test.ts
git commit -m "feat(cli): port archive store (addToArchive + manifest)"
```

---

### Task 4: `archive add` command

**Files:**

- Modify: `src/cli/commands/archiveAdd.ts`

Port of `regis archive add` (`regis/commands/archive.py`).

- [ ] **Step 1: Implement the command**

```ts
import { Command } from "commander";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { addToArchive } from "../lib/archiveStore";

export function registerArchiveAdd(program: Command): void {
  const archive =
    program.commands.find((c) => c.name() === "archive") ??
    program.command("archive").description("Manage the report archive");

  archive
    .command("add <report_file>")
    .requiredOption(
      "-A, --archive-dir <dir>",
      "Archive directory to add the report to",
    )
    .option(
      "--print-path",
      "Print only the archived report path (machine-readable)",
      false,
    )
    .action(
      (
        reportFile: string,
        opts: { archiveDir: string; printPath: boolean },
      ) => {
        let report: unknown;
        try {
          report = JSON.parse(readFileSync(resolve(reportFile), "utf8"));
        } catch (e) {
          throw new Error(
            `Could not read ${reportFile}: ${(e as Error).message}`,
          );
        }
        const dest = addToArchive(
          report as Record<string, any>,
          resolve(opts.archiveDir),
        );
        if (opts.printPath) {
          process.stdout.write(dest + "\n");
        } else {
          process.stderr.write(`Archived to ${dest}\n`);
        }
      },
    );
}
```

Note: the `archive` parent command is shared between `archive add` (Task 4) and `archive configure` (Task 5). The `find(...) ?? program.command(...)` idiom registers the parent once. Whichever of Tasks 4/5 runs first creates it; the other reuses it.

- [ ] **Step 2: Smoke test**

```bash
pnpm build:cli
echo '{"schemaVersion":1,"version":"0.33.0","request":{"url":"r/repo:1","registry":"r","repository":"repo","tag":"1","analyzers":[],"timestamp":"2026-05-31T10:00:00+00:00"},"results":{}}' > /tmp/r.json
node dist/cli/index.js archive add /tmp/r.json -A /tmp/arch --print-path
test -f /tmp/arch/manifest.json && echo "OK manifest written"
```

Expected: prints the archived report path; "OK manifest written".

- [ ] **Step 3: Commit**

```bash
git add src/cli/commands/archiveAdd.ts
git commit -m "feat(cli): add 'archive add' command"
```

---

### Task 5: `archive configure` + archives.json config (TDD)

**Files:**

- Create: `src/cli/lib/archivesConfig.ts`
- Test: `src/cli/__tests__/archivesConfig.test.ts`
- Modify: `src/cli/commands/archiveConfigure.ts`

Port of `_load_archives_config` / `_write_archives_config` and the `archive configure` flags (`--add`/`--remove`/`--list`) from `regis/commands/archive.py`. The archives.json shape is `{ "archives": [{ "name", "path" }] }` (from `regis/schemas/archives.schema.json`).

- [ ] **Step 1: Write the failing tests**

`src/cli/__tests__/archivesConfig.test.ts`:

```ts
import { describe, it, expect, beforeEach } from "vitest";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  loadArchives,
  addArchive,
  removeArchive,
  writeArchives,
} from "../lib/archivesConfig";

describe("archivesConfig", () => {
  let file: string;
  beforeEach(() => {
    file = join(mkdtempSync(join(tmpdir(), "cfg-")), "archives.json");
  });

  it("adds an entry and round-trips the {archives:[...]} shape", () => {
    const next = addArchive(
      loadArchives(file),
      "Prod",
      "https://x/manifest.json",
    );
    writeArchives(file, next);
    const parsed = JSON.parse(readFileSync(file, "utf8"));
    expect(parsed).toEqual({
      archives: [{ name: "Prod", path: "https://x/manifest.json" }],
    });
  });

  it("rejects a duplicate name", () => {
    const one = addArchive([], "Prod", "a");
    expect(() => addArchive(one, "Prod", "b")).toThrow(/already exists/);
  });

  it("removes by name and errors when absent", () => {
    const one = addArchive([], "Prod", "a");
    expect(removeArchive(one, "Prod")).toEqual([]);
    expect(() => removeArchive([], "Nope")).toThrow(/not found/);
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `pnpm test -- archivesConfig`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/cli/lib/archivesConfig.ts`**

```ts
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

export interface ArchiveEntry {
  name: string;
  path: string;
}

export function loadArchives(file: string): ArchiveEntry[] {
  if (!existsSync(file)) return [];
  try {
    const data = JSON.parse(readFileSync(file, "utf8"));
    return Array.isArray(data?.archives) ? data.archives : [];
  } catch {
    return [];
  }
}

export function addArchive(
  archives: ArchiveEntry[],
  name: string,
  path: string,
): ArchiveEntry[] {
  if (!name.trim() || !path.trim())
    throw new Error("Name and path must not be empty.");
  if (archives.some((a) => a.name === name)) {
    throw new Error(
      `Archive '${name}' already exists. Remove it first with --remove.`,
    );
  }
  return [...archives, { name, path }];
}

export function removeArchive(
  archives: ArchiveEntry[],
  name: string,
): ArchiveEntry[] {
  const next = archives.filter((a) => a.name !== name);
  if (next.length === archives.length)
    throw new Error(`Archive '${name}' not found.`);
  return next;
}

export function writeArchives(file: string, archives: ArchiveEntry[]): void {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify({ archives }, null, 2) + "\n", "utf8");
}
```

- [ ] **Step 4: Run to verify pass**

Run: `pnpm test -- archivesConfig`
Expected: PASS (3 tests).

- [ ] **Step 5: Implement the `archive configure` command** in `src/cli/commands/archiveConfigure.ts`

```ts
import { Command } from "commander";
import { resolve } from "node:path";
import {
  loadArchives,
  addArchive,
  removeArchive,
  writeArchives,
} from "../lib/archivesConfig";

export function registerArchiveConfigure(program: Command): void {
  const archive =
    program.commands.find((c) => c.name() === "archive") ??
    program.command("archive").description("Manage the report archive");

  archive
    .command("configure")
    .option("-o, --output <file>", "Path to archives.json", "archives.json")
    .option("--add <entry>", 'Add an archive: "Name:path-or-url"')
    .option("--remove <name>", "Remove an archive by name")
    .option("--list", "List configured archives and exit", false)
    .action(
      (opts: {
        output: string;
        add?: string;
        remove?: string;
        list: boolean;
      }) => {
        const file = resolve(opts.output);
        let archives = loadArchives(file);

        if (opts.list) {
          if (archives.length === 0)
            process.stderr.write("No archives configured.\n");
          else
            archives.forEach((a) =>
              process.stdout.write(`  ${a.name}: ${a.path}\n`),
            );
          return;
        }
        if (opts.remove) {
          archives = removeArchive(archives, opts.remove);
          writeArchives(file, archives);
          process.stderr.write(
            `Removed '${opts.remove}'. ${archives.length} remaining.\n`,
          );
          return;
        }
        if (opts.add) {
          const idx = opts.add.indexOf(":");
          if (idx < 0)
            throw new Error(
              `Invalid format: ${opts.add}. Expected "Name:path-or-url".`,
            );
          const name = opts.add.slice(0, idx);
          const path = opts.add.slice(idx + 1);
          archives = addArchive(archives, name, path);
          writeArchives(file, archives);
          process.stderr.write(`Added '${name}' -> ${path}\n`);
          return;
        }
        process.stderr.write(
          'Nothing to do. Use --add "Name:path", --remove NAME, or --list.\n',
        );
      },
    );
}
```

(The Python interactive prompt mode is intentionally dropped — non-interactive flags only, which is what CI uses.)

- [ ] **Step 6: Verify build + smoke**

```bash
pnpm build:cli
node dist/cli/index.js archive configure -o /tmp/archives.json --add "Prod:https://x/manifest.json"
node dist/cli/index.js archive configure -o /tmp/archives.json --list
```

Expected: writes `/tmp/archives.json`; `--list` prints `Prod: https://x/manifest.json`.

- [ ] **Step 7: Commit**

```bash
git add src/cli/lib/archivesConfig.ts src/cli/__tests__/archivesConfig.test.ts src/cli/commands/archiveConfigure.ts
git commit -m "feat(cli): add 'archive configure' command + archives.json config"
```

---

### Task 6: `render` command

**Files:**

- Modify: `src/cli/commands/render.ts`

Port of `_build_from_source` (`regis/report/docusaurus.py`) + the `-a` archives option from `dashboard export`. In the standalone repo the CLI lives **inside** the Docusaurus project, so `render` stages files into the project's own `static/` and runs its own build.

- [ ] **Step 1: Implement the command**

```ts
import { Command } from "commander";
import { execFileSync } from "node:child_process";
import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  cpSync,
  existsSync,
  copyFileSync,
} from "node:fs";
import { resolve, join, dirname } from "node:path";

// Repo root = two levels up from dist/cli/ (or src/cli/ in ts-node). Resolved at runtime.
function repoRoot(): string {
  // dist/cli/index.js -> dist/cli -> dist -> repo root
  return resolve(__dirname, "..", "..");
}

function parseArchives(entries: string[]): { name: string; path: string }[] {
  return entries.map((e) => {
    const idx = e.indexOf(":");
    if (idx < 0)
      throw new Error(`Invalid archive ${e}. Expected "Name:path-or-url".`);
    return { name: e.slice(0, idx), path: e.slice(idx + 1) };
  });
}

export function registerRender(program: Command): void {
  program
    .command("render <report>")
    .description("Build a static report site from a report.json")
    .requiredOption(
      "-o, --output <dir>",
      "Directory to write the static site into",
    )
    .option("--base-url <url>", "Base URL for the site (e.g. /reports/)", "/")
    .option(
      "-a, --archive <entry...>",
      'Named archive "Name:path-or-url" (repeatable)',
    )
    .action(
      (
        report: string,
        opts: { output: string; baseUrl: string; archive?: string[] },
      ) => {
        const root = repoRoot();
        const staticDir = join(root, "static");
        mkdirSync(staticDir, { recursive: true });

        // 1. stage report.json
        const reportData = readFileSync(resolve(report), "utf8");
        writeFileSync(join(staticDir, "report.json"), reportData, "utf8");

        // 2. stage archives.json if provided
        if (opts.archive?.length) {
          const archives = parseArchives(opts.archive);
          writeFileSync(
            join(staticDir, "archives.json"),
            JSON.stringify({ archives }, null, 2),
            "utf8",
          );
        }

        // 3. run the project's own docusaurus build with REPORT_BASE_URL set
        const baseUrl = opts.baseUrl.endsWith("/")
          ? opts.baseUrl
          : opts.baseUrl + "/";
        execFileSync("pnpm", ["run", "build"], {
          cwd: root,
          env: {
            ...process.env,
            REPORT_BASE_URL: baseUrl,
            NODE_ENV: "production",
          },
          stdio: "inherit",
        });

        // 4. copy build/ to the output dir, ensuring report.json at the root
        const outDir = resolve(opts.output);
        mkdirSync(outDir, { recursive: true });
        cpSync(join(root, "build"), outDir, { recursive: true });
        const outReport = join(outDir, "report.json");
        if (!existsSync(outReport)) {
          mkdirSync(dirname(outReport), { recursive: true });
          copyFileSync(join(staticDir, "report.json"), outReport);
        }
        process.stderr.write(`Report site written to ${outDir}\n`);
      },
    );
}
```

- [ ] **Step 2: Smoke test (uses the demo report from Phase 1a)**

```bash
pnpm build:cli
node dist/cli/index.js render static/report.json -o /tmp/site --base-url /
test -f /tmp/site/index.html && test -f /tmp/site/report.json && echo "OK render produced a site with report.json"
```

Expected: the build runs and "OK render produced a site with report.json" prints.

- [ ] **Step 3: Commit**

```bash
git add src/cli/commands/render.ts
git commit -m "feat(cli): add 'render' command (static report site build)"
```

---

### Task 7: `serve` command

**Files:**

- Modify: `src/cli/commands/serve.ts`

Static preview only (GitLab/webhook backend dropped). Stage the report, then run the project's own `docusaurus serve` after a build, or `docusaurus start` for live reload.

- [ ] **Step 1: Implement the command**

```ts
import { Command } from "commander";
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, join } from "node:path";

function repoRoot(): string {
  return resolve(__dirname, "..", "..");
}

export function registerServe(program: Command): void {
  program
    .command("serve <report>")
    .description("Build and serve a report locally (static preview)")
    .option("-p, --port <port>", "Port to listen on", "8000")
    .action((report: string, opts: { port: string }) => {
      const root = repoRoot();
      const staticDir = join(root, "static");
      mkdirSync(staticDir, { recursive: true });
      writeFileSync(
        join(staticDir, "report.json"),
        readFileSync(resolve(report), "utf8"),
        "utf8",
      );

      // Build once, then serve the static output (matches the dropped FastAPI preview's behavior).
      execFileSync("pnpm", ["run", "build"], {
        cwd: root,
        env: { ...process.env, REPORT_BASE_URL: "/", NODE_ENV: "production" },
        stdio: "inherit",
      });
      execFileSync("pnpm", ["run", "serve", "--", "--port", opts.port], {
        cwd: root,
        stdio: "inherit",
      });
    });
}
```

- [ ] **Step 2: Manual verification (documented, not automated — serve is long-running)**

```bash
pnpm build:cli
node dist/cli/index.js serve static/report.json -p 8123 &
sleep 8
curl -fsSL http://localhost:8123/report.json | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log('schemaVersion',JSON.parse(d).schemaVersion))"
kill %1
```

Expected: prints `schemaVersion 1`.

- [ ] **Step 3: Commit**

```bash
git add src/cli/commands/serve.ts
git commit -m "feat(cli): add 'serve' command (static preview)"
```

---

### Task 8: `bootstrap archive` command + templates (TDD)

**Files:**

- Create: `src/cli/templates/archive/**` (the 5 files, copied verbatim from the core cookiecutter output)
- Modify: `src/cli/commands/bootstrapArchive.ts`
- Test: `src/cli/__tests__/bootstrapArchive.test.ts`

The core cookiecutter does **no** real variable substitution (all GitHub `${{ }}` expressions are raw-wrapped, the image is hardcoded to `:main`). So `bootstrap archive` is a fixed file-copy with a platform-conditional deletion: `github` keeps `.github/`, drops `.gitlab-ci.yml`; `gitlab` keeps `.gitlab-ci.yml`, drops `.github/`.

- [ ] **Step 1: Copy the template files from the core**

From a core checkout, copy the **rendered** template tree (after cookiecutter strips `{% raw %}`/`{% endraw %}` — i.e. copy the literal file bodies the core ships, removing only the Jinja raw markers) into `src/cli/templates/archive/`:

- `.github/workflows/analyze.yml`
- `.github/workflows/preview.yml`
- `.github/workflows/.nojekyll`
- `gitlab-ci.yml` (will be written out as `.gitlab-ci.yml`)
- `regis-post-install.md` (written out as `.regis-post-install.md`)

When copying, replace any `{% raw %}` / `{% endraw %}` markers with nothing (the GitHub `${{ ... }}` expressions stay verbatim).

- [ ] **Step 2: Write the failing test**

`src/cli/__tests__/bootstrapArchive.test.ts`:

```ts
import { describe, it, expect, beforeEach } from "vitest";
import { mkdtempSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { scaffoldArchive } from "../commands/bootstrapArchive";

describe("scaffoldArchive", () => {
  let dir: string;
  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), "boot-"));
  });

  it("github platform keeps .github and drops .gitlab-ci.yml", () => {
    scaffoldArchive(dir, "github");
    expect(existsSync(join(dir, ".github/workflows/analyze.yml"))).toBe(true);
    expect(existsSync(join(dir, ".github/workflows/preview.yml"))).toBe(true);
    expect(existsSync(join(dir, ".gitlab-ci.yml"))).toBe(false);
    expect(existsSync(join(dir, ".regis-post-install.md"))).toBe(true);
  });

  it("gitlab platform keeps .gitlab-ci.yml and drops .github", () => {
    scaffoldArchive(dir, "gitlab");
    expect(existsSync(join(dir, ".gitlab-ci.yml"))).toBe(true);
    expect(existsSync(join(dir, ".github"))).toBe(false);
  });
});
```

- [ ] **Step 3: Run to verify failure**

Run: `pnpm test -- bootstrapArchive`
Expected: FAIL — `scaffoldArchive` not exported.

- [ ] **Step 4: Implement `src/cli/commands/bootstrapArchive.ts`**

```ts
import { Command } from "commander";
import { cpSync, mkdirSync, copyFileSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";

function templatesDir(): string {
  return resolve(__dirname, "..", "templates", "archive");
}

/** Scaffold an archive project into outDir for the given platform. Pure-ish (filesystem only). */
export function scaffoldArchive(
  outDir: string,
  platform: "github" | "gitlab",
): void {
  const tpl = templatesDir();
  mkdirSync(outDir, { recursive: true });

  // always: the post-install note
  copyFileSync(
    join(tpl, "regis-post-install.md"),
    join(outDir, ".regis-post-install.md"),
  );

  if (platform === "github") {
    cpSync(join(tpl, ".github"), join(outDir, ".github"), { recursive: true });
  } else {
    copyFileSync(join(tpl, "gitlab-ci.yml"), join(outDir, ".gitlab-ci.yml"));
  }
}

export function registerBootstrapArchive(program: Command): void {
  const bootstrap =
    program.commands.find((c) => c.name() === "bootstrap") ??
    program.command("bootstrap").description("Scaffold archive/CI projects");

  bootstrap
    .command("archive")
    .description(
      "Scaffold a report-archive project with CI for GitHub or GitLab Pages",
    )
    .requiredOption("-o, --output <dir>", "Directory to scaffold into")
    .option("--platform <platform>", "github | gitlab", "github")
    .action((opts: { output: string; platform: "github" | "gitlab" }) => {
      if (opts.platform !== "github" && opts.platform !== "gitlab") {
        throw new Error(
          `--platform must be 'github' or 'gitlab', got '${opts.platform}'`,
        );
      }
      const out = resolve(opts.output);
      if (
        existsSync(join(out, ".github")) ||
        existsSync(join(out, ".gitlab-ci.yml"))
      ) {
        throw new Error(`${out} already contains an archive scaffold.`);
      }
      scaffoldArchive(out, opts.platform);
      process.stderr.write(
        `Scaffolded ${opts.platform} archive project in ${out}\n`,
      );
    });
}
```

- [ ] **Step 5: Run to verify pass + ensure templates ship in the build**

The templates are non-`.ts` assets; `tsc` does not copy them. Add a copy step to `build:cli` so `dist/cli/templates/` exists:

```json
    "build:cli": "tsc -p tsconfig.cli.json && cp -r src/cli/templates dist/cli/templates",
```

Then:

```bash
pnpm test -- bootstrapArchive
pnpm build:cli
node dist/cli/index.js bootstrap archive -o /tmp/boot --platform gitlab && test -f /tmp/boot/.gitlab-ci.yml && echo OK
```

Expected: tests PASS; "OK".

- [ ] **Step 6: Commit**

```bash
git add src/cli/templates src/cli/commands/bootstrapArchive.ts src/cli/__tests__/bootstrapArchive.test.ts package.json
git commit -m "feat(cli): add 'bootstrap archive' command + templates"
```

---

### Task 9: Dockerfile + image publish workflow

**Files:**

- Create: `Dockerfile`, `.dockerignore`, `.github/workflows/cd-docker.yml`

- [ ] **Step 1: Write the `Dockerfile`**

The image must contain the dashboard source + `node_modules` + the compiled CLI so `render`/`serve` can run `docusaurus build` offline.

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build:cli

FROM node:20-alpine AS runtime
WORKDIR /app
RUN corepack enable
ENV NODE_ENV=production
COPY --from=build /app /app
# the CLI is the entrypoint; default workdir for user data is /data
WORKDIR /data
ENTRYPOINT ["node", "/app/dist/cli/index.js"]
CMD ["--help"]
```

- [ ] **Step 2: Write `.dockerignore`**

```dockerignore
node_modules
build
.docusaurus
.git
*.log
```

(Do not ignore `pnpm-lock.yaml` — it is needed for `--frozen-lockfile`.)

- [ ] **Step 3: Local build + run smoke test**

```bash
docker build -t regis-dashboard:dev .
docker run --rm -v "$PWD/static:/data" regis-dashboard:dev render /data/report.json -o /data/out
test -f static/out/index.html && echo "OK docker render"
```

Expected: image builds; "OK docker render".

- [ ] **Step 4: Write `.github/workflows/cd-docker.yml`**

```yaml
name: Publish Docker image

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/trivoallan/regis-dashboard
          tags: |
            type=semver,pattern={{version}}
            type=raw,value=latest
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

(release-please tags `v*` on release → this publishes `ghcr.io/trivoallan/regis-dashboard:<version>` and `:latest`.)

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore .github/workflows/cd-docker.yml
git commit -m "ci: add Dockerfile and GHCR publish workflow"
```

---

### Task 10: Wire CLI checks into CI + update README

**Files:**

- Modify: `.github/workflows/ci.yml` (from 1a), `README.md`

- [ ] **Step 1: Add test + CLI build to the PR CI**

In `.github/workflows/ci.yml`, after the existing `pnpm build` step, add:

```yaml
- run: pnpm test
- run: pnpm build:cli
```

- [ ] **Step 2: Update the README "Status"/usage section** to document the CLI:

```markdown
## Use the CLI

    # render a static site from a report
    docker run --rm -v "$PWD:/data" ghcr.io/trivoallan/regis-dashboard render /data/report.json -o /data/site

    # live preview
    docker run --rm -p 8000:8000 -v "$PWD:/data" ghcr.io/trivoallan/regis-dashboard serve /data/report.json

    # manage a multi-report archive
    regis-dashboard archive add report.json -A ./archive
    regis-dashboard archive configure --add "Prod:https://example.com/manifest.json"
    regis-dashboard bootstrap archive -o ./my-archive --platform github
```

- [ ] **Step 3: Verify the full check suite locally**

```bash
pnpm install
pnpm typecheck
pnpm test
pnpm build:cli
pnpm build
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml README.md
git commit -m "ci: run CLI tests + build in PR checks; document CLI in README"
```

---

## Self-review notes (reconciled against the spec & ports)

- **Spec Phase-1 "rewrite render/serve/bootstrap archive/archive add|configure JS-first"** → Tasks 6, 7, 8, 4, 5.
- **Ported logic fidelity:** `summary.ts`/`archiveStore.ts` mirror `_make_summary`/`_calculate_status`/`add_to_archive` (same `_SUMMARY_KEYS`, same id format `{registry}/{repo}/{tag}/{ts-safe}`, same `Z`-suffixed dir, same manifest replace-by-id + timestamp-desc sort, same `data.json == manifest.json`). `archivesConfig.ts` mirrors the `{archives:[{name,path}]}` schema and the add/remove/list flags.
- **`render` fidelity:** stages `report.json` into `static/`, sets `REPORT_BASE_URL`, runs the project build, copies `build/`→output, ensures `report.json` at output root — same four steps as `_build_from_source`.
- **Dropped behavior (intentional):** the Python `archive configure` interactive prompt (CI uses flags); the `dashboard serve` GitLab/webhook backend (static-preview-only decision).
- **Deferred to 1c (correctly NOT here):** the runtime `schemaVersion` compatibility gate and the cross-repo contract test. `vitest` is introduced here and reused there.

## Risks / watch-points

- **`repoRoot()` resolution:** `render`/`serve` assume the compiled CLI sits at `dist/cli/index.js` two levels under the repo root, and that the Docusaurus project (with `node_modules`) is at that root. This holds in the Docker image (Task 9) and in a local `pnpm build:cli` checkout. If the CLI is ever published to npm standalone (without the Docusaurus project), `render`/`serve` would need the project path injected — note for a future task, not needed for the Docker-primary distribution.
- **Templates in the build output:** `tsc` ignores non-TS files, so Task 8 Step 5 adds an explicit `cp` of `src/cli/templates` → `dist/cli/templates`. Without it, `bootstrap archive` fails at runtime. The test runs against `src/` paths, so it passes even if the copy is forgotten — the Step-5 smoke run against `dist/` is what catches a missing copy.
- **`pnpm` availability inside `render`/`serve`:** both shell out to `pnpm run build`. The Docker image enables corepack; a bare npm-only environment would fail. Documented as Docker-primary.
- **Timestamp helper divergence:** `tsSafe` must match the Python `.replace(":", "-").replace("+", "").split(".")[0]` exactly (the `id` is the manifest dedup key). The `summary.test.ts` `id` assertion guards this.
