---
sidebar_position: 6
title: Multi-Archive Setup
description: Configure multiple archives for cross-environment comparison in the Regis dashboard.
---

Regis supports multiple named [archives](../concepts/archives.md), allowing you
to organize analyses by environment (production, staging), team, or image
typology and compare them side by side.

The multi-archive browser — configuring named archives, switching between them,
and the combined "All Archives" view with source filtering — now lives in a
**separate project**:

➡️ **[trivoallan/regis-dashboard](https://github.com/trivoallan/regis-dashboard)**

It provides the `regis-dashboard archive configure`, `archive add`, `render`,
and `serve` commands for managing and viewing multi-archive setups.

## What the core CLI still produces

The Regis core CLI keeps writing the archive data the standalone dashboard
consumes. Append reports to as many archive directories as you need:

```bash
regis analyze myimage:latest --archive static/archive/prod
regis analyze myimage:staging --archive static/archive/staging
```

Each `--archive <dir>` directory holds a `manifest.json` index and the
timestamped reports. Point `regis-dashboard` at these directories to configure
named archives and browse them together.
