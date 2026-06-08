# Spec — UX du `meta` dans les règles

- **Date** : 2026-06-08
- **Statut** : validé (brainstorming) — prêt pour plan d'exécution
- **Type** : feature transverse (rupture report) + helpers + doc
- **Scope** : `regis/rules/evaluator.py`, `regis/playbook/context.py`,
  `regis/analyzers/metadata.py`, `regis/commands/analyze.py`,
  `regis/schemas/meta/well-known.schema.json`,
  `regis/schemas/report/report.schema.json`, `regis/utils/report.py`,
  doc `docs/website/docs/concepts/rules.md` (+ référence, upgrade).

## Problème

Écrire une règle qui consomme une valeur `--meta` est aujourd'hui pénible et
mal outillé :

1. **Chemin incohérent et non documenté.** `regis analyze --meta k=v` écrit le
   même dict à **deux** endroits du rapport : top-level `metadata.*` **et**
   `request.metadata.*` (cf. `analyze.py` flux normal et flux `--rerun`). Aucune
   page de doc ne montre comment référencer une valeur meta dans une condition
   JSON Logic.
2. **Valeurs toujours chaînes.** `_parse_meta` produit des chaînes (une clé sans
   `=` vaut `"true"`). Tester un drapeau booléen impose
   `{"==": [{"var": "..."}, "true"]}` ; valider une URL est impossible sans
   opérateur dédié.
3. **`incomplete` parasite.** `MissingDataTracker` marque une règle `incomplete`
   dès qu'une condition accède à une clé manquante. Tester l'absence d'un meta
   (le cas d'usage de `is_set`/`is_empty`) rend donc la règle `incomplete` au
   lieu de produire un pass/fail propre. Or `incomplete` signifie « un analyzer
   n'a pas tourné », pas « l'utilisateur n'a pas passé ce meta ».
4. **Schéma well-known inerte.** `--meta ci.job.url=x` produit la structure
   imbriquée `{ci: {job: {url: x}}}`, mais `well-known.schema.json` déclare des
   propriétés à **clés plates pointées** (`"ci.job.url"`) qui ne matchent jamais
   cette structure. Conséquence : `enum` sur `ci.platform` et `format: uri` sur
   `ci.job.url` ne s'appliquent **jamais**.

## Objectif

Faire du `metadata.*` un namespace de première classe pour les règles :
chemin unique documenté, helpers ergonomiques pour les valeurs-chaînes, absence
testable sans `incomplete`, et validation well-known qui fonctionne réellement.

## Décisions (issues du brainstorming)

| Sujet                 | Décision                                                                                |
| :-------------------- | :-------------------------------------------------------------------------------------- |
| Namespace meta        | **Normaliser à la source** : un seul emplacement, top-level `metadata.*`.               |
| Emplacement canonique | **Top-level `metadata.*`** ; `request.metadata` supprimé.                               |
| Helpers retenus       | `is_true` / `is_false`, `is_url`, `is_empty` / `is_set`, `matches`.                     |
| Helpers écartés       | `is_semver`, `to_number` (YAGNI).                                                       |
| Absence de meta       | `metadata.*` est un **namespace optionnel** : clé manquante → `null` sans `incomplete`. |
| Schéma well-known     | **Corrigé dans ce lot** (structure imbriquée, enum/format réellement appliqués).        |

## Design

### 1. Normalisation du namespace (rupture report)

- `analyze.py` cesse d'écrire `request["metadata"]` (flux normal **et** flux
  `--rerun`). Seul `report["metadata"]` est peuplé.
- `report.schema.json` : suppression de `request.properties.metadata` ; le
  top-level `metadata` est conservé et sa description précisée (« métadonnées
  utilisateur arbitraires, namespace optionnel exposé aux règles sous
  `metadata.*` »).
- `REPORT_SCHEMA_VERSION` **2 → 3** (`regis/utils/report.py`). Mise à jour de la
  fixture contrat `tests/fixtures/report.v1.json` et de tout test asséné sur la
  version.
- **Coordination** : rupture d'enveloppe report à séquencer avec la file
  « presentation generalization » (consommateurs aval : regis-gitlab,
  regis-backstage, regis-action). Une note `upgrade/` documente le retrait de
  `request.metadata`.
- Chemin canonique en règle : `{"var": "metadata.ci.job.url"}`.

### 2. Helpers JSON Logic

