---
adr: SDR-0007
slug: tests
title: Tests
status: accepted
revision: 1
date: 2026-10-17
authors: [Tristan Rivoallan]
supersedes: []
traits:
  tests:
    coverage_target: 90
---

# Tests

> **Qu'est-ce que ce fichier ?** Un ADR — *Architecture Decision Record* — est une décision consignée : son contexte, les options pesées, ce qui a été retenu, et ce que ça coûte. **Tant qu'il porte `status: proposed`, il s'écrit et se corrige librement.**
>
> **La ligne `revision:` de l'en-tête date la question, pas le fichier.** Elle n'avance que si la question posée ici change — jamais pour une reformulation, une coquille ou un lien réparé. Vous ne la remplissez pas : elle arrive avec le fichier, et votre verdict lui reste attaché. Elle existe pour qu'on reconnaisse, plus tard, un verdict rendu contre une question qui a depuis bougé.
>
> **`rejected` est une réponse pleine, pas un abandon.** Quand la question ne se pose pas dans ce dépôt, l'ADR reçoit le verdict `rejected` avec son motif, et le bloc `traits:` disparaît en entier — une clé sans objet ne se laisse pas vide. Le motif dit alors **ce qui en tient lieu**, pour qu'un agent qui le lit sache à quoi s'en tenir. **Un ADR `rejected` sans bloc `traits:` passe la vérification** — c'est mesuré, pas supposé.

## Context and Problem Statement

**Concrètement, ce que statuer change.** Tant que cette clé est vide, un agent qui ajoute du code à ce dépôt ne sait pas quel niveau de couverture tenir — il n'en vise donc aucun, et livre du code testé au hasard de ce qui lui a semblé utile. Une fois la valeur écrite, il sait ce qu'il doit atteindre avant de proposer sa merge request.

La méthode impose déjà **le TDD** et **trois bornes fermées** à ce que « couverture » veut dire. Ce qui reste à vous : le **chiffre**, parce qu'il dépend de ce que ce dépôt fait et de ce que votre équipe défend en revue.

## Considered Options

* **Un seuil chiffré** — celui que votre équipe tient et sait défendre.
* **`aucun`** — pour un langage sans instrument de couverture, ou pour un dépôt où la mesure n'apprendrait rien. **C'est une réponse**, et elle se justifie dans ce corps comme une autre.

## Decision Outcome

**La réponse que la méthode propose, et ses motifs.**

| Clé | Valeur proposée | Motif |
| --- | --- | --- |
| `tests.coverage_target` | `90` | c'est le seuil que la méthode tient pour elle-même, et les trois bornes ci-dessous le rendent atteignable sans tricher |

**Les trois bornes ne se négocient pas**, et c'est ce qui rend le chiffre comparable d'un dépôt à l'autre :

1. **tests unitaires seulement** — un harnais d'intégration ne compte pas ;
2. **code écrit à la main** — hors tests, hors sorties engendrées, hors gabarits ;
3. **couverture de lignes**.

**Cette proposition ne lie pas ce dépôt.** Un dépôt qui vise plus haut le dit ; un dépôt qui vise plus bas le dit aussi, et écrit pourquoi. Ce qui n'est pas une réponse, c'est un chiffre qu'on ne tient pas.

**Le seuil vaut pour le langage principal**, celui que [`SDR-0004`](SDR-0004-languages.md) déclare. Un dépôt qui en porte plusieurs déclare les autres dans ce corps, avec leur instrument — la clé n'en porte qu'un, parce qu'un agent n'a besoin que de celui-là pour savoir où il en est.

**Décision.** La proposition est adoptée : 90.

**Provenance.** Constatée : `[tool.coverage.report].fail_under = 90` dans `pyproject.toml`, appliqué en global et par fichier par `tests/_per_file_coverage.py`.

### Consequences

Le seuil est exécutable : `make test` échoue sous 90 % en global ou pour un seul fichier de `regis/`.
Le coût : le gate par fichier est plus strict que la proposition, et un petit module peu testé bloque une pull request entière.

## More Information

| Clé | Ce qu'elle porte | Valeurs admises |
| --- | --- | --- |
| `tests.coverage_target` | le seuil de couverture du langage principal, en pourcentage | un nombre, ou `aucun` |

**Ce que cette clé ne couvre pas** : ni runner, ni commande de test, ni sortie attendue, ni instrument de couverture. La méthode ne les transporte pas — elle ne sait pas ce que votre dépôt lance.

**La valeur s'écrit dans ce fichier, et nulle part ailleurs.** Aucun autre fichier ne la recopie : celui qui en a besoin renvoie ici. C'est ce qui garantit qu'elle ne peut pas être contredite ailleurs.

**Une clé laissée vide n'est pas une réponse** — celle-ci est exigée. `aucun` en est une, le vide non.

**Et sur ce point précis, la commande ne vous protège pas.** Elle sait refuser une valeur hors d'un ensemble fermé — c'est ce qu'elle fait pour l'architecture ou pour les langues. Ici la valeur est un **nombre ou le mot `aucun`** : aucun type ne couvre les deux, donc **une clé restée vide passe au vert**. C'est la relecture qui l'attrape, et il vaut mieux le savoir que le découvrir.

```bash
( cd docs/adr && npx @jackchuka/mdschema@0.15.1 check '*.md' )
```

**Si votre dépôt n'a ni Node ni `npm`, cette ligne ne vous sert à rien**, et le dire vaut mieux que le supposer. **Elle peut aussi échouer alors que Node est là.** Mesuré le 2026-09-20 sur macOS arm64, avec `npm` 10.9.8 puis 11.6.0 : `npx` rend `sh: mdschema: command not found`, parce que `npm` n'installe pas le lien du binaire — sur un répertoire neuf, avec `bin-links` à `true` et `ignore-scripts` à `false`. Le paquet est pourtant posé, sa dépendance de plateforme aussi, et son point d'entrée existe.

Dans les deux cas, `mdschema` est un binaire autonome : prenez-le dans les *releases* de [son dépôt](https://github.com/jackchuka/mdschema) et lancez `mdschema check '*.md'` depuis ce répertoire. **C'est le chemin sûr**, et non un repli de second choix. La ligne ci-dessus n'est qu'un raccourci, qui évite d'installer quoi que ce soit — quand il fonctionne.

Le schéma qu'elle applique est le `.mdschema.yml` de ce même répertoire, posé par la méthode. Elle nomme, fichier par fichier : une clé restée vide, une valeur hors de l'ensemble admis, un `status:` resté `proposed`, une `date:` absente, et le mode d'emploi qu'on aurait oublié de supprimer. **Elle reconnaît ce dernier à sa première phrase**, pas au tableau : le tableau a le droit de rester, et le garder ne déclenche rien. Elle ne juge pas votre décision — seulement qu'elle est prise.
