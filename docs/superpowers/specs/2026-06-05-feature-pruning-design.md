# Design — Dégraissage pré-v1 : suppression de features inutiles

- **Date** : 2026-06-05
- **Statut** : validé (brainstorming)
- **Thème** : poursuite de l'élan de dégraissage pré-v1 (dashboard extraite, action extraite,
  image Docker allégée). Retrait ciblé de trois features jugées sans valeur nette.

## 1. Contexte et cadrage

« Supprimer les features inutiles » n'est pas un projet unique mais un **parapluie** au-dessus
de plusieurs décisions de périmètre indépendantes. Un audit de la surface fonctionnelle (CLI,
analyzers, archive, skills) a produit la triage ci-dessous. Chaque candidate a reçu un verdict
explicite ; trois sont retenues pour suppression dans ce lot.

### Décision stratégique amont

`regis-dashboard` (la dashboard standalone extraite le 2026-06-01) est **destiné à être
abandonné** au profit du plugin **regis-backstage**. Conséquence directe : la feature **archive**
(`--archive` → `manifest.json`/`data.json`) perd son **unique consommateur**. Vérifié :
regis-backstage ne consomme **pas** le format archive — il lit le `report.json` (annotation
`regis.io/report-url`) et agrège lui-même côté backend (`CatalogAggregator`). L'archive bascule
donc de « garder » à « supprimer ».

À noter : le reste de la Phase 2 du découplage dashboard est **déjà fait** — `apps/dashboard`,
le builder `report/docusaurus.py` et la commande `serve` ont déjà quitté le cœur. Le seul vestige
cœur réellement couplé à la dashboard standalone est l'archive. Le rapport HTML self-contained
(`--html` → `report/html.py`) est **indépendant** de la dashboard et **conservé**.

### Triage complet (verdicts)

| Candidate | Réalité observée | Verdict |
| --- | --- | --- |
| `regis github update-pr` | Redondant avec `regis-action` (qui poste déjà le commentaire PR) ; escape-hatch manuel documenté | **Supprimer** |
| skill `/create-playbook` (`.claude/skills/`) | Skill orientée produit, documentée ; chevauche `regis bootstrap playbook` | **Supprimer** |
| archive (`--archive` + `regis/archive/store.py`) | Unique consommateur = `regis-dashboard`, destiné à l'abandon ; regis-backstage ne consomme pas le format | **Supprimer** |
| `regis gitlab` (`create-request`, `update-mr`) | Pas d'action extraite équivalente ; « Guide GitLab CI » au roadmap Sprint 1 | **Garder** (extraire plus tard) |
| `.github/skills/*` (gh-cli, conventional-commit, pytest-coverage) | Aides contributeur génériques | **Garder** |
| `regis check <url>` | Préflight d'accessibilité de manifest, peu coûteux | **Garder** |
| `--html` / `report/html.py` | Rapport self-contained, indépendant de la dashboard | **Garder** |
| `regis version`, `list`, `evaluate`, `doctor` | Fonctions distinctes et utiles | **Garder** |

### Périmètre retenu

- **Suppression A** : commande CLI `regis github` (cassant).
- **Suppression B** : skill Claude `/create-playbook` (non cassant).
- **Suppression C** : feature archive + purge de la doc dashboard-viewer périmée (cassant, doc-lourd).

Les trois suppressions sont **indépendantes** et livrées en **trois PR distinctes**, chacune
branchée sur le dernier `main`.

### Hors périmètre (notes de suivi)

- `regis gitlab` : extraction future (à l'image de l'action GitHub), à brainstormer séparément.
- L'**abandon effectif du dépôt `regis-dashboard`** (archivage GitHub, dépréciation de l'image
  GHCR, etc.) est une action côté autre dépôt — hors de ce lot cœur.
- La suppression B rend caduc le suivi tracké « la skill `/create-playbook` émet encore `rule:` »
  (issu du renommage rule → criterion du 2026-06-05).

## 2. Suppression A — commande `regis github`

### Justification

L'action GitHub a été extraite vers [`trivoallan/regis-action`](https://github.com/trivoallan/regis-action)
le 2026-06-04. L'action réutilisable poste déjà le commentaire de PR et applique les labels.
La commande CLI `regis github update-pr` est donc un doublon dont la maintenance n'apporte plus
de valeur nette ; tout besoin avancé est couvert par l'action.