Enregistrés dans `_add_custom_operations()` (`regis/rules/evaluator.py`), au
même titre que `intersects` / `env_contains`. Génériques (s'appliquent à
n'importe quel `var`), mais pensés pour les valeurs-chaînes du meta.

| Opérateur  | Arité          | Sémantique                                                                                                               |
| :--------- | :------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `is_true`  | `[x]`          | `True` si `x` ∈ {`true`,`1`,`yes`,`on`} (casse ignorée) ou booléen `True`. Sinon `False`.                                |
| `is_false` | `[x]`          | `True` si `x` ∈ {`false`,`0`,`no`,`off`} (casse ignorée) ou booléen `False`. Sinon `False`.                              |
| `is_url`   | `[x]`          | `True` si `x` est une URL `http`/`https` bien formée (`urllib.parse`, `scheme` ∈ {http,https} **et** `netloc` non vide). |
| `is_empty` | `[x]`          | `True` si `x` est `None`, `""`, ou chaîne de blancs.                                                                     |
| `is_set`   | `[x]`          | Complément de `is_empty` : `True` si `x` présent et non vide.                                                            |
| `matches`  | `[x, pattern]` | `re.search(pattern, x)` truthy. `x` non-string ou regex invalide → `False` (warning loggué).                             |

Règles transverses :

- `is_true` et `is_false` ne sont **pas** stricts complémentaires : une valeur
  parasite (`"maybe"`) n'est ni l'un ni l'autre. Intentionnel.
- Entrée non-string / `None` → `False` partout, sauf `is_empty` (→ `True` sur
  `None`/`""`) et `is_set` (→ `False`).
- Style défensif aligné sur les opérateurs existants (jamais d'exception qui
  remonte ; valeurs inattendues → résultat falsy).

### 3. Namespace `metadata.*` optionnel (fix `incomplete`)

- `MissingDataTracker` (`regis/playbook/context.py`) : un accès manquant ou
  `None` dont le **chemin complet** appartient au namespace `metadata` (égal à
  `metadata` ou commençant par `metadata.`) **n'arme plus** `missing_accessed`.
- La clé reste enregistrée dans `accessed_keys` (l'attribution d'analyzers et le
  reporting de couverture sont inchangés).
- Doit être épinglé par TDD pour les **deux** chemins de résolution employés par
  le moteur : clé aplatie (`metadata.ci.job.url` présente à plat dans le
  contexte aplati) **et** traversée imbriquée segment par segment.
- Sémantique : le meta est fourni par l'utilisateur ; son absence est un état
  testable (`is_set`/`is_empty`), pas un « analyzer absent ».

### 4. Schéma well-known corrigé

- `well-known.schema.json` réécrit en **structure imbriquée** :

  ```json
  {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://regis/schemas/meta/well-known.schema.json",
    "title": "Regis Well-Known Metadata",
    "description": "Standard metadata fields recognized by regis across all playbooks.",
    "type": "object",
    "properties": {
      "ci": {
        "type": "object",
        "properties": {
          "platform": {
            "type": "string",
            "enum": ["github", "gitlab"],
            "description": "CI platform running the analysis"
          },
          "job": {
            "type": "object",
            "properties": {
              "id": {
                "type": "string",
                "description": "Unique identifier of the CI job"
              },
              "url": {
                "type": "string",
                "format": "uri",
                "description": "URL to the CI job run"
              }
            },
            "additionalProperties": true
          }
        },
        "additionalProperties": true
      }
    },
    "additionalProperties": true
  }
  ```

- `metadata.py` : la construction de `metadata_validation` et le mapping
  d'erreurs jsonschema supposent aujourd'hui des **propriétés plates top-level**
  (itération sur `schema_properties`, `error.path[0]`). Retravaillé pour les
  chemins imbriqués : `metadata_validation` reste indexé par **clé pointée**
  (ex. `"ci.job.url"`) en aplatissant le chemin d'erreur jsonschema
  (`".".join(map(str, error.path))`), et la collecte des propriétés du schéma
  parcourt récursivement les `properties` imbriquées. Le contrat de sortie
  (`{field: {"valid": bool, "error"?: str}}`) est préservé.
- L'extension de bundle `meta.schema.json` (fusionnée en `allOf`) suit la même
  forme imbriquée ; la doc d'extension est mise à jour en conséquence.

### 5. Documentation

- `docs/website/docs/concepts/rules.md` : nouvelle section **« Référencer le
  meta dans les règles »** —
  - chemin canonique `metadata.*` ;
  - comportement namespace optionnel (absent → `null`, jamais `incomplete`) ;
  - table des champs well-known (`ci.platform`, `ci.job.id`, `ci.job.url`) ;
  - exemples concrets avec helpers, dont « `metadata.ci.job.url` doit être une
    URL valide lorsqu'il est fourni » et un drapeau `is_true`.
- Table des opérateurs personnalisés étendue avec les 6 nouvelles lignes.
- Référence schéma well-known régénérée (`reference/schemas/meta/...`).
- Aide `--meta` / `configuration.md` ajustées si nécessaire.
- Note `docs/website/docs/upgrade/` pour le retrait de `request.metadata` et le
  bump `REPORT_SCHEMA_VERSION 2 → 3`.

### 6. Tests (TDD)

- Unitaires par helper : `is_true`/`is_false` (toutes formes + parasites +
  non-string), `is_url` (http/https valides, schéma absent, netloc vide,
  non-string), `is_empty`/`is_set` (None/""/blancs/valeur), `matches` (match,
  non-match, regex invalide, non-string).
- Exemption tracker `metadata.*` : règle référençant un meta absent → `failed`
  ou `passed` selon la condition, **jamais** `incomplete` ; un accès `results.*`
  manquant reste `incomplete` (non-régression).
- Validation well-known imbriquée : `ci.platform` hors enum → erreur ;
  `ci.job.url` non-uri → erreur ; cas valides → `valid: true`. (Garde anti-
  régression : la version plate antérieure laissait tout passer.)
- Mapping d'erreurs `metadata.py` : `metadata_validation` indexé par clé pointée.
- End-to-end : `evaluate_rules` sur un rapport portant `metadata.*`, règles
  utilisant les helpers → statuts et messages attendus.
- Rupture report : `analyze` n'écrit plus `request.metadata` ; `metadata`
  top-level présent ; `schemaVersion == 3` ; fixture mise à jour.

## Hors périmètre

- `is_semver`, `to_number` (YAGNI).
- Migration outillée des rapports existants (sortie générée, pas de la config
  utilisateur ; les consommateurs aval s'adaptent via la version de schéma).
- Refonte du flux `--rerun metadata` au-delà du retrait de `request.metadata`.

## Risques / coordination

- **Rupture d'enveloppe report** : à séquencer avec la file « presentation
  generalization » pour éviter deux bumps non coordonnés vus des consommateurs
  aval.
- **Réécriture well-known + `metadata.py`** : le mapping d'erreurs est le point
  le plus délicat ; couverture TDD avant refactor.
- **Exemption tracker** : doit couvrir les deux chemins de résolution `var`,
  sinon `is_set`/`is_empty` restent piégés par `incomplete`.
