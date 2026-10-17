---
adr: "0017"
title: Parallel analysis with one registry client per thread
status: accepted
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# Parallel analysis with one registry client per thread

## Context and Problem Statement

Analyzers spend most of their time waiting on I/O: registry calls and external tools. Run one after the other, the run time of `regis` is the sum of all analyzers, which slows every CI pipeline that calls it.

## Considered Options

* A sequential loop.
* `asyncio`.
* A thread pool.

## Decision Outcome

A thread pool. `regis/core/application/analyze_image.py` runs the selected analyzers in a `ThreadPoolExecutor`, with 4 workers by default; `--max-workers` overrides it. Each thread gets its own `RegistryClient`, so no HTTP session is shared between threads.

`asyncio` was rejected because the external tools and the registry client are synchronous: every call would have to be wrapped, for no gain over threads on I/O-bound work.

### Consequences

The run time follows the slowest analyzer rather than the sum of all of them (quality goal 3, CI integrability).
The cost: analyzers must be thread-safe, and a registry sees up to as many concurrent clients as there are workers.
