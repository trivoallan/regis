---
trigger: always_on
---

- Simple workflow for a small team based on feature / bug branches that are merged to the main branch before release
- main branch is protected. PR are mandatory.
- PRs are merged with squash merge only (`gh pr merge --squash`); never use merge commits or rebase, to keep `main` history linear.
