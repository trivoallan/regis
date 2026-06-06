# Design — Généralisation de la couche « integrations » du playbook → `spec.presentation`

- **Date** : 2026-06-06
- **Statut** : validé (brainstorming)
- **Sous-projet** : #1 (cœur) d'un effort multi-dépôts. Découple le moteur de playbook des
  spécificités plateforme, le rend extensible, et déplace le _rendu_ plateforme vers les dépôts
  d'intégration.

## 1. Contexte et cadrage

Aujourd'hui le cœur connaît GitLab en dur :

- **Schéma playbook** : `spec.integrations.gitlab.{badges, checklist, checklists, templates}`
  (`regis/schemas/playbook/v1alpha1/playbook.schema.json`).
- **Évaluateur** : `regis/playbook/evaluator.py` importe et appelle en dur
  `resolve_gitlab_integration(...)` (`regis/playbook/integrations/gitlab.py`).
- **Sortie `report.json`** : `badge_labels`, `mr_description_checklists`, `mr_templates` (le préfixe
  `mr_` = Merge Request = GitLab).

Or **la logique de résolution est déjà générique** (évaluer `show_if`/`check_if` contre le contexte,
résoudre des badges en labels). Seuls le **nommage** (`integrations.gitlab`, `mr_*`) et l'**import en
dur** sont spécifiques plateforme. La **résolution doit rester dans le cœur** (elle a besoin du moteur
d'évaluation + du contexte d'analyse) ; le **rendu** plateforme (resolved data → labels MR/PR,
annotations) appartient déjà aux intégrations externes (regis-gitlab template, regis-action,
regis-backstage), qui sont **non-Python** et ne peuvent pas exécuter de résolveur du cœur.

### Décisions (brainstorming)

1. **Généraliser** (vs registry de plugins / hybride) : le cœur expose des directives playbook
   **neutres**, résolues en champs `report.json` **neutres** ; chaque intégration lit ces champs et
   rend à sa plateforme. Le cœur ne connaît plus aucune plateforme.
2. **Nom de section : `spec.presentation`** (« comment les findings sont présentés aux
   consommateurs » : labels, checklists, templates).
