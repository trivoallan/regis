# Secret-scan : critères booléens (verified / any)

**Date :** 2026-06-08
**Statut :** Validé, prêt pour plan d'implémentation
**Type :** `feat(analyzer)!` — breaking change

## Problème

Le critère `secret-scan` de l'analyzer `secrets` repose sur un comptage avec
seuil configurable : `secrets_count <= max_count`, `max_count: 0` par défaut
(`regis/analyzers/secrets.py:48`).

Ce paramètre est un faux paramètre :

- Un seuil de secrets « acceptable » > 0 n'a aucun sens en posture sécurité.
  Tolérer « jusqu'à N credentials en dur » est un anti-pattern.
- La doc générée affiche la description du paramètre comme `n/a`
  (`docs/website/docs/reference/rules/secrets/secret-scan.md:19`) — symptôme
  que le paramètre n'a pas de sémantique réelle.
- L'analyzer expose déjà `verified_count` (secrets confirmés actifs par
  TruffleHog, distincts des simples matches), inexploité par les critères.

## Objectif

Remplacer le critère unique à compteur par **deux critères booléens** qui
expriment l'intention exacte et exploitent la distinction vérifié/non-vérifié :

| Slug | Niveau | Condition | Intention |
| :-- | :-- | :-- | :-- |
| `verified-secrets` | `critical` | `verified_count == 0` | Credentials confirmés actifs |
| `secret-scan` | `warning` | `secrets_count == 0` | Tout secret détecté (vérifié ou non) |

### Choix de nommage

- `secret-scan` est **conservé** pour le critère large (warning) plutôt que
  renommé en `unverified-secrets` : ce critère fire sur *tous* les secrets, donc
  « unverified » serait trompeur ; conserver le slug préserve l'URL de doc
  existante. C'est néanmoins un breaking change car sa sémantique change
  (compteur → booléen, `critical` → `warning`, suppression de `max_count`).
- `verified-secrets` est un nouveau critère critique, suivant la convention
  booléenne de `has-sbom` (`regis/analyzers/sbom.py:95`).

### Niveaux disponibles

L'enum de niveaux est `["info", "warning", "critical", "none"]`
(`regis/schemas/playbook/v1alpha1/playbook.schema.json:170`). Pas de « high » /
« medium » : le critère large est donc `warning`.

## Design

### Analyzer — `regis/analyzers/secrets.py`

`default_criteria()` renvoie deux critères au lieu d'un. Conditions en JSON
Logic (style `has-sbom`) :

```python
# verified-secrets (critical)
{"==": [{"var": "results.secrets.verified_count"}, 0]}
# secret-scan (warning)
{"==": [{"var": "results.secrets.secrets_count"}, 0]}
```

Messages :

- `verified-secrets`
  - pass : `No verified secrets detected in the image.`
  - fail : `TruffleHog verified ${results.secrets.verified_count} active credential(s) in the image.`
- `secret-scan`
  - pass : `No secrets detected in the image.`
  - fail : `TruffleHog detected ${results.secrets.secrets_count} secret(s) in the image.`

Aucun changement dans `analyze()` : `secrets_count` et `verified_count` sont
déjà produits (`regis/analyzers/secrets.py:105`) et requis par le schéma
(`regis/schemas/analyzer/secrets.schema.json:13`).

### Playbook par défaut — `regis/playbooks/default/playbook.yaml`

Ajouter **uniquement** `verified-secrets` dans la section Security (Critical) :

```yaml
    - provider: secrets
      criterion: verified-secrets
      slug: verified-secrets
      level: critical
```

Le critère large `secret-scan` (warning) reste disponible dans
`default_criteria()` mais n'est pas câblé par le playbook par défaut (cohérent
avec l'état actuel où aucun critère secrets n'y figure).

### Documentation générée

Les pages `reference/rules/**.md` sont produites par `regis rules list` →
`_render_rule_markdown` (`regis/commands/rules.py:204`), pas éditées à la main.
Régénérer après le changement de code :

- `docs/website/docs/reference/rules/secrets/secret-scan.md` (mis à jour :
  booléen, plus de table Parameters, niveau warning)
- `docs/website/docs/reference/rules/secrets/verified-secrets.md` (nouvelle page)

Vérifier que `_render_rule_markdown` gère proprement un critère sans `params`
(déjà le cas pour `has-sbom`).

## Tests

- `tests/test_analyzer_secrets.py` : mettre à jour les attentes sur
  `default_criteria()` — deux critères, slugs, niveaux, conditions, messages.
- Couvrir les deux conditions booléennes : image sans secret (pass/pass),
  secret non vérifié seul (verified pass, secret-scan fail), secret vérifié
  (les deux fail).
- Suite complète avant PR (couverture ≥ 90 %).

## Hors périmètre (YAGNI)

- Pas d'allowlist de findings spécifiques (mécanisme séparé, futur si besoin).
- Pas de nouveau champ `unverified_count` : le warning fire sur *tous* les
  secrets (`secrets_count`), donc inutile.
- Pas de critère `info` distinct pour les non-vérifiés.

## Migration / breaking change

- Commit `feat(analyzer)!` avec note BREAKING CHANGE : `secret-scan` passe de
  critical/compteur à warning/booléen, le paramètre `max_count` disparaît.
- Tout playbook utilisateur référençant `secret-scan` avec `options.max_count`
  doit retirer ce paramètre ; pour gater les credentials actifs en critical,
  ajouter le critère `verified-secrets`.
