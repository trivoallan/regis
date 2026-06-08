# Spec — Alléger le dépôt `regis`

- **Date** : 2026-06-08
- **Statut** : validé (design approuvé), prêt pour planification
- **Scope** : infrastructure dépôt / CI docs. Aucun changement au code applicatif `regis/`.

## Problème

Le clone par défaut du dépôt pèse **326 MB** (taille du `.git` packé), ce qui rend
le clonage lourd. Diagnostic mesuré :

| Périmètre                                        | Poids objets (décompressé)         |
| ------------------------------------------------ | ---------------------------------- |
| `main` seul                                      | 138 MB                             |
| Toutes refs **sauf** `gh-pages`                  | 143 MB                             |
| `gh-pages`                                       | **~8,5 GB** ← tout le poids est là |
| `origin/docs/latest-generated` (branche générée) | 138 MB                             |

**Cause racine n°1 — historique `gh-pages`.** La branche `gh-pages` accumule
**284 commits de déploiement** (~8,5 GB d'objets, packés à ~290 MB). Un `git clone`
récupère toutes les branches, dont `gh-pages` → c'est l'essentiel du poids du clone.

**Cause racine n°2 — le robinet est ouvert.** `.github/workflows/cd-docs.yml` déploie
avec `peaceiris/actions-gh-pages` en **`keep_files: true` et sans `force_orphan`** :
chaque build **empile** un nouveau commit _et_ conserve tous les anciens fichiers.
La branche grossit sans borne (ex. 226 versions de `search-index.json` empilées).

**Cause racine n°2 bis — versions périmées.** L'arbre actuel de `gh-pages` (dernier
commit, hors historique) pèse déjà **826 MB / 20 236 fichiers** et contient **21 versions
de docs** (`v0.19.0` → `v0.33.0` + `next`). Or `release-snapshot.yml` élague déjà la
**source** à 3 versions (`while len(versions) > 3`). À cause de `keep_files: true`, les
18 anciennes versions ne sont jamais supprimées de `gh-pages`.

## Objectif

- Clone par défaut : **326 MB → ~35 MB (~90 %)**.
- Réduction **permanente** : aucune branche ne peut réaccumuler du build généré.
- `main` et toutes les branches de travail **intouchés** (pas de réécriture
  d'historique sur la ligne principale → aucun re-clone forcé, aucun rebase des PR
  ouvertes nécessaire). La seule réécriture concerne `gh-pages`, qui est jetable et
  régénérée par le CI.

## Décisions actées

1. **Réécriture d'historique** : acceptée, mais limitée à `gh-pages` (branche CI
   jetable). `main` n'est pas réécrit.
2. **Mécanisme de service Pages** : migration vers un déploiement **basé artefact**
   (`actions/upload-pages-artifact` + `actions/deploy-pages`), **suppression de la
   branche `gh-pages`**. C'est la prévention définitive : sans branche, rien ne peut
   regonfler le clone. Le site ne sert plus que les 3 versions courantes + `next`,
   ce qui est cohérent avec la politique d'élagage de la source.

## Conception

### WS1 — Refonte CI (prévention ; doit atterrir en premier)

Cible : `.github/workflows/cd-docs.yml`.

- Remplacer les **deux** étapes `peaceiris/actions-gh-pages` (`Deploy docs to GitHub
Pages` et `Deploy root redirect to GitHub Pages`) par un déploiement basé artefact :
  1. Assembler un dossier unique `_site/` :
     - `docs/website/build/` → `_site/docs/`
     - `.github/pages-root/*` → `_site/` (préserver `CNAME`/redirect racine si présents)
  2. `actions/upload-pages-artifact` avec `path: _site`.
  3. `actions/deploy-pages` (job ou étape avec l'environment `github-pages`).
- Permissions du job : ajouter `id-token: write` et conserver `pages: write` ;
  `deploy-pages` s'authentifie via OIDC → retirer l'usage du token applicatif
  (`personal_token`) pour le déploiement Pages.
- Conserver l'étape `peter-evans/create-pull-request` (branche `docs/latest-generated`)
  inchangée : elle synchronise les assets générés dans la source, ne touche pas Pages.
- Vérifier que `release-snapshot.yml` n'écrit **pas** sur `gh-pages` (il ne fait que
  versionner la source via `docusaurus docs:version`) → aucun changement attendu, à
  confirmer pendant l'implémentation.