3. **Transition : hard-cut coordonné** — le cœur **renomme** les champs (pas de dual-emit) et
   **bumpe `REPORT_SCHEMA_VERSION` (1 → 2)**. Les consommateurs (#2/#3/#4) migrent en lockstep.
   La dégradation downstream est **gracieuse** : regis-backstage gate sur `schemaVersion` (UI d'erreur
   hors plage, pas de crash) et le template regis-gitlab utilise `// []` en jq (labels/checklists
   vides plutôt que crash) tant qu'il n'est pas mis à jour.

### Décomposition de l'effort (rappel)

| #     | Sous-projet                                                   | Statut                 |
| ----- | ------------------------------------------------------------- | ---------------------- |
| **1** | **Cœur — généralisation** (ce spec)                           | en cours               |
| 2     | regis-gitlab (template lit les champs neutres)                | cycle propre, après #1 |
| 3     | regis-backstage (`regis-common` types/schema + rendu)         | cycle propre, après #1 |
| 4     | regis-action (consomme les champs neutres → parité PR GitHub) | cycle propre, après #1 |

**Ce spec ne couvre que #1 (cœur).** Les #2/#3/#4 auront leur propre spec→plan.

## 2. Changements — schéma playbook (entrée, cassant)

Dans `regis/schemas/playbook/v1alpha1/playbook.schema.json` :

- Remplacer `spec.integrations` par **`spec.presentation`** (object), portant les **mêmes 3
  directives**, plateforme-neutres :
  - `badges` : liste de slugs de badges à exposer comme labels (ex-`integrations.gitlab.badges`).
  - `checklists` : checklists conditionnelles (ex-`integrations.gitlab.checklists`) ; items via le
    `$def` `checklist_item` existant (`label`, `show_if`, `check_if`).
  - `templates` : templates cookiecutter conditionnels (ex-`integrations.gitlab.templates`).
- **Drop** le `checklist` singulier déprécié (la migration le replie dans `checklists`).
- Mettre à jour la `description` de la section (retirer « GitLab/GitHub »).

`apiVersion` reste `regis.trivoallan.dev/v1alpha1` (le schéma est explicitement pré-v1/évolutif).

## 3. Changements — évaluateur + résolveur (cœur)

- **Renommer** `regis/playbook/integrations/gitlab.py` → `regis/playbook/presentation.py` ; renommer
  `resolve_gitlab_integration` → **`resolve_presentation`**. Les helpers (`_resolve_badge_labels`,
  `_resolve_checklists`, `_resolve_templates`) sont déjà génériques. **Précision loader** : le loader
  valide l'enveloppe k8s (section sous `spec.presentation` dans le schéma) puis **normalise vers un
  dict aplati** (cf. décision 2026-06-01) ; le résolveur lit donc la forme **aplatie**
  `playbook.get("presentation", {})` (comme l'actuel `playbook["integrations"]["gitlab"]` lit déjà
  la forme aplatie, pas `spec.*`).
- **Supprimer** le package `regis/playbook/integrations/` (vide après le renommage).
- `regis/playbook/evaluator.py` : remplacer l'import + l'appel `resolve_gitlab_integration(...)`
  (l. 17, 296) par `resolve_presentation(...)`. Mettre à jour le docstring (« GitLab integration
  directives » → « presentation directives »).

## 4. Changements — sortie `report.json` (contrat, cassant + bump version)

- Renommer dans le résultat produit + `regis/schemas/playbook/result.schema.json` :
  - `mr_description_checklists` → **`checklists`**
  - `mr_templates` → **`templates`**
  - `badge_labels` → **conservé** (déjà neutre).
- `regis/utils/report.py` : **`REPORT_SCHEMA_VERSION` 1 → 2**.
- Mettre à jour `regis/schemas/report/report.schema.json` / `result.schema.json` en conséquence (les
  champs neutres + la version).

## 5. Migration + dogfood

- **`regis playbook upgrade`** : déplacer `spec.integrations.gitlab.{badges,checklist,checklists,templates}`
  → `spec.presentation.{badges,checklists,templates}` (replier `checklist`→`checklists`), idempotent.
  Drop `spec.integrations` une fois vide.
- **Playbook par défaut** (`regis/playbooks/default/…`) migré (dogfood) → plus de section
  `integrations`.
- Cookiecutters playbook (`regis/cookiecutters/playbook/`) mis à jour vers `presentation`.

## 6. Documentation cœur

- `concepts/playbooks.md` (section MR-description-checklists / integrations) recadrée sur
  `spec.presentation`, neutre, sans framing GitLab.
- `reference/` schémas régénérés (`playbook.schema.md`, `result.schema.md`).
- `roadmap.md` : ligne « Stable API surface » (l. 25) — retirer `mr_description_checklists`,
  mentionner `presentation` / `checklists` ; noter le bump `schemaVersion`.
- `versioned_docs/**` : intacts.

## 7. Tests

- Renommer/adapter `tests/test_playbook_engine.py` (`TestGitLabChecklist` / `TestGitLabTemplates`
  → `TestPresentationChecklists` / `TestPresentationTemplates`) : testent le résolveur générique,
  lisant `spec.presentation`, attendant `checklists`/`templates`/`badge_labels`.
- Tests de `regis playbook upgrade` : `integrations.gitlab` → `presentation` (+ repli `checklist`).
- Tests de l'évaluateur / loader inchangés sauf chemin de section.
- `pipenv run pytest` vert, couverture **≥ 90 %**. `ruff` + `trunk` verts. Build doc sans lien cassé.

## 8. Hors périmètre (sous-projets suivants)

- **#2 regis-gitlab** : le template `regis-mr.yml` lit `.playbook.checklists` / `.playbook.templates`
  (ex-`mr_description_checklists`/`mr_templates`) ; nouvelle release `v2` ; gate sur le nouveau
  `schemaVersion`.
- **#3 regis-backstage** : `regis-common` types + `report.schema.json` alignés ; rendu sur les champs
  neutres ; élargir la plage `checkSchemaCompat` (`{min,max}`) pour accepter `schemaVersion: 2`.
- **#4 regis-action** : consommer `.playbook.badge_labels` / `.playbook.checklists` → parité PR GitHub
  (labels + checklist dans la description de PR).

## 9. Séquencement & risques

| Risque                                                      | Mitigation                                                                                                                                   |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Hard-cut casse les consommateurs avant #2/#3/#4             | Dégradation gracieuse (gate `schemaVersion` côté backstage, `// []` côté template) ; merger #1 puis enchaîner #2/#3/#4 rapidement            |
| Dépendance à `regis-gitlab.py` (renommé) vs PR #652 ouverte | Brancher l'implémentation sur `main` **après merge de #652** (qui conserve `gitlab.py`) ; sinon conflit de renommage                         |
| Champ « stable » documenté (`mr_description_checklists`)    | Le schéma playbook est `v1alpha1` (évolutif, pré-v1) ; migration fournie ; roadmap mise à jour                                               |
| Playbooks tiers utilisant `integrations.gitlab`             | `regis playbook upgrade` les migre ; warning de dépréciation possible si on veut un dual-read transitoire (optionnel, non retenu — hard-cut) |

## 10. Livrable

- **1 PR cœur** (breaking : `feat(playbook)!` — schéma playbook + contrat report + bump
  `REPORT_SCHEMA_VERSION`). Branchée sur `main` après #652.
- Mise à jour Memory Bank (`activeContext.md` + `progress.md` + `decisionLog.md`) à la complétion.
