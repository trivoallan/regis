# Design — Adoption de la GitHub Merge Queue

- **Date** : 2026-06-10
- **Statut** : validé (brainstorming), en attente de relecture avant plan
- **Scope** : remplacer la machinerie CI maison (auto-rebase + ré-armement d'auto-merge) par la merge queue native de GitHub.

## Problème

`regis` maintient deux workflows faits main pour garder les PRs à jour et les merger :

- **`repo-autorebase.yml`** — à chaque push sur `main`, force-push/rebase de **toutes** les PRs ouvertes (le ruleset exige des branches à jour via _strict status checks_). Rebase aussi à l'ouverture/passage ready d'une PR.
- **`repo-automerge.yml`** — auto-merge natif GitHub enrobé d'une logique de ré-armement (disable → re-enable → fallback merge-direct) pour rattraper les races où une PR reste `MERGEABLE/CLEAN` sans merger.

Douleur observée et documentée :

- L'autorebase réécrit les SHAs distants des branches de PR → les pushes locaux sont **rejetés silencieusement** (`HEAD != origin/<branch>`).
- Chaque merge sur `main` déclenche une **cascade O(n²)** : toute la flotte est rebasée, re-run pytest+Trunk, puis ré-armée.
- Races de ré-armement : PRs coincées `CLEAN` sans merger.

Avec un débit réel de plusieurs PRs concurrentes (batches Dependabot, travail multi-branches), cette cascade et ces races sont structurelles, pas anecdotiques.

## Décision

Adopter la **merge queue native** de GitHub (repo public → disponible gratuitement) et **retirer** la machinerie maison. La fraîcheur des branches et la sérialisation des merges deviennent la responsabilité de la queue, plus celle de workflows custom.

### Choix actés pendant le brainstorming

- **Approche** : adoption complète, suppression de l'autorebase (pas de coexistence — autorebase et queue se disputent la gestion de fraîcheur).
- **PRs de release Please** : passent par la queue comme les autres (chemin de merge unique).
- **Auto-enqueue** : **full auto** — toute PR verte rejoint la file sans clic (auto-merge armé à l'ouverture).
- **Merge method** : `Squash` (cohérent avec l'historique linéaire déjà requis et avec Release Please).

## Modèle de flux

### Avant

```text
PR verte → auto-merge armé → push sur main (autre PR)
  → repo-autorebase force-push TOUTE la flotte
  → chaque PR re-run pytest+Trunk → repo-automerge ré-arme chacune
  → races : PR coincée CLEAN, push local rejeté
```

### Après

```text
PR ouverte → auto-merge armé (= rejoint la file dès que les checks passent)
  → GitHub crée une branche temporaire gh-readonly-queue/main/<sha>
    = main projeté + PR (+ PRs déjà en file devant)
  → pytest + Trunk Check tournent sur CETTE branche (événement merge_group)
  → verts → squash-merge sur main, dans l'ordre de la file
  → branches de PR JAMAIS touchées ; aucune cascade ; aucun ré-armement
```

Propriétés :

- **Fraîcheur** gérée par la branche temporaire → on retire _« require branches to be up to date »_ du ruleset.
- **Sérialisation** possédée par la queue → la logique disable/re-enable/merge-direct disparaît.
- **Historique linéaire** (déjà requis) satisfait par le squash.
- **Test spéculatif** : plusieurs PRs testées en parallèle (empilées) ; une PR qui casse est éjectée seule, les suivantes re-testées sans elle.

## Changements concrets

### a) Ruleset `main`

- ✅ Activer **Merge queue** : merge method `Squash`, build concurrency ~5, group size min/max à démarrer 1/5, timeout d'attente des checks.
- ✅ Required checks de la queue : `pytest`, `Trunk Check` (identiques à aujourd'hui).
- ❌ Retirer _« Require branches to be up to date before merging »_ (strict).
- ✅ Conserver : `required_linear_history`, le `pull_request` rule.
- À vérifier au moment du plan : la config ruleset est-elle gérée en IaC (Settings App `.github/settings.yml`) ou seulement via l'UI ? Appliquer au bon endroit.

### b) `ci-test.yml`

Ajout du seul trigger `merge_group:` (le job `pytest` fonctionne tel quel sur la branche de groupe) :

```yaml
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  merge_group: # nouveau
  workflow_dispatch:
```

### c) `ci-lint.yml`

Ajout du trigger `merge_group:` **et** adaptation du job `trunk` (`Trunk Check`).

Problème : sur une PR, le job fait _Trunk Format → commit & push des fixes → fail si fixes nécessaires_, avec `ref: ${{ github.head_ref }}`. Sur `merge_group`, `github.head_ref` est **vide** et la branche est éphémère (`gh-readonly-queue/...`) — auto-commiter dessus est absurde.

**Choix retenu (c1, diff minimal)** : garder un seul job, ajouter `if: github.event_name != 'merge_group'` sur les steps format/commit/push, ne lancer que le _check_ en `merge_group`. Vérifier que le `ref` du checkout se résout correctement hors PR (en `merge_group`, checkout par défaut de la branche de groupe, pas `head_ref`).

Les autres jobs de `ci-lint` (`docs-links`, `workflow-action-pinning`, `generated-artifacts-guard`, guard plans) ne sont **pas** des checks requis : ils tourneront en `merge_group` mais ne bloqueront pas la file. Acceptable (option future : les gater par `if` pour réduire le bruit).

### d) `repo-autorebase.yml`

**Supprimé** entièrement.

### e) `repo-automerge.yml`

**Réduit** (~15 lignes au lieu de 105) :

```text
on: pull_request_target [opened, ready_for_review]
→ enable auto-merge (SQUASH) sur la PR
```

Avec la queue active, « auto-merge armé » = _« rejoint la file dès que les checks requis passent »_. Suppression de : trigger `workflow_run`, boucle de candidats, fallback merge-direct, `concurrency` complexe, **et l'exclusion `autorelease: pending`** (les PRs de release passent par la file).

L'armement reste stable car l'autorebase ne produira plus de `synchronize` par force-push — c'était la cause de la danse de ré-armement.

### f) Inchangés

- `ci-image-size.yml`, `ci-security.yml`, `ci-tools-*.yml` : non requis, restent sur `pull_request`.
- `cd-docker.yml`, `cd-docs.yml`, `release-please.yml`, `release-snapshot.yml` : inchangés.
- `repo-dependabot-critical-vulns.yml` : inchangé fonctionnellement ; à relire pour confirmer qu'il n'entre pas en conflit avec l'enqueue (agit sur labels/priorité, ne devrait pas).

## Intégrations

### Release Please

- Le harvest `## Summary` et le label `whats-new` ne changent pas.
- Release Please **met à jour sa PR** quand des commits landent sur `main` (réécrit la branche de release) → re-déclenche simplement l'enqueue quand elle est verte. À valider en test.
- Tag/release toujours déclenché au merge de la PR de release (inchangé).

### Dependabot

- Support natif merge queue : Dependabot enqueue lui-même les PRs éligibles quand la queue est active. Doublé par l'auto-merge armé via `repo-automerge.yml`.

## Modes de défaillance & garde-fous

| Risque                        | Cause                                                  | Mitigation                                                                           |
| ----------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Groupe coincé indéfiniment    | un check requis ne se déclenche pas sur `merge_group`  | **Piège n°1** : vérifier qu'un `merge_group` réel produit `pytest` ET `Trunk Check`. |
| `Trunk Check` échoue en queue | format-and-push sur branche éphémère / `head_ref` vide | `if: github.event_name != 'merge_group'` sur format/commit/push (c1).                |
| Faux « tout vert »            | un check non requis échoue sans bloquer                | Comportement voulu (image-size/security indicatifs) — assumé, pas un bug.            |
| Release PR ne merge pas       | interaction Release Please ↔ queue                     | Testée en conditions réelles ; 1ère release post-migration = vrai test.              |
| PR éjectée silencieusement    | conflit sémantique détecté par la queue                | Bénéfice attendu ; documenter où voir les éjections (onglet merge queue).            |

## Rollback

Sûr et rapide : désactiver la merge queue dans le ruleset, puis `git revert` du PR de migration (restaure `repo-autorebase.yml` + l'ancien `repo-automerge.yml`). Aucune donnée perdue ; les branches de PR n'ont jamais été modifiées par la queue.

## Vérification (preuve avant de déclarer terminé)

1. PR de migration mergée → ouvrir une **PR jouet triviale**.
2. Armer l'auto-merge → confirmer l'**ajout à la file** (onglet merge queue).
3. Confirmer que le run `merge_group` produit **`pytest` + `Trunk Check`** verts.
4. Confirmer le **squash-merge** automatique, historique linéaire préservé.
5. Ouvrir **2 PRs jouets simultanées** → confirmer le test spéculatif et l'absence de force-push (`HEAD == origin/<branch>` reste vrai localement).
6. Première release Please post-migration → confirmer traversée de la file + tag.

## Séquencement (œuf-poule)

On ne peut pas activer la queue **avant** que les checks tournent sur `merge_group`, sinon le tout premier groupe se coince. Ordre :

1. Merger le PR de migration (triggers `merge_group` + adaptation `Trunk Check` + suppression autorebase + réduction automerge) — ce PR se merge encore **à l'ancienne**.
2. _Puis_ activer la merge queue + retirer le mode strict dans le ruleset.
3. Exécuter la checklist de vérification.

## Hors scope

- Gating par `if` des jobs `ci-lint` non requis sur `merge_group` (optimisation de bruit, future).
- Tuning fin du group size / concurrency au-delà des valeurs de démarrage.
