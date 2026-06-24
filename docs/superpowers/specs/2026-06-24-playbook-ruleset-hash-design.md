# Empreinte de ruleset (`ruleset_hash`) — rendre le reçu SARIF tamper-evident

> Suite directe de [#797](https://github.com/trivoallan/regis/pull/797) (reçu SARIF `kind:"pass"`
> qui distingue « évalué & clean » de « jamais analysé »). Ce document fait autorité pour le
> sous-chantier **`ruleset_hash`**.

## 1. Contexte

#797 a réglé l'ambiguïté *absence* (clean vs jamais-scanné) en émettant un reçu positif
`kind:"pass"` keyé au digest. Reste une faille de **substance** : le reçu dit « gouverné »,
pas « gouverné **contre quel** ruleset ». Un reçu obtenu contre un playbook trivial — ou contre
un playbook trafiqué qui garde le même nom/version mais **desserre un seuil** (`cve-count.max`
0 → 9999) — est gouverné sur le papier. Par l'identité seule (`slug`+`version`, déjà présente),
c'est indétectable : l'identité est *gameable*.

L'identité déclarative est insuffisante car le report ne porte **pas** les `options` des règles :
l'entry d'issue est `{slug, description, level, tags, passed, status, message, analyzers,
criterion}` ([`evaluator.py:424-436`](../../../regis/core/domain/rules/evaluator.py)), où
`criterion` est le seul *nom* du template. Le seuil n'y figure jamais → hasher les rules d'issue
n'attrape pas le tampering paramétrique.

En revanche, la règle **résolue** qui est réellement évaluée porte sa `condition` (le JSON Logic
avec le seuil baked-in, [`evaluator.py:382-400`](../../../regis/core/domain/rules/evaluator.py)).
Hasher la `condition` défait le tampering paramétrique **par construction**.

## 2. Décisions (tranchées au brainstorming, 2026-06-24)

1. **Modèle de menace : tamper-evidence totale, seuils inclus** (pas seulement structurelle). Le
   consommateur découplé doit pouvoir détecter « mêmes règles, seuils desserrés », pas seulement
   « mauvais playbook ».
2. **Hash du *ruleset résolu*, pas du fichier source.** Calculé sur ce qui a réellement mordu
   (templates instanciés + règles activées), pas sur le YAML source — meilleur sémantiquement
   (capture l'instanciation, ignore commentaires/whitespace) et placé dans le cœur (fait du
   domaine), rendu par l'adaptateur.
3. **Placement du calcul : cœur** (`core.domain.rules`), pas l'adaptateur SARIF. L'empreinte « ce
   qui a été imposé » est un fait du domaine ; l'adaptateur ne fait que la *rendre*.
4. **Surface : sur le reçu `kind:"pass"`** (donc cas clean uniquement). C'est exactement le
   périmètre de la menace. Un run en échec n'a pas de reçu, mais ses breaches *sont* la preuve
   d'un ruleset réel. Pin sur les runs en échec = **extension différée**.
5. **Un hash par playbook** (les playbooks sont évalués indépendamment,
   [`playbook_runner.py:64-107`](../../../regis/core/application/playbook_runner.py)) ; le reçu
   surface celui du **primaire** (`playbooks[0]`). Pas de hash-merge multi-playbook spéculatif.

## 3. Design

### 3.1 Unité : `ruleset_fingerprint`

Nouveau module pur `regis/core/domain/rules/fingerprint.py` :

```python
def ruleset_fingerprint(enabled_rules: list[dict[str, Any]]) -> str:
    """Empreinte stable du ruleset résolu réellement imposé.

    Tamper-evident : tout changement de ce qui mord (règle ajoutée/retirée,
    sévérité modifiée, seuil desserré dans la condition) change le hash.
    """
```

- **Input** : `enabled_rules` — les règles résolues **et activées** (`enable=False` déjà filtré,
  [`evaluator.py:387`](../../../regis/core/domain/rules/evaluator.py)). Une règle désactivée
  n'entre pas (correct : non imposée).
