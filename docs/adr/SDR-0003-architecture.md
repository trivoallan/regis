---
adr: SDR-0003
slug: software-architecture
title: Software Architecture
status: accepted
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  architecture:
    pattern: hexagonal
    document: arc42
---

# Software Architecture

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que cette clé est vide, un agent qui ajoute un module à ce dépôt invente une structure — et il en invente une différente à chaque fois, parce qu'il déduit du fichier qu'il a sous les yeux. Une fois la valeur écrite, il sait où poser le code et ce qui a le droit de dépendre de quoi.

La question se pose tôt parce qu'elle est chère à défaire : une arborescence et des frontières de dépendance se changent module par module, longtemps après qu'on a cessé d'y penser.

**Cet ADR gouverne aussi le sort de `docs/architecture/arc42.md`.** Tant que ce fichier manque, le premier artefact de chaque change propose de le créer depuis le gabarit [arc42](https://arc42.org/download). Si votre architecture vit déjà ailleurs — un document mûr sous un autre chemin —, ou si vous ne tenez pas de document d'architecture, dites-le par la clé `architecture.document` : `ailleurs` ou `aucun` font taire la proposition.

## Considered Options

* **`hexagonal`** — ports & adapters : le domaine ne dépend d'aucune I/O.
* **`layered`** — couches classiques, chacune ne connaissant que la suivante.
* **`microservices`** — des services déployés séparément.
* **`monolithic`** — un seul déployable, sans frontière interne forte.
* **`event-driven`** — les composants communiquent par événements.
* **`soa`** — services partagés, couplés par contrats.

## Decision Outcome

**La réponse que la méthode propose, et ses motifs.**

| Clé | Valeur proposée | Motif |
| --- | --- | --- |
| `architecture.pattern` | `hexagonal` | **il convient bien au travail agentique** : le domaine ne dépend d'aucune I/O, donc un agent l'écrit et le teste sans environnement qui tourne, et change un adaptateur sans toucher au domaine |

Le motif mérite d'être développé, parce qu'il n'est pas le motif habituel. Un pattern hexagonal borne ce qu'un agent doit tenir en tête pour modifier une règle : le domaine seul, sans base, sans réseau, sans framework. C'est aussi ce qui rend une modification vérifiable sans monter d'environnement — un agent sait donc s'il a cassé quelque chose, au lieu de le supposer.

**Cette proposition ne lie pas ce dépôt.** Elle vaut pour un service applicatif de taille moyenne. Sous 500 lignes, ou pour un dépôt qui n'est pas un service, `monolithic` est souvent la réponse honnête — et si la question n'a pas d'objet ici, statuez `rejected`.

**Décision.** La proposition est adoptée : `hexagonal`, et le document d'architecture sous `docs/architecture/arc42.md`.

**Provenance.** `pattern: hexagonal` est constatée : le contrat import-linter « Hexagonal layering » de `pyproject.toml`, vérifié en CI par `make lint`, impose `adapters > core.application > core.domain > core.ports > core.model`. `document: arc42` est répondue le 2026-10-17 (onboarding, cadrage passe 1).

### Consequences

La règle de dépendance est déjà exécutable : import-linter fait échouer la CI quand une couche importe au-dessus d'elle.
Le coût : `docs/architecture/arc42.md` et `docs/memory-bank/systemPatterns.md` décrivent la même architecture ; le premier doit renvoyer au second plutôt que le recopier.

## More Information

| Clé | Ce qu'elle porte | Valeurs admises |
| --- | --- | --- |
| `architecture.pattern` | le pattern qui structure le code de ce dépôt | `event-driven`, `hexagonal`, `layered`, `microservices`, `monolithic`, `soa` |
| `architecture.document` | où vit le document d'architecture de ce dépôt | `arc42` (`docs/architecture/arc42.md`), `ailleurs`, `aucun` |

**Deux clés, et c'est délibéré.** La méthode ne transporte pas votre arborescence, vos noms de paquets ni vos règles de dépendance : elles se décident chez vous et se lisent dans ce corps. Le trait ne porte que ce qu'un agent doit lire sans interpréter.

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**Une clé laissée vide n'est pas une réponse** — celle-ci est exigée, et vous n'avez pas à le vérifier à l'œil. Depuis la racine de votre dépôt :

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
