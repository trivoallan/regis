# Design — Extraction de la story GitLab vers `regis-gitlab`

- **Date** : 2026-06-05
- **Statut** : validé (brainstorming)
- **Thème** : sortir toute l'intégration GitLab du cœur `regis` vers un dépôt dédié
  `trivoallan/regis-gitlab`, à l'image de l'extraction `regis-action`. Suite logique du
  dégraissage pré-v1 et de la note « `regis gitlab` : extraire plus tard » du spec
  `2026-06-05-feature-pruning-design.md`.

## 1. Contexte et décisions de cadrage

Le cœur expose aujourd'hui une story GitLab complète :

- `regis gitlab create-request` (`regis/gitlab_cli.py`) — échographie triviale d'un JSON de
  requête (`image_url`, `playbook_url`, `requester_id`, `requester_login`).
- `regis gitlab update-mr` (`regis/gitlab_cli.py`) — via **`python-gitlab`** : poste un
  **commentaire** sur la MR (lien rapport), dérive des **labels** + **badge-labels colorés**
  depuis `report.json["playbook"]`, et injecte des **checklists** dans la **description** de la MR.
- `regis bootstrap gitlab-ci` (`regis/commands/bootstrap.py`) — scaffolder cookiecutter
  (`regis/cookiecutters/gitlab-ci/`) générant `.gitlab-ci.yml` + `playbook.yaml` +
  `CI-VARIABLES.md` (stages `request_analysis` / `analyze_image` / `push_results`).
- Tests : `tests/test_gitlab_cli.py`, `tests/test_bootstrap_gitlab_ci.py`.
- Docs : `usage/integrations/gitlab.md`, `reference/cli.md` (sections `gitlab` + `bootstrap`),
  item roadmap « Guide GitLab CI ».
- Dépendance : `python-gitlab>=4.4.0` (`pyproject.toml`), **utilisée uniquement** par
  `gitlab_cli.py` (vérifié).

### Décisions (issues du brainstorming)

1. **Posting MR → CI-native** (calque exact de `regis-action`, dont l'action poste le commentaire
   PR elle-même sans appeler `regis github`). `regis-gitlab` poste sur la MR via l'**API GitLab
   native** (`curl` + `jq`) dans le job CI. `regis gitlab` **n'est pas porté** ; il est **droppé**
   du cœur, **avec la dépendance `python-gitlab`** (gain de deps). `create-request` (echo JSON)
   devient du `jq`/`echo` inline.
2. **Hébergement → GitHub + template `include: remote`**. `regis-gitlab` reste dans l'org GitHub
   (cohérent avec `regis-action`/`regis-dashboard`/`regis-backstage`), consommé via
   `include: remote: <raw URL>@tag`. **Pas** de composant CI/CD GitLab.com / catalogue.
3. **Scaffolder non porté**. Pas de cookiecutter dans `regis-gitlab` : le dépôt fournit le
   template + un snippet `include:` documenté + un playbook d'exemple + la doc des variables CI.
   Le scaffolding de playbook reste couvert par `regis bootstrap playbook` (gardé dans le cœur).

### Garde-fou absolu

Le `.gitlab-ci.yml` **racine** du dépôt cœur est un **exemple client confidentiel** : ne jamais
le lire/stager/commiter/pousser, et **ne pas** le confondre avec le template extrait. Le template
de `regis-gitlab` **dérive du cookiecutter** `regis/cookiecutters/gitlab-ci/`, pas de ce fichier.

## 2. Architecture & séquencement

Deux phases, **extraire d'abord, retirer du cœur ensuite** (précédent `regis-action`) :

- **Phase 1** — créer/publier le dépôt `trivoallan/regis-gitlab` (template + docs + CI), tagué `v1`.
- **Phase 2** — retirer la story GitLab du cœur (breaking `feat(cli)!`, bump mineur pré-v1).
  Ne merge **qu'une fois `regis-gitlab` live**, pour que la doc cœur pointe vers un `@v1` réel.

Le template tourne l'image cœur `ghcr.io/trivoallan/regis:<tag>` ; la ref `@v1` du template et le
tag d'image restent **indépendants** (comme `regis-action`).

## 3. Phase 1 — contenu de `regis-gitlab`

### Arborescence cible

```text
regis-gitlab/
  templates/regis-mr.yml       # fragment de pipeline réutilisable (include: remote)
  examples/.gitlab-ci.yml      # consommateur minimal (le snippet include)
  examples/playbook.yaml       # playbook d'exemple
  README.md                    # usage + Guide GitLab CI + variables CI (absorbe CI-VARIABLES.md)
  .github/workflows/           # CI du dépôt (lint template, release-please, tag-major)
  release-please-config.json   # release-type: simple
  .release-please-manifest.json
```

### `templates/regis-mr.yml`

Adapté du cookiecutter `.gitlab-ci.yml`, **CI-native** :

- **Stage analyse** : `regis analyze "$IMAGE_URL" --html` (image `ghcr.io/trivoallan/regis:<tag>`),
  artefact `reports/`.
- **Stage post-to-MR** reproduisant fidèlement `update-mr` via `curl` + `jq` sur l'API GitLab
  (`${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}`) :
  1. **Commentaire** : `POST .../notes` avec le corps markdown (lien `report.html`).
  2. **Labels + badge-labels colorés** : extraits de `report.json` (`.playbook.labels`,
     `.playbook.badge_labels[]` avec mapping `class`→couleur `success/warning/error/information`),
     créés si besoin (`POST .../labels`) puis appliqués (`PUT .../merge_requests/:iid?add_labels=`).
  3. **Checklists** : `.playbook.mr_description_checklists` injectées dans la **description** de la
     MR (`PUT .../merge_requests/:iid` avec `description`).
