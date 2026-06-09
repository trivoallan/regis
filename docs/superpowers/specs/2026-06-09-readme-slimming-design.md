# Spec — README allégé (porte d'entrée minimale)

- **Date** : 2026-06-09
- **Statut** : approuvé (design)
- **Périmètre** : `README.md` à la racine du dépôt uniquement.

## Problème

Le `README.md` actuel fait 199 lignes. Il duplique du contenu maintenu dans le
site de documentation publié (<https://trivoallan.github.io/regis/>), contient une
note de breaking change **périmée** (elle pointe vers `regis-dashboard`, projet
abandonné au profit de regis-backstage), et embarque la documentation détaillée
d'une GitHub Action qui vit dans son **propre dépôt** (`trivoallan/regis-action`).
Le README doit redevenir une porte d'entrée concise qui oriente vers la doc
canonique, sans duplication ni information obsolète.

## Objectif

Réduire le README à ~50-60 lignes : présenter Regis en quelques secondes et
rediriger vers le site de doc. Source unique de vérité = site de doc ;
le README ne fait qu'orienter.

## Structure cible

1. `# Regis` + tagline blockquote + 2 badges (coverage, image size) — inchangé.
2. **Pitch** : le paragraphe d'introduction actuel (1 phrase).
3. **Image héro** : un seul screenshot `report-overview.png` sous le pitch, suivi
   du lien « Explore the interactive example report » (lien existant ligne 53).
4. **Key Features** : les 6 bullets actuels conservés (pitch produit).
5. **Documentation** : mini-index curé de liens pointés vers le site, plus le
   lien racine. Pages cibles (toutes existantes sous `docs/website/docs/`) :
   - Getting Started → `https://trivoallan.github.io/regis/docs/usage/getting-started`
   - Concepts → `https://trivoallan.github.io/regis/docs/concepts/introduction`
   - Usage guides → `https://trivoallan.github.io/regis/docs/usage/analyze-image`
   - CLI Reference → `https://trivoallan.github.io/regis/docs/reference/cli`
   - Lien racine → `https://trivoallan.github.io/regis/`
6. **GitHub Action** : 2 phrases + lien vers `trivoallan/regis-action` et la
   marketplace. Aucune table d'inputs/outputs, aucun exemple YAML, aucune note de
   migration (tout cela vit dans le dépôt de l'action et sa doc).
7. **License** : MIT — inchangé.

## Contenu supprimé et destination

| Section retirée du README                                            | Destination canonique         |
| -------------------------------------------------------------------- | ----------------------------- |
| Note « Breaking change in v0.33.0 » (regis-dashboard, **périmée**)   | CHANGELOG / pages `upgrade/`  |
| Table « Image variants »                                             | `docs/usage/tools-management` |
| Paragraphe « slim image lazy-loads… »                                | `docs/usage/tools-management` |
| Table « Built-in Analyzers »                                         | `docs/concepts/analyzers`     |
| 6 des 7 screenshots `<details>` (on garde la vue d'ensemble en héro) | exemple interactif + doc      |
| Section « CI/CD Security & Supply Chain Integrity »                  | doc (détail interne)          |
| Tables Inputs / Outputs de l'Action                                  | `trivoallan/regis-action`     |
| Exemples YAML (basic / PR comment / version pinning)                 | `trivoallan/regis-action`     |
| Note de migration `regis@vX` → `regis-action@v1`                     | `trivoallan/regis-action`     |

## Hors périmètre

- Aucune modification du site de doc, des badges, ou des assets `.github/assets/`.
- Pas de réécriture de contenu marketing au-delà du nécessaire (on réutilise le
  pitch et les bullets existants tels quels).

## Critères d'acceptation

- `README.md` ≤ ~60 lignes.
- Aucune mention de `regis-dashboard` ni de la breaking change v0.33.0.
- Les 5 liens de la section Documentation résolvent vers des pages existantes
  (vérification : les fichiers source correspondants existent sous
  `docs/website/docs/`).
- Un seul screenshot de rapport (vue d'ensemble) subsiste.
- La section GitHub Action tient en ≤ 3 lignes + liens, sans table ni YAML.
- Les badges coverage et image-size restent intacts (maintenus automatiquement).
