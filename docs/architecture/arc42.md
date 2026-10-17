---
date: 2026-10-17
title: regis architecture
---

Based on the arc42 template, version 9.0-EN (July 2025), © Dr. Peter
Hruschka, Dr. Gernot Starke and contributors. See <https://arc42.org>.

Only sections 1 and 9 are written so far. The detailed architecture
(layers, ports, adapters) lives in
[`docs/memory-bank/systemPatterns.md`](../memory-bank/systemPatterns.md);
this document links to it rather than copying it.

# Introduction and Goals

## Requirements Overview

`regis` judges a container image against a **playbook** of declarative rules
and produces a verdict, a machine-readable report and an HTML report. It lets
a platform decide, in CI and without a human in the loop, whether an image may
enter a catalogue, and lets a person understand that decision afterwards.

### Essential Features

- Analyse an image by digest with pluggable analyzers: vulnerabilities, secrets,
  SBOM, Dockerfile and image linting, freshness, end of life, size, popularity,
  provenance, OpenSSF Scorecard, metadata.
- Evaluate the analysis against a playbook: JSON Logic criteria, rule templates
  instantiated with options, a verdict per rule and for the image.
- Produce a JSON report validated by a versioned schema, plus a Markdown and an
  interactive HTML report that explain each refusal.
- Run as a CLI or a container image (slim and full variants) in any CI.
- Extend: a new analyzer registers through a Python entry point; a new rule is
  written in a playbook, without code.

### Business Context

Teams that run an internal image catalogue need a gate that says, for each
image, whether it is acceptable, and why. Scanners give findings, not
decisions; `regis` turns findings into a verdict against a policy that the
security team writes and audits. Within the OCI workspace, `regis` says
*whether*, `knock` places the image, and `uske` schedules both and records the
outcome. `regis` knows neither of them.

### References

- [`docs/README.md`](../README.md): user documentation entry point.
- [`docs/reference/`](../reference/): generated rule and schema reference.
- [`docs/memory-bank/projectbrief.md`](../memory-bank/projectbrief.md) and
  [`productContext.md`](../memory-bank/productContext.md): scope and product context.

## Quality Goals

Top quality requirements, in priority order. Every architecture decision must
support them; a lower goal yields to a higher one.

| Priority | Quality Goal | Concrete Scenario |
|:--------:|--------------|-------------------|
| 1 | `#reliable` Reproducibility | The same image digest, evaluated with the same playbook, the same pinned tool versions and the same vulnerability database snapshot (its checksum is recorded in the report, under `results.cve.source`), yields the identical verdict on 10 runs out of 10. |
| 2 | `#usable` Explainability of the verdict | 100 % of failed rules name, in the report, the criterion, the observed value and the expected threshold, so that a refusal is understood without asking the maintainer. |
| 3 | `#operable` CI integrability | The JSON report is validated by a versioned schema (`REPORT_SCHEMA_VERSION`), and no exit code changes meaning outside a major release. |
| 4 | `#flexible` Extensibility | A new analyzer is added through an entry point, without modifying `regis/core/application` or the CLI. |

Detailed quality scenarios belong to section 10, not yet written.

**Quality goal sign-off:** the `regis` maintainer.

## Stakeholders

| Role | Contact | Expectations |
|------|---------|--------------|
| Platform security owner (primary user) | GitHub issues | Can explain, from the report alone, why an image was refused, and defend the gate. |
| Architect consuming the catalogue (secondary user) | GitHub issues | Knows which images are admitted and under which policy. |
| Security team (policy author) | GitHub issues | Auditable playbooks; no silent false negative; a rule change shows in the verdict. |
| CI operators | GitHub issues | Bounded run time, pinned external tools, a light image, stable exit codes. |
| Orchestrators (`uske`, `knock`) | Their repositories | Versioned report schema and stable exit codes they can script against. |
| Open source contributors | Pull requests | Readable architecture, explicit CI gates, an analyzer added without touching the core. |

# Architecture Constraints

# Context and Scope

## Business Context

**\<Diagram or Table\>**

**\<optionally: Explanation of external domain interfaces\>**

## Technical Context

**\<Diagram or Table\>**

**\<optionally: Explanation of technical interfaces\>**

**\<Mapping Input/Output to Channels\>**

# Solution Strategy

# Building Block View

## Whitebox Overall System

***\<Overview Diagram\>***

Motivation  
*\<text explanation\>*

Contained Building Blocks  
*\<Description of contained building block (black boxes)\>*

Important Interfaces  
*\<Description of important interfaces\>*

### \<Name black box 1\>

*\<Purpose/Responsibility\>*

*\<Interface(s)\>*

*\<(Optional) Quality/Performance Characteristics\>*

