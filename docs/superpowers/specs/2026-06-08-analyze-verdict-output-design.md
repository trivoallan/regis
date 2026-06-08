# Spec — Verdict de sortie de `regis analyze` (tier, score, badges)

- **Date** : 2026-06-08
- **Statut** : approuvée (brainstorming)
- **Scope** : rendu du verdict d'évaluation playbook dans les trois surfaces humaines (terminal, HTML, markdown). Pas de refonte du calcul de score.

## Problème

Aujourd'hui, `regis analyze` ne montre le résultat de l'évaluation playbook que de façon partielle :

- Le **terminal** n'affiche un résumé que si `--playbook` est passé explicitement (`_print_playbook_summary`), et `tier`/`badges` ne sont hoistés au top-level du report que sous `--evaluate`. Un simple `regis analyze <url>` n'affiche **aucun** verdict — alors que le tier, le score et les badges existent déjà dans `final_report["playbooks"][0]`.
- Le **tier obtenu, le score et les badges** ne vivent que dans les fichiers de sortie (JSON/HTML/markdown), jamais dans le terminal.
- Le rendu diffère d'une surface à l'autre faute de composant partagé : risque de dérive (un Gold qui ne ressemble pas à un Gold partout).

## Objectif

Surfacer un **verdict** cohérent — accroche `tier + score` (ex. `🥇 Gold · 94/100`) — par défaut sur chaque run, dans le terminal, le HTML et le markdown, à partir d'un modèle de données unique.

## Décisions cadrées

| Sujet              | Décision                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------- |
| Surfaces           | Terminal (stdout), HTML, Markdown. **Pas** le JSON.                                          |
| Accroche           | `tier + score` ensemble (ex. `🥇 Gold · 94/100`), avec le pire niveau échoué visible.        |
| Quand              | Affiché **par défaut** sur `regis analyze <url>`. `-q/--quiet` le supprime.                  |
| Style terminal     | Bloc multi-lignes, **click seul** (pas de dépendance `rich`).                                |
| Score              | % non pondéré **inchangé** (`passées/total`). On affiche seulement.                          |
| Badges markdown    | Texte + emoji (zéro dépendance, lisible en brut).                                            |
| Tiers              | **Dynamiques** : noms/conditions définis par le playbook. Icône **déclarative optionnelle**. |
| Marqueurs sévérité | Carrés colorés 🟥🟧🟩 (forme distincte des médailles rondes, orange ≠ or).                   |

## Architecture (approche A : modèle partagé + 3 renderers fins)

```text
final_report  ──►  build_verdict()  ──►  Verdict  ──►  3 renderers (terminal / markdown / HTML)
                   (regis/playbook/verdict.py)            partagent tier_label() / badge_emoji()
```

Un seul constructeur normalise le verdict ; trois renderers minces le consomment via les **mêmes** helpers de mapping. C'est l'unique point qui garantit qu'un tier donné se rend à l'identique partout.

### Modèle de données — `regis/playbook/verdict.py`

```python
@dataclass(frozen=True)
class RuleLine:
    slug: str
    level: str        # "critical" | "warning" | "info"
    message: str

@dataclass(frozen=True)
class VerdictBadge:
    label: str        # ex. "CVE: Critical" (depuis badge["label"] résolu)
    klass: str        # "error" | "warning" | "success"

@dataclass(frozen=True)
class Verdict:
    evaluated: bool            # False si aucun playbook n'a tourné
    tier: str | None           # nom du tier obtenu, ou None (aucun seuil atteint)
    tier_icon: str | None      # icône déclarée sur le tier, ou None
    score: int                 # 0-100
    total: int                 # nb de règles
    passed: int
    failed: int
    incomplete: int
    worst_level: str | None    # pire niveau échoué : "critical" | "warning" | "info" | None
    badges: list[VerdictBadge]
    failures: list[RuleLine]   # règles échouées (slug, level, message)
    incompletes: list[RuleLine]  # règles incomplètes (slug, message)

def build_verdict(final_report: dict) -> Verdict: ...
```

