---
sidebar_position: 6
title: Multi-Archive Setup
description: Configure multiple archives for cross-environment comparison in the Regis dashboard.
---

Regis supports multiple named [archives](../concepts/archives.md), allowing you to organize analyses by environment (production, staging), team, or image typology and compare them side by side in the dashboard.

## Quick start

### 1. Configure archives

```bash
regis archive configure \
  --add "Production:static/archive/prod" \
  -o static/archives.json

regis archive configure \
  --add "Staging:static/archive/staging" \
  -o static/archives.json
```

### 2. Add reports to each archive

```bash
regis analyze myimage:latest --archive static/archive/prod
regis analyze myimage:staging --archive static/archive/staging
```

### 3. View in the dashboard

```bash
regis dashboard serve \
  --archive "Production:static/archive/prod/manifest.json" \
  --archive "Staging:static/archive/staging/manifest.json"
```

The dashboard shows archive tabs and a combined "All Archives" view with source filtering.

---

## Managing archives

### List configured archives

```bash
regis archive configure --list static/archives.json
```

### Remove an archive

```bash
regis archive configure --remove "Staging" -o static/archives.json
```

### Interactive mode

Run without flags to add archives interactively:

```bash
regis archive configure -o static/archives.json
```

You'll be prompted for each archive's name and path.

---

## Archive paths

Archive paths can be:

- **Relative paths** — `static/archive/prod/manifest.json` (relative to the site root)
- **HTTP(S) URLs** — `https://host.example.com/archive/manifest.json` (for remote archives)

---

## Bootstrapping with multi-archive

When you scaffold a new archive site with `regis bootstrap archive`, the post-install notes explain how to add more archives. The scaffolded site starts with a single archive — use `regis archive configure` to add more.

---

## How it works

The `archives.json` file lists named archives:

```json
{
  "archives": [
    { "name": "Production", "path": "static/archive/prod/manifest.json" },
    { "name": "Staging", "path": "static/archive/staging/manifest.json" }
  ]
}
```

The dashboard detects this file and enables:

- **Archive tabs** — switch between individual archives
- **All Archives view** — merged view with a source column and filter
- **Session persistence** — remembers the selected archive tab