*\<(Optional) Directory/File Location\>*

*\<(Optional) Fulfilled Requirements\>*

*\<(optional) Open Issues/Problems/Risks\>*

### \<Name black box 2\>

*\<black box template\>*

### \<Name black box n\>

*\<black box template\>*

### \<Name interface 1\>

…​

### \<Name interface m\>

## Level 2

### White Box *\<building block 1\>*

*\<white box template\>*

### White Box *\<building block 2\>*

*\<white box template\>*

…​

### White Box *\<building block m\>*

*\<white box template\>*

## Level 3

### White Box \<\_building block x.1\_\>

*\<white box template\>*

### White Box \<\_building block x.2\_\>

*\<white box template\>*

### White Box \<\_building block y.1\_\>

*\<white box template\>*

# Runtime View

## \<Runtime Scenario 1\>

- *\<insert runtime diagram or textual description of the scenario\>*

- *\<insert description of the notable aspects of the interactions
  between the building block instances depicted in this diagram.\>*

## \<Runtime Scenario 2\>

## …​

## \<Runtime Scenario n\>

# Deployment View

## Infrastructure Level 1

***\<Overview Diagram\>***

Motivation  
*\<explanation in text form\>*

Quality and/or Performance Features  
*\<explanation in text form\>*

Mapping of Building Blocks to Infrastructure  
*\<description of the mapping\>*

## Infrastructure Level 2

### *\<Infrastructure Element 1\>*

*\<diagram + explanation\>*

### *\<Infrastructure Element 2\>*

*\<diagram + explanation\>*

…​

### *\<Infrastructure Element n\>*

*\<diagram + explanation\>*

# Cross-cutting Concepts

## *\<Concept 1\>*

*\<explanation\>*

## *\<Concept 2\>*

*\<explanation\>*

…​

## *\<Concept n\>*

*\<explanation\>*

# Architecture Decisions

## Overview

Decisions are recorded as MADR files under [`docs/adr/`](../adr/), one file
per decision, with a machine-readable frontmatter (`status`, `traits`) checked
by `mdschema` (see SDR-0001). This section is the index: it states what each
decision fixes and which quality goal it serves, and links to the ADR for the
context, the options weighed and the consequences. It never copies them.

A decision that changes gets a new ADR that supersedes the old one; the old
file stays, marked. The `SDR-*` files are inherited from an engineering
method and were given their verdict on 2026-10-17; ADRs written for `regis`
itself start at 0015 and follow the same format.

### Decision Log

| ADR | Decision | Status | Date | Quality goals served |
|-----|----------|--------|------|----------------------|
| [SDR-0001](../adr/SDR-0001-record-architecture-decisions.md) | Decisions are MADR files with a checked frontmatter | Accepted | 2026-08-29 | 4 Extensibility (decisions readable by agents and contributors) |
| [SDR-0003](../adr/SDR-0003-architecture.md) | Hexagonal architecture, enforced by import-linter; this arc42 document | Accepted | 2026-10-17 | 1 Reproducibility, 4 Extensibility |
| [SDR-0004](../adr/SDR-0004-languages.md) | Python is the main language | Accepted | 2026-10-17 | 4 Extensibility |
| [SDR-0005](../adr/SDR-0005-validation.md) | JSON Schema validates data at the boundary and in data files | Accepted | 2026-10-17 | 3 CI integrability, 2 Explainability |
| [SDR-0007](../adr/SDR-0007-tests.md) | 90 % line coverage, globally and per file | Accepted | 2026-10-17 | 1 Reproducibility |
| [SDR-0010](../adr/SDR-0010-forge-and-ci.md) | GitHub, with a blocking CI gate | Accepted | 2026-10-17 | 1 Reproducibility, 3 CI integrability |
| [SDR-0011](../adr/SDR-0011-delivery.md) | Release Please; images published to `ghcr.io` on tag; no deployment | Accepted | 2026-10-17 | 3 CI integrability |
| [0015](../adr/0015-analyzers-discovered-through-entry-points.md) | Analyzers are discovered through Python entry points | Accepted | 2026-10-17 | 4 Extensibility |
| [0016](../adr/0016-rules-in-json-logic.md) | Rules are JSON Logic, with custom operators | Accepted | 2026-10-17 | 1 Reproducibility, 2 Explainability |
| [0017](../adr/0017-parallel-analysis-one-client-per-thread.md) | Analyzers run in a thread pool, one registry client per thread | Accepted | 2026-10-17 | 3 CI integrability |
| [0018](../adr/0018-external-tools-as-subprocesses.md) | External tools are called as subprocesses, versions pinned | Accepted | 2026-10-17 | 1 Reproducibility |
| [SDR-0002](../adr/SDR-0002-localization.md) | English by default, commit messages in French | Accepted | 2026-10-17 | 2 Explainability (public readers) |
| [SDR-0006](../adr/SDR-0006-commits.md) | Conventional Commits with fixed scopes, checked on the PR title | Accepted | 2026-10-17 | 3 CI integrability (versions derived from messages) |
| [SDR-0008](../adr/SDR-0008-documentation.md) | Plain Markdown under `docs/`, public audience | Accepted | 2026-10-17 | 2 Explainability |
| [SDR-0009](../adr/SDR-0009-branching.md) | GitHub flow, squash merge | Accepted | 2026-10-17 | 3 CI integrability |
| [SDR-0000](../adr/SDR-0000-socle-de-service.md) | No service operating principles: `regis` is an open source tool | Rejected | 2026-10-17 | none |
| [SDR-0013](../adr/SDR-0013-frontend.md) | No frontend framework: the HTML report is rendered from templates | Rejected | 2026-10-17 | none |
| [SDR-0014](../adr/SDR-0014-work-tracking.md) | No Jira: work is tracked in GitHub issues | Rejected | 2026-10-17 | none |

