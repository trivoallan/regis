---
adr: "0016"
title: Rules expressed in JSON Logic
status: accepted
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# Rules expressed in JSON Logic

## Context and Problem Statement

Playbooks are written by security teams, not by Python developers. A rule must be data that can be versioned, reviewed and audited, and its evaluation must give the same result for the same input.

## Considered Options

* Rules as Python callables.
* A custom rule language.
* JSON Logic.

## Decision Outcome

JSON Logic, through the `json-logic-qubit` library (`pyproject.toml`). `regis` adds its own operators in `regis/core/domain/rules/evaluator.py` (`_add_custom_operations`): `intersects`, `contains_all`, `subset`, `keys`, `get`, `env_contains`, `matches`, `is_true`, `is_false`, `is_url`, `is_empty` and `is_set`.

Python callables were rejected because a playbook would become code, which a security team can neither write nor audit. A custom language was rejected because it needs a parser, tooling and documentation that JSON Logic already has.

### Consequences

A rule is data, written in YAML and validated by a JSON Schema ([SDR-0005](SDR-0005-validation.md)), and its evaluation is deterministic (quality goals 1, Reproducibility, and 2, Explainability).
The cost: the custom operators form a dialect that other JSON Logic engines do not know, and each new operator widens it. The operator list is part of the playbook contract.