- **Étape manuelle (utilisateur, hors git)** : GitHub → Settings → Pages → Source =
  _GitHub Actions_. À coordonner avant le premier déploiement artefact.

### WS2 — Nettoyage curatif (l'allègement effectif)

Pré-condition : WS1 mergé **et** site vérifié live depuis l'artefact.

- **Supprimer `gh-pages`** (origin + local) → ses ~8,5 GB d'objets deviennent
  inatteignables.
- Supprimer les branches mortes / générées, après confirmation au cas par cas pour les
  non-évidentes :
  - `origin/docs/latest-generated` (138 MB ; regénérée à chaque run du CI docs)
  - `caca`, `nodogfood` (branches d'expérimentation)
  - branches déjà mergées dans `main` : `origin/claude/pip-audit-error-resolution-*`,
    `origin/copilot/fix-failing-checks`
- Élaguer les branches locales `tritri/*` (39) mergées/abandonnées — **local only**,
  risque nul.
- **Nuance à documenter** : le clone _vécu par les utilisateurs_ maigrit **dès** la
  suppression de `gh-pages` (un client ne fetch pas une branche supprimée). Le **pack
  côté serveur** ne rétrécit qu'après le `gc` automatique de GitHub (quelques jours ;
  pas de `gc` manuel exposé). Optionnel : ouvrir un ticket GitHub Support pour forcer
  un repack si le délai pose problème.

### WS3 — Garde-fous (empêcher tout regonflement futur)

- `.gitignore` : verrouiller les sorties de build :
  `docs/website/build/`, `docs/website/.docusaurus/`, `_site/`.
- Garde CI dans `ci-lint.yml` (ou check dédié) : **échoue si un commit sur `main`
  ajoute** des fichiers aux signatures de généré : `**/search-index.json`,
  `docs/v[0-9]*/**`, sorties de build Docusaurus. Empêche tout re-commit d'artefacts.
- Documenter le modèle dans `docs/memory-bank/systemPatterns.md` : « Pages servi depuis
  un artefact GitHub Actions, pas de branche `gh-pages` ; le build n'est jamais
  committé ».

## Séquencement & sécurité

1. **Backup** : `git clone --mirror` de origin vers une archive locale, **avant** toute
   opération destructive (filet de sécurité, conserve les vieilles versions publiées).
2. **WS1** : PR → merge → réglage manuel Pages → vérifier le site live.
3. **WS3** : peut atterrir avec WS1 (même PR ou PR jumelle).
4. **WS2** : suppressions de branches → mesurer la taille de clone.

## Vérification

- **Après WS1** : le site charge à l'URL publiée ; le sélecteur de versions montre les
  3 versions + `next` ; le redirect racine fonctionne ; `gh-pages` n'est plus écrite par
  le CI.
- **Après WS2** : `git clone --no-local` du dépôt dans un dossier temporaire → mesurer
  la taille du `.git` (cible ~35 MB).

## Rollback

- **WS1** réversible : revert du workflow + rebascule de Pages Source sur « Deploy from
  a branch ».
- **WS2** récupérable depuis le mirror de backup (`git push` des refs supprimées).

## Risques

- Les URL des anciennes versions (`v0.19.0`…`v0.30.0`) cessent d'être servies — cohérent
  avec la politique 3-versions de la source, mais 404 si un lien externe pointe dessus.
  Mitigation : le mirror de backup les conserve ; republication possible si besoin.
- Le réglage GitHub Pages (Source → GitHub Actions) est manuel, hors git → à coordonner
  avec le merge de WS1.
- Le rétrécissement du pack côté serveur dépend du timing du `gc` GitHub (non instantané).

## Hors scope

- Réécriture de l'historique de `main` (gain marginal : 138 MB, presque tout légitime ;
  coût élevé : re-clone + rebase des PR). Explicitement écarté.
- Réduction du working tree local (`node_modules/`, `htmlcov/`, etc.) : déjà `.gitignore`,
  sans effet sur le clone.
