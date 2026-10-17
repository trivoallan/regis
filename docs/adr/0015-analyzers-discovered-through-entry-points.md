---
adr: "0015"
title: Analyzers discovered through entry points
status: accepted
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# Analyzers discovered through entry points

## Context and Problem Statement

`regis` ships 14 analyzers: vulnerabilities, secrets, SBOM, Dockerfile and image linting, freshness, end of life, size, popularity, provenance, OpenSSF Scorecard, metadata and others. The hexagonal core ([SDR-0003](SDR-0003-architecture.md)) must not import any of them by name, otherwise adding one means editing the core.

## Considered Options

* A registry of analyzers hard-coded in the core.
* Python entry points, read at run time.
* Scanning a plugins directory for modules.

## Decision Outcome

Python entry points. Each analyzer subclasses `BaseAnalyzer` and is registered in the group `regis.analyzers` (`[project.entry-points."regis.analyzers"]` in `pyproject.toml`). `regis/core/domain/analyzers/discovery.py` loads the group with `importlib.metadata.entry_points`. The group name is the discovery contract, not a module path.

A hard-coded registry was rejected because it couples the core to every analyzer. A plugins directory was rejected because it bypasses packaging: a third-party analyzer could not be installed with `pip`.

### Consequences

A package outside `regis` adds an analyzer by declaring an entry point, without touching `regis` (quality goal 4, Extensibility).
The cost: entry points are read from the installed metadata, so `uv sync` is required after any change to them, and a missing registration fails silently: the analyzer is simply not discovered.
