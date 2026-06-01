---
sidebar_position: 3
---

# Archive Repository

Scaffolding and publishing a standalone [archive](../../concepts/archives.md)
viewer site — creating the remote repository, pushing the initial commit, and
enabling GitHub/GitLab Pages — now lives in a **separate project**:

➡️ **[trivoallan/regis-dashboard](https://github.com/trivoallan/regis-dashboard)**

It provides the `regis-dashboard bootstrap archive` command (including the
`--repo` flow) that creates the viewer site and wires up Pages deployment.

## What the core CLI still produces

The Regis core CLI keeps writing the archive data the standalone viewer
consumes. Append reports to an archive directory from any project:

```bash
regis analyze <image> --archive /path/to/regis-archive/static/archive
```

Then commit and push in your archive repository:

```bash
cd /path/to/regis-archive
git add static/archive/
git commit -m "chore: add report for <image>"
git push
```

See the [`regis-dashboard`](https://github.com/trivoallan/regis-dashboard)
project for scaffolding the viewer site and configuring Pages deployment.
