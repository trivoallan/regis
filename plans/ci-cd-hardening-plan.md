# Plan de durcissement CI/CD — Workflows GitHub Actions

## Objectifs

- Éliminer les failles courantes dans les workflows CI/CD
- Appliquer le SHA pinning sur toutes les actions
- Réduire les permissions au strict minimum (least privilege)
- Ajouter des guardrails et des validations statiques
- Documenter le processus et les points de contrôle

## Étapes principales

### 1. Audit initial

- Lister tous les workflows et templates concernés
- Identifier les actions non pinnées (`ref: v3`, `v4`, `main`, etc.)
- Repérer les permissions globales (`write`/`all`) et les usages inutiles

### 2. SHA pinning systématique

- Remplacer toutes les références d’actions par des SHA exacts
- Ajouter un job de validation statique (`grep`/`actionlint`) pour empêcher les refs mutables

### 3. Permissions minimales

- Déplacer les permissions au niveau job (jamais global sauf nécessité)
- Limiter à `read-only` par défaut, n’ouvrir que ce qui est strictement requis (ex : `contents: write` pour release)
- Vérifier l’absence de `write`/`all` global

### 4. Guardrails et validation

- Ajouter un job de contrôle statique (grep sur permissions, action refs)
- Documenter les patterns recherchés et les exclusions
- Prévoir une vérification manuelle à chaque PR majeure

### 5. Documentation et transmission

- Rédiger ce plan dans `plans/ci-cd-hardening-plan.md`
- Lister les fichiers modifiés et les patterns appliqués
- Préparer un message de commit/PR expliquant la démarche

## Points de contrôle (Checklist)

- [x] Toutes les actions sont pinnées par SHA
- [x] Aucune permission globale `write`/`all` sauf nécessité documentée
- [x] Permissions minimales au niveau job
- [x] Guardrails statiques présents (`grep`/`actionlint`)
- [x] Documentation du plan et des patterns

## Validation

- Ouvrir une PR et vérifier le passage de tous les jobs
- Contrôler les logs de validation statique
- En cas d’échec, corriger et revalider

## Scénarios de test

- Ajout d’une action non pinnée → la CI doit échouer
- Ajout d’une permission `write` globale → la CI doit échouer
- Ajout d’un nouveau workflow → doit respecter les patterns

## Fichiers concernés

- `.github/workflows/*.yml`
- `regis/cookiecutters/archive/{{cookiecutter.project_slug}}/.github/workflows/*.yml`
- `plans/ci-cd-hardening-plan.md`

## Historique et leçons

- Problème rencontré : corruption de fichiers par outil d’édition
- Solution : restauration depuis main, puis durcissement progressif
- Importance de la validation statique et de la documentation