- **`create-request`** : remplacé par un `jq -n`/`echo` inline produisant le JSON de requête.
- Variables CI requises (documentées) : `GITLAB_TOKEN` (PRIVATE-TOKEN, `pull-requests`-équivalent),
  `IMAGE_URL`, chemin/URL du playbook, tag d'image regis.

### Versioning & consommation

- Release-please `release-type: simple` + workflow `tag-major.yml` maintenant le tag flottant `v1`
  (calque `regis-action`).
- Consommation : `include: remote: https://raw.githubusercontent.com/trivoallan/regis-gitlab/v1/templates/regis-mr.yml`.

### CI du dépôt

- `yamllint` + validation de la structure du template.
- Note : un vrai run MR de bout en bout nécessite un projet GitLab (hors CI auto) → documenté,
  pas testé en CI. Lint + dry-run suffisent.

## 4. Phase 2 — retrait du cœur (breaking)

| Cible                                            | Action                                                                                               |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `regis/gitlab_cli.py`                            | **Supprimer**                                                                                        |
| `regis/cli.py`                                   | Retirer l'import `gitlab_cmd` + `main.add_command(gitlab_cmd, name="gitlab")`                        |
| `tests/test_gitlab_cli.py`                       | **Supprimer**                                                                                        |
| `regis/commands/bootstrap.py`                    | Retirer la commande `bootstrap_gitlab_ci` (décorateur + fonction)                                    |
| `regis/cookiecutters/gitlab-ci/`                 | **Supprimer l'arborescence**                                                                         |
| `tests/test_bootstrap_gitlab_ci.py`              | **Supprimer**                                                                                        |
| `pyproject.toml`                                 | **Retirer `python-gitlab>=4.4.0`** (+ régénérer `Pipfile.lock`) — unique consommateur                |
| `docs/website/docs/usage/integrations/gitlab.md` | Remplacer le contenu par un pointeur vers `regis-gitlab@v1` + note de migration (calque `github.md`) |
| `docs/website/docs/reference/cli.md`             | Retirer la section `### gitlab` + l'entrée `bootstrap gitlab-ci`                                     |
| `docs/website/docs/roadmap.md`                   | « Guide GitLab CI » / wizard `bootstrap gitlab-ci` → déplacé vers `regis-gitlab`                     |
| `docs/website/versioned_docs/**`                 | **Intacts** (snapshots figés)                                                                        |

Commit : `feat(cli)!: remove the GitLab integration (extracted to regis-gitlab)` → `bump-minor-pre-major` ⇒ **bump mineur**. Note de migration : `include: remote: …/regis-gitlab/v1/…`.

## 5. Réalité de création du dépôt

Vécu lors de `regis-action` : le dépôt peut être créé via l'API GitHub, mais le **scope MCP de
session** (`trivoallan/regis` seul) **bloque le push** vers le nouveau dépôt. Mitigation : stager
le contenu sous `regis-gitlab-staging/` sur la branche Phase 2, le **mainteneur pousse** le bundle,
coupe `v1.0.0` + tag flottant `v1`, pose la branch protection, puis retire le dossier de staging de
la branche PR. **Manuel restant** : secret PAT `RELEASE_PLEASE_TOKEN` (pour que les PR de release
déclenchent la CI).

## 6. Tests & vérification

### Phase 1 (`regis-gitlab`)

- `yamllint templates/regis-mr.yml` + validation structurelle.
- Revue manuelle du script `curl`/`jq` contre le comportement de l'actuel `update-mr` (commentaire +
  labels colorés + checklists) — parité fonctionnelle.

### Phase 2 (cœur)

- `pipenv run pytest` : suite verte après retrait (les tests gitlab/bootstrap-gitlab-ci partent avec
  leurs features) ; couverture **≥ 90 %**.
- `pipenv run regis --help` : plus de commande `gitlab`.
- `pipenv run regis bootstrap --help` : plus de sous-commande `gitlab-ci`.
- Résolution des dépendances **sans `python-gitlab`** (`pipenv install --dev` régénère le lock).
- `ruff check .` + `trunk check` verts ; build Docusaurus sans lien cassé.

## 7. Risques & mitigations

| Risque                                                                         | Mitigation                                                                                                      |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Toucher par erreur le `.gitlab-ci.yml` confidentiel racine                     | Garde-fou explicite (§1) ; le template dérive du cookiecutter ; ne jamais stager ce fichier                     |
| Parité imparfaite du posting CI-native vs `update-mr`                          | Reproduire les 3 comportements (commentaire, labels colorés, checklists) ; revue manuelle contre le code actuel |
| Retrait du cœur avant que `regis-gitlab` soit live (doc pointant dans le vide) | Séquencement strict : Phase 2 ne merge qu'après publication de `regis-gitlab@v1`                                |
| Push vers le nouveau dépôt bloqué par le scope MCP                             | Staging `regis-gitlab-staging/` + push mainteneur (précédent `regis-action`)                                    |
| Couverture < 90 % après retrait                                                | Le code retiré emporte ses tests ; vérifier le ratio avant PR                                                   |
| Conflits de rebase Phase 2 vs autres PR docs                                   | Brancher sur `main` à jour juste avant commit ; rebase-only                                                     |

## 8. Livrables

- **Contenu `regis-gitlab`** (template + examples + README + CI) — staging puis push mainteneur,
  `v1.0.0` + `v1` flottant.
- **1 PR cœur** (Phase 2, breaking `feat(cli)!`) — retrait code + cookiecutter + tests + dépendance
  `python-gitlab` + docs.
- Mise à jour Memory Bank (`activeContext.md` + `progress.md` + `decisionLog.md`) à la complétion.
