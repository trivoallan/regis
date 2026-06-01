---
sidebar_position: 5
tags:
  - reports
  - dashboard
---

# Dashboard

The interactive dashboard — a Single Page Application that turns Regis security
data into filterable, searchable, drill-down views — now lives in a **separate
project**:

➡️ **[trivoallan/regis-dashboard](https://github.com/trivoallan/regis-dashboard)**

It provides the `regis-dashboard render`, `serve`, `archive add`,
`archive configure`, and `bootstrap archive` commands for rendering and hosting
interactive reports and multi-archive browsers.

## What the core CLI still produces

The Regis core CLI keeps producing everything the standalone dashboard consumes:

- **`regis analyze --json`** — the machine-readable `report.json` contract.
- **`regis analyze --html`** — a self-contained single-file `report.html` you
  can open in any browser or ship as a CI artifact, no server required.
- **`regis analyze --archive <dir>`** — appends to an archive directory the
  standalone `regis-dashboard` browses and renders.

For a deep dive into the reporting engine and the `report.json` contract, see
the **[Reporting Concepts](../concepts/reports.md)** page.
