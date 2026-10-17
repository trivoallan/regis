---
adr: "0018"
title: External tools called as subprocesses
status: accepted
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# External tools called as subprocesses

## Context and Problem Statement

Vulnerability, secret, SBOM and lint analysis are done best by tools that their communities maintain: `grype`, `syft`, `trufflehog`, `hadolint`, `dockle` and `regctl`. They are written in Go and other languages, not in Python.

## Considered Options

* Reimplement the analysis in Python.
* Bind the tools as libraries.
* Call the tools as binaries.

## Decision Outcome

Call the binaries as subprocesses, through the `ToolRunner` port. `regis/adapters/driven/tools/subprocess_tool_runner.py` implements it, with a timeout on each call. Tool versions, their sha256 and their signing identities are pinned in `regis/adapters/driven/tools/manifest.yaml`. A fetched binary is always checked against its sha256; its `cosign` signature is verified when `cosign` is on the `PATH`, and required when `REGIS_REQUIRE_COSIGN=1`.

Reimplementing was rejected because `regis` would then own the quality of vulnerability matching and secret detection. Bindings were rejected because most of these tools offer none for Python.

### Consequences

`regis` reuses tools that the ecosystem maintains, and pins their versions (quality goal 1, Reproducibility).
The cost: the binaries must be on the `PATH` or fetched, the `full` image grows with them, and the output format of each tool is a contract that `regis` does not control.
