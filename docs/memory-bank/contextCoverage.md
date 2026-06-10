# Context Coverage

## Coverage Status

| File                    | Coverage                            | Last Updated | Notes                                                 |
| ----------------------- | ----------------------------------- | ------------ | ----------------------------------------------------- |
| projectbrief.md         | 🟢 Complete                         | 2026-04-21   | Filled from README and packaging metadata             |
| productContext.md       | 🟢 Complete                         | 2026-04-21   | Filled from README and project structure              |
| systemPatterns.md       | 🟢 Complete                         | 2026-04-21   | Derived from repository layout and CLAUDE.md          |
| techContext.md          | 🟢 Complete                         | 2026-04-21   | Derived from `pyproject.toml`, `uv.lock`, and scripts |
| activeContext.md        | 🟢 Complete                         | 2026-04-21   | Captures setup state and current branch context       |
| progress.md             | 🟢 Complete                         | 2026-04-21   | Captures initial project status                       |
| businessLogic.md        | 🟡 Partial                          | 2026-04-21   | High-level rules only                                 |
| dataModel.md            | 🟡 Partial                          | 2026-04-21   | No database schema identified                         |
| dependencies.md         | 🟢 Complete                         | 2026-04-21   | Based on `pyproject.toml` and `uv.lock`               |
| events.md               | 🟡 Partial                          | 2026-04-21   | No dedicated event bus identified                     |
| externalIntegrations.md | 🟡 Partial                          | 2026-04-21   | External services inferred from codebase              |
| featureToggles.md       | ◻️ Empty / 🟡 Partial / 🟢 Complete | 2026-04-21   | No toggles identified                                 |
| observability.md        | 🟡 Partial                          | 2026-04-21   | CI-focused visibility only                            |
| security.md             | 🟢 Complete                         | 2026-04-21   | CI security posture captured from workflows and docs  |
| technicalDebt.md        | 🟡 Partial                          | 2026-04-21   | No explicit debt list yet                             |

## Gaps Identified

- Import alias configuration was not found in the inspected files.
- No explicit environment variable inventory was found in the inspected files.
- Database, events, and health-check details are not documented in the inspected files.

## Staleness Risk

- `activeContext.md` and `progress.md` will go stale quickly without session updates.

## Improvement Actions

- Add more precise dependency and architecture notes as the codebase changes.
- Update coverage entries whenever significant features, workflows, or integrations change.
