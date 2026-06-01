---
sidebar_position: 4
---

# Customizing the Archive UI

The standalone [archive](../../concepts/archives.md) viewer site — its React
components, styling, and the cookiecutter template behind it — now lives in a
**separate project**:

➡️ **[trivoallan/regis-dashboard](https://github.com/trivoallan/regis-dashboard)**

Scaffolding a local working copy, iterating on the UI, and syncing changes back
to the template are handled there (`regis-dashboard bootstrap archive --dev` and
`--sync-from`). See that project's documentation for customization details.

## What the core CLI still produces

The Regis core CLI keeps writing the archive data the viewer renders. Append
reports to an archive directory with:

```bash
regis analyze <image> --archive /path/to/archive
```

Then point `regis-dashboard` at that directory to render and customize the view.
