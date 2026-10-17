---
adr: SDR-0013
slug: frontend
title: Frontend
status: rejected
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# Frontend

## Context and Problem Statement

La méthode prescrit un framework front pour toute interface web qu'un dépôt construit. `regis` n'a pas d'application front : son rapport HTML est rendu depuis des gabarits (`regis/templates/`, `regis/cookiecutters/`), sans framework ni build front.

## Considered Options

* Adopter le framework et le thème proposés.
* Le rejeter, le dépôt n'ayant pas de front applicatif.

## Decision Outcome

`rejected`. **Ce qui en tient lieu** : les gabarits du rapport HTML, sous la portée de commit `templates`, et le *Google HTML/CSS Style Guide* que nomme `CLAUDE.md`.

Provenance : répondu le 2026-10-17 (onboarding, cadrage passe 2).

### Consequences

Un agent qui touche au rapport HTML ne tire aucun framework front dans le dépôt.
Le coût : si `regis` gagnait une interface web, cette question serait à reprendre.