**Construction** :

- **Source** : `final_report["playbooks"][0]` si présent (cas par défaut et `--playbook`), sinon les champs top-level hoistés (`tier`/`badges`/`rules`/`rules_summary`, cas `--evaluate`/rerun). `evaluated=False` (et bloc omis) si ni l'un ni l'autre.
- `tier` ← champ `tier` ; `tier_icon` ← émis par l'évaluateur (voir plus bas) ; `score` ← `rules_summary.score`.
- Compteurs et `worst_level` ← réutilisent la logique existante de `_print_playbook_summary` : `passed`/`failed` (hors `status == "incomplete"`)/`incomplete`, `worst_level` = min par `severity_order` parmi les échecs.
- `badges` ← `final_report["badges"]` (déjà résolus en `{label, class}`), filtrés et **ordonnés** par `spec.presentation.badges`. Les slugs inconnus (ex. `score`, `freshness` du playbook par défaut, qui ne matchent aucun badge défini) sont **ignorés silencieusement** — comportement actuel conservé. La correction du playbook par défaut est un suivi séparé, hors scope.

### Helpers de mapping (source unique)

```python
TIER_FALLBACK_ICON = "🏷️"          # tier sans icône déclarée
TIER_NONE_LABEL    = "⚪ Unrated"   # aucun tier atteint

CLASS_EMOJI = {"error": "🟥", "warning": "🟧", "success": "🟩"}   # class des badges
LEVEL_EMOJI = {"critical": "🟥", "warning": "🟧", "info": "🟦"}    # level des règles
LEVEL_STYLE = {"critical": "red", "warning": "yellow", "info": "blue"}  # couleurs click

def tier_label(tier: str | None, icon: str | None) -> str:
    # None              -> "⚪ Unrated"
    # tier, icon donné  -> f"{icon} {tier}"
    # tier, sans icon   -> f"🏷️ {tier}"

def badge_emoji(klass: str) -> str:  # CLASS_EMOJI.get(klass, "")
```

> Note : `click` n'a pas de couleur orange ; le texte d'une ligne `warning` est colorisé en `yellow`, mais l'**emoji** reste le carré orange 🟧 — c'est l'emoji qui porte la distinction visuelle vis-à-vis des médailles, pas la couleur du texte.

### Schéma playbook — champ `icon` optionnel sur les tiers

`regis/schemas/playbook/v1alpha1/playbook.schema.json` : ajouter une propriété optionnelle `icon` (string) aux items de `spec.tiers`. Rétro-compatible (champ optionnel, pas dans `required`).

```yaml
spec:
  tiers:
    - name: Gold
      icon: "🥇" # optionnel
      condition: { ">": [var: rules_summary.score, 90] }
```

L'**évaluateur** (`regis/playbook/evaluator.py`), qui résout déjà le tier obtenu, émet en plus son `icon` sous une clé `tier_icon` (à côté de `tier`) dans le résultat playbook. Le **playbook par défaut** (`regis/playbooks/default/playbook.yaml`) reçoit `🥇/🥈/🥉` sur ses trois tiers (dogfood) — rendu identique à l'attendu out-of-the-box, mais piloté par la donnée.

## Renderers

Scénario de référence (maquettes) : score 78 → Silver, une règle **critique** en échec (le % non pondéré donne Silver mais un `critical` casse — cas « honnêteté »), badges error/warning/success.

### Terminal — `_render_verdict_block` (analyze.py, click)

Remplace `_print_playbook_summary` (le gate `if playbook_paths:` est retiré → affiché par défaut). Supprimé sous `-q/--quiet`. En-tête en gras neutre ; la sévérité est portée par les emoji carrés et la colorisation click des lignes de règles.

```text
  🥈 Silver · 78/100
  17/20 règles · 2 échecs · 1 incomplète · pire niveau : 🟧 warning
  🟥 CVE: Critical   🟧 CVE: High   🟩 SBOM: Present
  ✗ [cve-critical]    1 critical CVE (max 0)
  ✗ [cve-high]        12 high CVEs (max 10)
  ⚠ [scorecard-min]   OpenSSF Scorecard data unavailable
```

