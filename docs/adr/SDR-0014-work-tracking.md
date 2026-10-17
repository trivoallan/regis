---
adr: SDR-0014
slug: work-tracking
title: Suivi du travail dans Jira
status: rejected
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# Suivi du travail dans Jira

## Context and Problem Statement

La méthode propose de rattacher chaque change à un ticket d'un outil de suivi. `regis` est un dépôt public dont le travail se suit sur la forge publique.

## Considered Options

* Rattacher chaque change à une story Jira.
* Le rejeter, et suivre le travail sur la forge publique.

## Decision Outcome

`rejected`. **Ce qui en tient lieu** : les issues et pull requests GitHub du dépôt.

Provenance : répondu le 2026-10-17 (onboarding, cadrage passe 2).

### Consequences

Aucun agent n'a besoin d'un accès à Jira pour travailler dans `regis`.
Le coût : le lien entre un change et un besoin passe par l'issue GitHub, pas par une clé normalisée.