*Architecturally significant decisions first (style, language, validation,
quality gates, delivery), then conventions, then rejected questions.*

### Implications

What each architecturally significant decision engages. Building blocks are
named as in [`docs/memory-bank/systemPatterns.md`](../memory-bank/systemPatterns.md);
risks refer to the section *Risks and Technical Debts*.

**SDR-0003 Hexagonal architecture**
- Building blocks: `core` (model, ports, domain, application) and `adapters` (driven, driving).
- Quality goals: 1 Reproducibility (the domain runs without I/O), 4 Extensibility.
- Constraints created: no import from an outer layer, enforced by import-linter in `make lint`.
- Risks: none.

**SDR-0005 JSON Schema validation**
- Building blocks: `core/domain`, `schemas/`.
- Quality goals: 3 CI integrability, 2 Explainability.
- Constraints created: every data format that `regis` reads or writes has a published schema.
- Risks: none.

**SDR-0007 Coverage gate**
- Building blocks: every module under `regis/`.
- Quality goals: 1 Reproducibility.
- Constraints created: a single file under 90 % coverage blocks the pull request.
- Risks: none.

**SDR-0010 GitHub and a blocking CI gate**
- Building blocks: `.github/workflows/`.
- Quality goals: 1 Reproducibility, 3 CI integrability.
- Constraints created: five required checks before any merge to `main`.
- Risks: none.

**SDR-0011 Delivery**
- Building blocks: `release.yml`, the `slim` and `full` images.
- Quality goals: 3 CI integrability.
- Constraints created: a version exists only through a tag set by Release Please.
- Risks: RISK-02, for the `full` image, which ships grype.

**0015 Analyzers discovered through entry points**
- Building blocks: `core/domain/analyzers`, `adapters/driven/analyzers`.
- Quality goals: 4 Extensibility.
- Constraints created: the entry point group `regis.analyzers` is a public contract.
- Risks: none.

**0016 Rules in JSON Logic**
- Building blocks: `core/domain/rules`, `core/domain/playbook`.
- Quality goals: 1 Reproducibility, 2 Explainability.
- Constraints created: the set of custom operators is part of the playbook contract.
- Risks: RISK-01.

**0017 Parallel analysis**
- Building blocks: `core/application`, `adapters/driven/registry`.
- Quality goals: 3 CI integrability.
- Constraints created: analyzers must be thread-safe.
- Risks: none.

**0018 External tools as subprocesses**
- Building blocks: `adapters/driven/tools`.
- Quality goals: 1 Reproducibility.
- Constraints created: the tools are on the `PATH` or fetched, with pinned versions.
- Risks: RISK-02.

# Quality Requirements

## Quality Requirements Overview

## Quality Scenarios

# Risks and Technical Debts

| ID | Risk | Quality goal | Priority | Mitigation |
|----|------|--------------|----------|------------|
| RISK-01 | A failed rule does not yet always name the criterion, the observed value and the threshold, so a refusal can still need the maintainer to be understood. | 2 Explainability | High | The change that makes every refusal self-explanatory; the goal holds once it is released. |
| RISK-02 | `regis` cannot impose a vulnerability database snapshot: grype updates its database, so the same digest can get a different verdict from one day to the next. | 1 Reproducibility | Medium | The snapshot checksum is recorded in the report, so a change of verdict can be traced to a database change. Imposing a snapshot is a future capability. |

# Glossary

| Term         | Definition         |
|--------------|--------------------|
| *\<Term-1\>* | *\<definition-1\>* |
| *\<Term-2\>* | *\<definition-2\>* |