Cas « tout passe » : en-tête + `20/20 règles · tout passe ✓`, badges succès s'il y en a, pas de lignes d'échec.

### Markdown — préfixé en tête de `_render_markdown` (`regis/utils/report.py`)

```markdown
## 🥈 Silver · 78/100

**17/20 règles** · 2 échecs · 1 incomplète · pire niveau : 🟧 warning

🟥 CVE: Critical · 🟧 CVE: High · 🟩 SBOM: Present

|     | Règle         | Niveau   | Résultat               |
| --- | ------------- | -------- | ---------------------- |
| ✗   | cve-critical  | critical | 1 critical CVE (max 0) |
| ✗   | cve-high      | warning  | 12 high CVEs (max 10)  |
| ⚠   | scorecard-min | warning  | data unavailable       |
```

### HTML — panneau `.verdict` en tête de `regis/templates/html/report.html.j2`

Une partial Jinja, sans JS : grand titre `🥈 Silver · 78/100`, badges en chips colorés réutilisant la `class` existante → CSS (`error`/`warning`/`success`), ligne de compteurs + pire niveau, puis le détail des règles. `html.py` passe le `Verdict` au contexte du template.

## Cas limites

| Cas                                       | Rendu                                                                      |
| ----------------------------------------- | -------------------------------------------------------------------------- |
| Tout passe                                | `🥇 Gold · 100/100` + `N/N règles · tout passe ✓`                          |
| Aucun tier atteint                        | `⚪ Unrated · 42/100`                                                      |
| Tier sans `icon`                          | `🏷️ Production-Ready · 88/100`                                             |
| Règles incomplètes                        | comptées à part, lignes `⚠`                                                |
| `-q/--quiet`                              | bloc supprimé ; un breach `--fail` continue d'écrire sur stderr (inchangé) |
| Aucun playbook évalué (`evaluated=False`) | pas de bloc                                                                |

## Tests (gate couverture ≥ 90 %)

- **Unit `build_verdict`** sur fixtures : clean / silver-avec-critical / unrated / tier-sans-icon / no-playbook (source `playbooks[0]` vs top-level hoisté).
- **Unit helpers** `tier_label` (None / avec icône / sans icône) et `badge_emoji`.
- **Renderer terminal** : via `CliRunner`, ANSI strippé — vérifie l'accroche, les compteurs, l'ordre des badges, les lignes d'échec, la suppression sous `-q`.
- **Renderer markdown** : l'en-tête verdict est préfixé, table des règles correcte.
- **Renderer HTML** : le panneau `.verdict` est présent, les chips portent les classes `error`/`warning`/`success`.
- **Schéma** : `icon` optionnel accepté ; le playbook par défaut valide avec ses icônes ; l'évaluateur émet `tier_icon`.

## Hors scope (suivis séparés)

- Pondération du score par sévérité (gate critique, score pondéré) — explicitement écarté.
- Correction de `spec.presentation.badges` du playbook par défaut (slugs `score`/`freshness` orphelins).
- Badges shields.io / SVG offline en markdown — écarté au profit du texte + emoji.

## Fichiers touchés

- **Nouveau** : `regis/playbook/verdict.py` (modèle + helpers + `build_verdict`).
- `regis/commands/analyze.py` : `_render_verdict_block` (remplace `_print_playbook_summary`), appel par défaut, respect de `-q`.
- `regis/playbook/evaluator.py` : émission de `tier_icon`.
- `regis/schemas/playbook/v1alpha1/playbook.schema.json` : `icon` optionnel sur les tiers.
- `regis/playbooks/default/playbook.yaml` : icônes 🥇🥈🥉.
- `regis/utils/report.py` : préfixe verdict dans `_render_markdown`.
- `regis/templates/html/report.html.j2` (+ `regis/report/html.py`) : panneau `.verdict`.
- Tests associés.
