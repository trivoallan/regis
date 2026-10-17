---
adr: SDR-0000
slug: socle-de-service
title: Principes d'exploitation
status: rejected
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
---

# Principes d'exploitation

## Context and Problem Statement

La méthode propose des principes d'exploitation pour les services qu'un dépôt met en production. `regis` est un outil en ligne de commande open source, publié sur un dépôt public : il n'expose pas de service en production.

## Considered Options

* Adopter ces principes.
* Le rejeter, la question ne se posant pas pour un outil open source.

## Decision Outcome

`rejected`. Rien de ce que portent ces principes ne s'applique à `regis`. **Ce qui en tient lieu** : la licence et la gouvernance du dépôt public, et les ADR qui portent un verdict dans `docs/adr/`.

Provenance : répondu le 2026-10-17 (onboarding, cadrage passe 2).

### Consequences

Aucune règle d'exploitation de service ne pèse sur un agent qui travaille dans `regis`.
Le coût : si `regis` devenait un service exploité en production, cet ADR serait à rouvrir depuis le texte de la méthode.
