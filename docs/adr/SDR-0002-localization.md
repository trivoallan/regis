---
adr: SDR-0002
slug: localization
title: Localization
status: accepted
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  localization:
    language:
      default: anglais
      commits: français
---

# Localization

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que ces clés sont vides, un agent qui écrit du code dans ce dépôt ne sait pas en quelle langue nommer une fonction, ni s'il doit commenter en français, ni comment rédiger un message de commit. Il devine — et il devine différemment d'une fois sur l'autre. Une fois la valeur écrite, il la lit et l'applique, sans vous la redemander.

La question se pose parce que les supports n'ont pas les mêmes lecteurs. Une documentation s'adresse à l'équipe et à ceux qui la rejoindront ; un symbole, à quiconque lit le code, y compris hors de l'équipe ; un commentaire, à celui qui relit une fonction dans six mois ; un message de commit, à qui remonte l'historique dans deux ans. Répondre « la même langue partout » est une réponse, mais c'en est une, et elle se choisit — c'est ce que `default` sert à dire.

## Considered Options

- **Tout en français** — documentation, commits, symboles, commentaires.
- **Prose française, symboles anglais** — la proposition de la méthode, décrite ci-dessous.
- **Tout en anglais** — pour un dépôt ouvert ou une équipe non francophone.
- **Un autre découpage** — les quatre surcharges sont indépendantes, rien n'oblige à les aligner.

## Decision Outcome

**La réponse que la méthode propose, et ses motifs.** Une langue par défaut, et une seule surcharge :

| Clé       | Valeur proposée | Motif                                                                                                    |
| --------- | --------------- | -------------------------------------------------------------------------------------------------------- |
| `default` | `français`      | l'équipe l'est, et tout ce qui s'adresse à elle suit                                                     |
| `code`    | `anglais`       | un symbole est lu par des outils et par des gens hors de l'équipe ; l'anglais y est la langue par défaut |

`documentation`, `commits` et `comments` ne sont pas renseignés : ils prennent `default`. **Ne remplissez une de ces trois clés que pour vous écarter du défaut** — sinon, laissez-la vide, c'est ce qui rend la décision lisible d'un coup d'œil. La retirer dit la même chose : les deux formes passent la vérification, et vous n'avez pas à défaire l'une pour l'autre.

**Cette proposition ne lie pas ce dépôt.** Elle existe pour qu'il y ait quelque chose à quoi réagir, plutôt qu'une page blanche : elle se garde, s'amende ou s'écarte.

**Décision, et où elle s'écarte de la proposition.** `default: anglais` au lieu de `français` : `regis` est un dépôt public, lu hors de l'équipe ; code, commentaires, README et `docs/` y sont en anglais. `commits: français` reprend la pratique du dépôt. Le Memory Bank (`docs/memory-bank/`) et les specs internes restent en français : exception locale, consignée ici plutôt qu'en trait.

**Provenance.** `default` et `commits` : répondues le 2026-10-17 (onboarding, cadrage passe 2). `commits: français` est aussi constatée sur `git log` (`feat(report): expliquer chaque refus dans le rapport HTML`).

### Consequences

Un agent écrit le code, les commentaires et la documentation en anglais, et les messages de commit en français, sans avoir à deviner.
Le coût : deux langues dans le même dépôt, et le Memory Bank en français reste une exception que seule cette page explique.

## More Information

| Clé             | Ce qu'elle porte                                               | Valeurs admises       |
| --------------- | -------------------------------------------------------------- | --------------------- |
| `default`       | la langue de tout ce qui n'est pas surchargé ci-dessous        | `français`, `anglais` |
| `documentation` | la documentation, si elle diffère du défaut                    | `français`, `anglais` |
| `commits`       | les messages de commit, s'ils diffèrent                        | `français`, `anglais` |
| `code`          | les symboles — fonctions, classes, variables — s'ils diffèrent | `français`, `anglais` |
| `comments`      | les commentaires de code, s'ils diffèrent                      | `français`, `anglais` |

**Seule `default` est exigée.** Les quatre autres sont des surcharges : une clé vide — ou retirée — veut dire « comme `default` », et c'est une réponse, pas un oubli.

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**`default` laissée vide n'est pas une réponse** — les quatre surcharges, si : vides, elles disent « comme `default` ». Vous n'avez pas à distinguer ces deux vides à l'œil : la commande ci-dessous refuse `default` vide en la nommant, et laisse passer une surcharge vide. **Elle ne voit pas `default` retirée** : la clé absente passe, et seule la relecture l'attrape. Mesuré le 2026-09-20 sur `mdschema` 0.15.1 — un champ y est requis pour tous les ADR du répertoire ou pour aucun, et l'exiger ferait échouer chacun de vos ADR qui ne parle pas de langue. Depuis la racine de votre dépôt :

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