- **Champs retenus par règle** : `{slug, level, condition}`. La `condition` (JSON Logic résolu)
  porte le seuil. **Exclus** : `description`, `message`, `tags` (cosmétique/présentation/scoring —
  ne changent pas le verdict pass/fail d'une règle).
- **Canonicalisation** : règles triées par `slug` ; `json.dumps(payload, sort_keys=True,
  separators=(",", ":"), ensure_ascii=False)` ; `sha256` du UTF-8.
- **Sortie** : `"sha256:<hex64>"` (préfixe auto-descriptif, **non tronqué** — pin de sécurité).

**Propriétés garanties (= tests) :** déterministe · indépendant de l'ordre des règles · *sensible
au seuil* (changer une valeur de `condition` change le hash) · *insensible au cosmétique*
(changer `description`/`message`/`tags` ne change pas le hash).

### 3.2 Câblage / data flow

1. `evaluate_rules` ([`evaluator.py:362`](../../../regis/core/domain/rules/evaluator.py)) calcule
   `ruleset_hash = ruleset_fingerprint(enabled_rules)` après le filtre `enable`, et l'ajoute à son
   `rules_results` retourné.
2. Le `result` du playbook ([`evaluator.py:98-106`](../../../regis/core/domain/playbook/evaluator.py))
   gagne `"ruleset_hash": rules_results["ruleset_hash"]`.
3. Il remonte tel quel dans `report["playbook"]` / `report["playbooks"][i]` via `run_playbooks`
   (aucune transformation requise).

### 3.3 Surface SARIF

`build_sarif` ([`sarif.py`](../../../regis/adapters/driven/report/sarif.py)) lit
`report.get("playbook", {}).get("ruleset_hash")` et, **s'il est présent**, l'ajoute aux
`properties` du reçu `kind:"pass"`, à côté de `digest` :

```json
"properties": { "image": "...", "digest": "sha256-...", "evaluated": 14,
                "ruleset_hash": "sha256:9f2c..." }
```

Le consommateur épingle la valeur attendue : un playbook trafiqué → hash différent → reçu rejeté.

### 3.4 Schéma

- **Bump `REPORT_SCHEMA_VERSION` 5 → 6** ([`report.py:8`](../../../regis/core/model/report.py)).
  Changement **additif** (champ optionnel) : un consommateur v5 parse encore un report v6 (champ
  ignoré) ; exiger v6 permet de *se reposer* sur le hash.
- Déclarer `ruleset_hash` (string optionnel, non `required`) sur l'objet playbook-result dans :
  - `regis/schemas/playbook/result.schema.json` (validation de `regis playbook`),
  - la section `playbook` / `playbooks` de `regis/schemas/report/report.schema.json`
    (`report.schema.json` est `additionalProperties:false` au top-level — vérifier que la
    sous-définition du playbook-result l'est aussi et y ajouter le champ).

## 4. Gestion d'erreur

- `condition` est un dict JSON Logic déjà validé par le schéma playbook → JSON-sérialisable par
  construction. Pas de `try/except` autour du `json.dumps` (échouer fort = bug de schéma en amont).
- `ruleset_hash` absent du report (reports legacy < v6, ou report sans playbook) → `build_sarif`
  l'omet simplement (`.get` → `None` → propriété non émise). **Rétro-compatible**, aucune erreur.
- Ruleset vide (`enabled_rules == []`) → pas de reçu émis de toute façon (#797 exige `rules`), donc
  le hash d'un ruleset vide n'est jamais surfacé.

## 5. Tests

| Cible | Cas |
| --- | --- |
| `ruleset_fingerprint` | déterminisme ; ordre-indépendant ; **seuil → hash change** (le test qui prouve la menace défaite) ; cosmétique → hash stable ; format `sha256:` |
| `evaluate_rules` / playbook result | le `result` porte `ruleset_hash` |
| SARIF | reçu porte `ruleset_hash` issu de `report["playbook"]["ruleset_hash"]` ; **absent** quand pas dans le report (rétro-compat) |
| Schéma | report v6 avec `ruleset_hash` valide ; `result.schema.json` valide |

Gates : couverture par-fichier ≥ 90 % sur les fichiers touchés ; suite complète verte ; ruff clean.

## 6. Hors périmètre / différé

- **Pin sur les runs en échec** (porter `ruleset_hash` aussi sur les results `kind:"fail"` ou au
  niveau `run.properties`). La menace stated est le cas *pass* ; les breaches prouvent déjà un
  ruleset réel.
- **Hash-merge multi-playbook** (une empreinte unique couvrant tous les playbooks). Per-playbook
  suffit ; le reçu pin le primaire.
- **Distribution d'une allowlist de hashes approuvés** côté consommateur (houba) — hors de ce repo.

## 7. Fichiers touchés (indicatif)

| Fichier | Changement |
| --- | --- |
| `regis/core/domain/rules/fingerprint.py` | **nouveau** — `ruleset_fingerprint` |
| `regis/core/domain/rules/evaluator.py` | calcule + expose `ruleset_hash` dans `rules_results` |
| `regis/core/domain/playbook/evaluator.py` | propage `ruleset_hash` dans le `result` |
| `regis/core/model/report.py` | bump `REPORT_SCHEMA_VERSION` 5 → 6 |
| `regis/schemas/playbook/result.schema.json` | champ optionnel `ruleset_hash` |
| `regis/schemas/report/report.schema.json` | champ optionnel `ruleset_hash` (sous-déf playbook) |
| `regis/adapters/driven/report/sarif.py` | rend `ruleset_hash` sur le reçu |
| `tests/…` | cf. §5 |
| `docs/website/docs/reference/cli.md` | mentionner le `ruleset_hash` du reçu |
