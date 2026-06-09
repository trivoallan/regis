# Spec — Refonte UI du rapport HTML standalone

- **Date** : 2026-06-09
- **Scope commit** : `feat(templates)` (non cassant)
- **Statut** : design validé, en attente de revue spec

## Contexte

`regis analyze --html` / `regis evaluate --html` génèrent un `report.html`
**self-contained** (un seul fichier, HTML + CSS inline, **zéro JS, zéro
dépendance externe**, fonctionne en `file://` / offline). Renderer actuel :
[`regis/report/html.py`](../../../regis/report/html.py) +
[`regis/templates/html/report.html.j2`](../../../regis/templates/html/report.html.j2).

Le rendu actuel est fonctionnel mais plat : header + verdict + table playbook +
sections analyzer empilées au même niveau visuel, sans navigation ni
priorisation. Quatre axes d'amélioration retenus : **lisibilité/hiérarchie**,
**navigation/volume**, **branding/esthétique**, **densité/priorisation**.

## Contrainte structurante

**CSS pur, zéro JavaScript.** On reste mono-fichier self-contained. On s'appuie
uniquement sur les primitives HTML/CSS natives : `<details>`/`<summary>`
(repli), `position: sticky` (sommaire collant), `:target` (surlignage section
active), CSS Grid (layout), `@media` (responsive). Cette contrainte garantit la
robustesse partout (email, `file://`, CSP stricte, export PDF) et préserve le
contrat « un fichier, aucune ressource externe ».

Conséquence assumée : **pas de filtrage/recherche dynamique** ni de scroll-spy
(impossibles sans JS).

## Décisions de design

| Axe                  | Décision                                                                                                                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Layout**           | Dashboard à 2 colonnes : sommaire latéral collant (gauche) + contenu (droite), avec **panneau triage** en tête du contenu (fusion des directions « dashboard » A et « triage-first » C). |
| **Esthétique**       | Skin **Carbon** : quasi-monochrome (zinc/gris), couleur réservée au sémantique. Typo système + **monospace** pour les refs techniques.                                                   |
| **Thème**            | **Clair uniquement** (pas de dark mode pour cette itération ; `prefers-color-scheme` reste une évolution future possible).                                                               |
| **Impression**       | **Écran d'abord** : pas de feuille `@media print` dédiée. L'impression reste lisible mais non optimisée.                                                                                 |
| **Repli par défaut** | Panneau triage + analyzers **en échec** dépliés (`<details open>`) ; analyzers **OK** repliés.                                                                                           |
| **Responsive**       | Sous ~720px : layout 1 colonne, sommaire latéral → **barre de pilules collante** horizontale en haut (défilable) ; severity strip 4 → **2×2** ; header empilé.                           |

## Architecture

Changement **localisé** au renderer mono-fichier. Aucune modification de la CLI,
de la signature `render_html_single(report, sections)`, ni du format interne
`"html"`. `--sections all|summary|<slugs>` et le filtre par slugs restent
supportés à l'identique.

### Fichiers touchés

1. **[`regis/templates/html/report.html.j2`](../../../regis/templates/html/report.html.j2)**
   — réécriture complète du markup et du CSS inline (skin Carbon, grille
   sidebar/main, sommaire, panneau triage, severity strip, sections `<details>`,
   `@media` responsive). Conserve les macros de rendu de valeurs existantes
   (`render_scalar`, `render_list_of_dicts`, `render_detail`) qui restent
   correctes pour le corps des analyzers.

2. **[`regis/report/html.py`](../../../regis/report/html.py)** — extension du
   **view-model** passé au template (calculs que Jinja ne dérive pas
   simplement). La fonction `render_html_single` garde sa signature ; on enrichit
   le dict de contexte `template.render(...)`.

### View-model — données ajoutées