### Touchpoints exacts

| Fichier | Action |
| --- | --- |
| `regis/github_cli.py` (217 l.) | **Supprimer le fichier** |
| `regis/cli.py` | Retirer l'import `from regis.github_cli import github_cmd` (l. 17) et `main.add_command(github_cmd, name="github")` (l. 79) |
| `tests/test_github_cli.py` | **Supprimer le fichier** |
| `docs/website/docs/usage/integrations/github.md` | Retirer la section « Posting Results to Pull Requests » (l. 279–319) ; repointer le lecteur vers `regis-action@v1` |
| `docs/website/docs/roadmap.md` (l. 47) | Retirer ou mettre à jour la ligne d'historique de la feature |
| `docs/website/versioned_docs/**` | **Intacts** (snapshots figés, convention projet) |

### Vérifications préalables (faites)

- Aucun appelant interne (CI / scripts) : `grep` sur `.github/workflows/` et `scripts/` → vide.
- `ci-action-dogfood.yml` déjà supprimé lors de l'extraction de l'action.

### Versioning & commit

- Suppression d'une commande user-facing = **breaking change**.
- Commit `feat(cli)!: remove the regis github PR-integration command` → `bump-minor-pre-major`
  ⇒ **bump mineur** (pré-v1).
- Corps de commit : note de migration « utiliser `trivoallan/regis-action@v1` ».

## 3. Suppression B — skill `/create-playbook`

### Justification

L'utilisateur a décidé de retirer cette skill orientée produit. Le chemin de remplacement
existe déjà : `regis bootstrap playbook` (squelette) + documentation de la structure de playbook.
Retirer la skill réduit le couplage du dépôt à un outil propriétaire pour cette fonction précise.
Les skills contributeur génériques (`.github/skills/*`) sont **conservées**.

### Touchpoints exacts

| Fichier | Action |
| --- | --- |
| `.claude/skills/create-playbook/` (SKILL.md + `references/available-rules.md` + `references/playbook-examples.md`) | **Supprimer l'arborescence** |
| `docs/website/docs/usage/custom-playbook.md` | Retirer la section « Create a playbook with the AI assistant » (l. 14–84) ; promouvoir « Bootstrap a skeleton manually » (`regis bootstrap playbook`) comme chemin principal |
| `CLAUDE.md` (l. 64) | Retirer `/create-playbook` de la liste des « project skills » (sinon contradiction) |
| `docs/website/versioned_docs/**`, `docs/memory-bank/**` | **Intacts** (snapshots / historique) |

### Versioning & commit

- Pas un artefact packagé (absent de `pyproject.toml` / `MANIFEST.in`) → **pas de bump**.
- Commit `chore(skills): remove the create-playbook Claude skill` (partie doc éventuellement
  séparée en `docs(playbook):` selon la granularité souhaitée).
- Pas de breaking change CLI.

## 4. Suppression C — feature archive (+ purge doc dashboard-viewer)

### Justification

L'archive (`--archive` sur `analyze` → `manifest.json`/`data.json`) n'a qu'un consommateur :
`regis-dashboard`, destiné à l'abandon (cf. §1). regis-backstage ne consomme pas ce format.
Sans viewer pour l'exploiter, l'archive est du poids mort. On en profite pour purger la doc
dashboard-viewer désormais périmée (déjà réduite à des stubs de redirection vers le dépôt
abandonné).

### Touchpoints exacts — code

| Fichier | Action |
| --- | --- |
| `regis/archive/` (`store.py` + `__init__.py`) | **Supprimer le package** |
| `regis/commands/analyze.py` | Retirer l'option `--archive` (l. 260–265), le param `archive_dir` (310), la validation d'exclusion mutuelle avec `--html` (430–431) et les branches `add_to_archive` (434, 642–645, 657–663) + commentaire (662). **Uniquement `analyze`** (pas `evaluate`) |
| `regis/schemas/archives.schema.json` (955 B) | **Supprimer** (schéma orphelin — zéro référence vérifiée) |

### Touchpoints exacts — tests

