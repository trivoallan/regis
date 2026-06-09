# Per-file coverage gate (≥ 90 %)

**Date** : 2026-06-08
**Statut** : approuvé (design), prêt pour planification

## Problème

Le seuil de couverture du projet est **global** : `--cov-fail-under=90` (addopts)
et `[tool.coverage.report].fail_under = 90`. Un fichier peu testé peut donc rester
sous 90 % tant que d'autres fichiers très couverts maintiennent la moyenne au-dessus
du seuil. Aujourd'hui la couverture globale est à 92 %, mais **8 fichiers sont sous
90 %** (de 73 % à 88 %).

Objectif : garantir qu'**aucun fichier individuel** de `regis/` ne descende sous 90 %.

## Décisions de cadrage

| Décision          | Choix retenu                                                                                                                     |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Périmètre         | **Tous les fichiers, toujours.** Échec dur si un seul fichier < 90 %, qu'il soit touché ou non par la PR.                        |
| Exemptions        | **Aucune liste d'exemptions.** Pas de baseline gelée.                                                                            |
| Fichiers legacy   | **Remontés ≥ 90 % d'abord**, dans la même livraison, avant d'armer le gate.                                                      |
| Mécanisme         | **Plugin pytest intégré** (hook `pytest_sessionfinish`). Une seule commande `pipenv run pytest` enforce tout, en local et en CI. |
| Seuil par-fichier | **Identique au seuil global** (90), lu depuis l'unique source `[tool.coverage.report].fail_under`. Pas de second chiffre en dur. |

## Comportement cible

`pipenv run pytest` échoue si au moins un fichier de `regis/` est sous 90 %, en
plus du gate global existant. Le message d'échec liste chaque fichier fautif avec
son pourcentage, trié du pire au meilleur. Exemple :

```text
FAILED per-file coverage gate: 2 file(s) below 90.0%
   73.3%  regis/tools/cosign.py
   84.7%  regis/rules/evaluator.py
```

- `pytest --no-cov` reste un **no-op** : la boucle d'itération rapide est intacte.
- Tout **nouveau** fichier sous 90 % est bloqué automatiquement, sans config à
  maintenir.

## Architecture

### Le plugin

- **Emplacement** : la logique de seuil vit dans un module dédié et isolé,
  `tests/_per_file_coverage.py`, enregistré via `tests/conftest.py`. Le module
  expose une fonction pure prenant des données de couverture (mapping
  `fichier -> pourcentage`) + un seuil, et renvoyant la liste triée des fichiers
  fautifs — testable sans lancer toute la suite.
- **Hook** : `pytest_sessionfinish` en `hookwrapper`, pour s'exécuter **après**
  pytest-cov (qui combine et écrit les données en fin de session).
- **Source des données** : l'objet `Coverage` de coverage.py via son API
  (`get_data()` / `analysis2` ou équivalent), pas un parse de fichier sur disque.
  Robuste et déjà disponible en mémoire après pytest-cov.
- **Seuil** : lu depuis `[tool.coverage.report].fail_under` dans `pyproject.toml`
  (parse via `tomllib`). Une seule source de vérité partagée avec le gate global.

### Cas limites

| Cas                                          | Comportement                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `--no-cov` (couverture non collectée)        | Sortie silencieuse, aucun échec.                                                            |
| Fichiers `omit` (`regis/cookiecutters/*`)    | Exclus automatiquement : on lit les données coverage déjà filtrées par la config existante. |
| Fichier à 0 instruction (`__init__.py` vide) | Ignoré (considéré comme passant).                                                           |
| Échec                                        | `session.exitstatus` forcé non nul + tableau fautif imprimé dans le résumé terminal.        |

### Flux

```text
pytest run
  ├─ pytest-cov collecte + écrit les données de couverture (sessionfinish)
  └─ hookwrapper per-file gate (sessionfinish, après pytest-cov)
       ├─ couverture absente ? → no-op
       ├─ lit le seuil depuis pyproject.toml
       ├─ calcule % par fichier depuis l'objet Coverage
       ├─ filtre les fichiers 0-instruction
       ├─ collecte les fichiers < seuil
       └─ si non vide → imprime + exitstatus ≠ 0
```

## Travail préalable — remonter les 8 fichiers

Avant d'armer le gate, écrire en **TDD** les tests manquants pour amener chacun
des fichiers suivants ≥ 90 %. Chaque fichier est une étape isolée, ordonnée du
plus bas au plus haut :

| % actuel | Fichier                        |
| -------- | ------------------------------ |
| 73.3     | `regis/tools/cosign.py`        |
| 73.8     | `regis/commands/doctor.py`     |
| 75.0     | `regis/utils/process.py`       |
| 78.6     | `regis/playbook/sections.py`   |
| 79.4     | `regis/analyzers/endoflife.py` |
| 83.2     | `regis/playbook/evaluator.py`  |
| 84.7     | `regis/rules/evaluator.py`     |
| 87.8     | `regis/playbook/conditions.py` |

Le plugin lui-même (`tests/_per_file_coverage.py`) doit aussi être ≥ 90 %.

> Note : `tests/` n'est pas mesuré par coverage (`source = ["regis"]`), donc le
> module de plugin sous `tests/` n'est pas soumis au gate. Sa couverture est
> néanmoins assurée par ses propres tests unitaires (section suivante).

## Tests du plugin

Tests unitaires de la fonction de seuil, indépendants d'un run complet :

- fichier sous le seuil → présent dans la liste fautive, trié ;
- tous les fichiers ≥ seuil → liste vide (succès) ;
- `--no-cov` / couverture absente → no-op ;
- fichier 0-instruction → ignoré ;
- lecture correcte du seuil depuis `pyproject.toml`.

## Intégration & documentation

- **Aucun nouveau step CI** : le gate vit dans `pipenv run pytest`, déjà lancé en
  CI et en pré-PR.
- Mettre à jour `CLAUDE.md` (section Commands) pour signaler le gate par-fichier.
- Mettre à jour le memory-bank (`systemPatterns.md` et/ou `techContext.md`) pour
  documenter la règle « aucun fichier < 90 % » et son mécanisme.

## Hors périmètre (YAGNI)

- Pas de seuil par-fichier distinct du seuil global.
- Pas de liste d'exemptions ni de baseline gelée.
- Pas de couverture par-diff (l'absolu par fichier couvre déjà les nouveaux fichiers).
- Pas de dépendance tierce.