| Clé                                               | Source                                                                                         | Usage template                                                |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `toc` : liste de `{slug, label, status}`          | `report.results` keys + set d'échecs                                                           | sommaire latéral + barre de pilules ; pastille `✓`/`✗`        |
| `failing_analyzers` : `set[str]`                  | analyzers des `rules[]` avec `passed: false` (champ `rules[].analyzers`)                       | choix `<details open>` vs replié par section                  |
| `severity` : liste ordonnée `{label, count, css}` | `results.cve.{critical,high,medium,low,negligible,unknown}_count`                              | severity strip ; **omise** si pas d'analyzer `cve`            |
| `triage`                                          | `verdict.failures` + `verdict.incompletes` (déjà calculés dans le view-model verdict existant) | panneau triage ; si vide → état positif « All checks passed » |

**Périmètre du triage (v1)** : règles **en échec** + **incomplètes**
uniquement. On ne descend **pas** dans les CVE individuelles (shape variable,
`results.cve.targets` parfois volumineux) — listé en évolution future.

### Layout (CSS Grid)

```text
┌──────────┬────────────────────────────────────┐
│ SIDEBAR  │  HEADER   image identity + meta      │
│ (sticky) │  ──────────────────────────────────  │
│ regis    │  VERDICT HERO   score ring + tier    │
│          │  ──────────────────────────────────  │
│ ▸ Verdict│  TRIAGE PANEL   ⚠ échecs/incomplets   │  ← open
│ · Triage │  ──────────────────────────────────  │
│ · cve  ✗ │  SEVERITY STRIP crit/high/med/low     │  ← si cve
│ · oci  ✓ │  ──────────────────────────────────  │
│          │  <details open>  cve  (échec)         │
│ footer   │  <details>       oci  (ok, replié)    │
└──────────┴────────────────────────────────────┘
```

- Sidebar `position: sticky; top: 0`. Liens = ancres `#<slug>`. Surlignage
  section active via `:target` (au clic ; pas de scroll-spy).
- Sous le breakpoint : la grille passe en une colonne, la sidebar devient une
  barre de pilules sticky en haut.

### Skin Carbon — jetons

- Neutres : palette zinc/gris (`#fafafa` fonds, `#18181b` texte, `#e4e4e7`
  bordures).
- Sémantique uniquement : rouge (critical / fail), orange (high / warn), ambre
  (medium), vert (low / pass).
- Monospace (`ui-monospace, Menlo, monospace`) pour : digest, tag, versions
  scanner, IDs CVE.
- Score ring : bordure neutre, libellé de tier coloré.

## Comportement des modes (inchangé fonctionnellement)

- `--sections all` (défaut) : header + verdict + triage + severity + **toutes**
  les sections analyzer (échecs dépliés, OK repliés).
- `--sections summary` : header + verdict + triage + severity + sommaire,
  **sans** le détail des analyzers.
- `--sections <slugs>` : header + verdict + triage + severity + **seulement** ces
  sections (dépliées). Slugs inconnus → warning sur stderr (comportement
  existant conservé).

## Tests

- **Existants** (`tests/.../test_html*.py`, 23 tests) : adapter les assertions
  structurelles aux nouveaux ids/classes en préservant la couverture
  (global ≥ 90 % et par-fichier ≥ 90 % sur `regis/report/html.py`).
- **Nouveaux** :
  - sommaire présent avec une entrée par analyzer + pastille `✓`/`✗` correcte ;
  - `<details open>` sur un analyzer en échec, replié sur un analyzer OK ;
  - severity strip présente quand `cve` est dans les résultats, absente sinon ;
  - panneau triage liste les échecs/incomplets ; état « All checks passed »
    quand zéro échec ;
  - aucun `<script>` ni URL externe (`http`/`//`) dans la sortie — garde la
    contrainte self-contained / zéro-JS.

## Hors périmètre (évolutions futures notées)

- Dark mode (`prefers-color-scheme`).
- Feuille `@media print` dédiée (dépliage des `<details>` à l'impression, sauts
  de page).
- Triage descendant dans les CVE individuelles (high/critical par ID).
- Filtrage / recherche dynamique (nécessiterait du JS).
- Scroll-spy du sommaire (nécessiterait du JS).