| Fichier | Action |
| --- | --- |
| `tests/test_archive_store.py` | **Supprimer le fichier** |
| `tests/commands/test_analyze_html.py` | Élaguer les cas testant `--archive` / l'exclusion mutuelle ; conserver les cas `--html` |
| `tests/test_bootstrap.py` | Vérifier/retirer toute référence archive résiduelle (probable faux positif — pas de sous-commande `bootstrap archive`) |

### Touchpoints exacts — doc

| Cible | Action |
| --- | --- |
| `concepts/archives.md`, `usage/multi-archive.md`, `integrations/archive-repo.md`, `integrations/archive-customize.md` | **Supprimer** (pages 100 % archive) |
| `usage/report-viewer.md`, `tools/viewer.mdx` | **Supprimer** (stubs de redirection vers le dépôt dashboard abandonné) |
| `getting-started.md`, `analyze-image.md`, `concepts/reports.md`, `concepts/introduction.md`, `usage/troubleshooting.md`, `integrations/github.md`, `integrations/gitlab.md`, `reference/cli.md`, `roadmap.md`, `tags.yml` | Élaguer les mentions archive / dashboard-viewer. **Préserver impérativement le contenu `--html`** (rapport self-contained, conservé) |
| Sidebar Docusaurus (`sidebars.*`) | Retirer les entrées des pages supprimées |
| `docs/website/versioned_docs/**` | **Intacts** (snapshots figés) |

> Note éditoriale (à trancher au plan) : remplacer le récit « viewer » par un pointeur bref vers
> `--html` (rapport rapide) et/ou le plugin Backstage, pour ne pas laisser de trou.

### Versioning & commit

- Suppression d'un flag user-facing (`--archive`) = **breaking change**.
- Commit `feat(cli)!: remove the report archive feature` → **bump mineur** (pré-v1).
- Doc éventuellement scindée en `docs(archive): ...` selon la granularité souhaitée.

## 5. Tests & vérification

### Suppression A

- Retirer `tests/test_github_cli.py` ; `pipenv run pytest --no-cov` passe ;
  `pipenv run regis --help` n'expose plus `github` ; couverture **≥ 90 %** ; `trunk check` vert.

### Suppression B

- Aucune incidence sur la suite (skill non couverte par pytest) ; aucun lien doc cassé vers la
  section retirée de `custom-playbook.md`.

### Suppression C

- Retirer `tests/test_archive_store.py` + élaguer `test_analyze_html.py` ;
  `pipenv run pytest --no-cov` passe ; `pipenv run regis analyze --help` n'expose plus `--archive` ;
  couverture **≥ 90 %** maintenue ; `trunk check` vert.
- Build de la doc Docusaurus (`docs/website`) sans lien cassé : grep des ancres internes
  référençant les pages supprimées, vérification de la sidebar.

## 6. Risques & mitigations

| Risque | Mitigation |
| --- | --- |
| Un utilisateur dépendait de `regis github update-pr` | Note de migration explicite vers `regis-action@v1` (commit + github.md) |
| Un utilisateur dépendait de `--archive` | Note de migration dans le commit ; orienter vers `--html` (rapport ponctuel) ou le plugin Backstage |
| Abandon dashboard non encore acté côté dépôt | La suppression cœur est découplée du calendrier d'archivage de `regis-dashboard` ; décision validée par l'utilisateur |
| Chute de couverture sous 90 % | Le code retiré emporte ses tests ; impact net neutre/positif — vérifier le ratio avant PR |
| Liens doc cassés (pages supprimées, sidebar) | Grep des ancres + build doc avant PR ; suppression coordonnée des entrées sidebar |
| Suppression accidentelle de doc `--html` en élaguant les mentions archive | Instruction explicite : préserver tout contenu `--html` (feature conservée) |
| Contradiction `CLAUDE.md` ↔ skills réellement présentes | Mise à jour de la ligne 64 (suppression B) |

## 7. Livraison

- **PR1** — Suppression A (`feat(cli)!`, bump mineur). Branche sur `main` à jour.
- **PR2** — Suppression B (`chore(skills)` / `docs`, pas de bump). Branche sur `main` à jour.
- **PR3** — Suppression C (`feat(cli)!`, bump mineur ; doc-lourd). Branche sur `main` à jour.
- Rebase-only (jamais de merge de `main` dans les branches).
- Mise à jour du Memory Bank (`activeContext.md` + `progress.md`) à la complétion.
