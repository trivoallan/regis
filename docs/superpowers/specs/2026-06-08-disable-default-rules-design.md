# Suppression de l'héritage implicite des règles par défaut

**Date** : 2026-06-08
**Type** : `feat(rules)!` (cassant, bump mineur pré-v1)
**Statut** : conception validée

## Problème

Aujourd'hui, un playbook n'évalue jamais une page blanche. Le moteur
([`evaluate_rules`](../../../regis/rules/evaluator.py)) appelle
`merge_rules(defaults, custom)`, et `merge_rules` **réinjecte tous les
`default_criteria()` non instanciés** des analyzers présents
([evaluator.py:236-241](../../../regis/rules/evaluator.py)). Conséquence : ce
qu'on lit dans le YAML d'un playbook ≠ ce qui est réellement évalué. Un playbook
hérite silencieusement de tout ce que les analyzers embarquent.

Cela casse l'auditabilité et la reproductibilité : on ne peut pas garantir qu'un
playbook évalue exactement ses règles déclarées.

### Portée concrète de l'auto-injection

Le playbook par défaut déclare ~10 critères, mais 9 `default_criteria` non
déclarés sont aujourd'hui auto-injectés et évalués (params concrets, vrai verdict
pass/fail qui compte dans le score/tier) :

| Critère auto-injecté          | Politique implicite actuelle |
| ----------------------------- | ---------------------------- |
| `dockle:severity-count`       | 0 alerte FATAL               |
| `hadolint:severity-count`     | 0 erreur Hadolint            |
| `secrets:secret-scan`         | 0 secret (vérifié ou non)    |
| `oci:max-size`                | ≤ 1000 Mo                    |
| `oci:layers-count`            | ≤ 30 couches                 |
| `oci:platforms-count`         | ≥ 2 plateformes              |
| `oci:exposed-ports-whitelist` | ports ∈ {80, 443}            |
| `oci:required-labels`         | label `image.source` présent |
| `oci:env-blacklist`           | pas de `DEBUG`/`SECRET_KEY`  |

## Objectif

**On n'hérite jamais des défauts.** Pas d'interrupteur, pas de champ de playbook :
on retire purement l'auto-injection. Un playbook évalue _uniquement_ ses règles
déclarées. Les `default_criteria()` redeviennent un **catalogue de templates**,
résolus seulement quand un playbook les instancie via `criterion:`.

Décisions de conception (toutes validées) :

1. **Aucun interrupteur** — comportement global, pas de flag CLI ni de champ
   `spec.inheritDefaults`. Le schéma playbook est **inchangé**.
2. **Vocabulaire** — finir la migration `rule → criterion` : « default rules »
   disparaît du code. `get_default_rules` → `get_criterion_templates` (c'est un
   catalogue, pas des règles par défaut).
3. **Playbook par défaut curé** (changement assumé, pas iso-comportement) : on
   déclare explicitement les 3 critères sécurité (`dockle:severity-count`,
   `hadolint:severity-count`, `secrets:secret-scan`) et on **abandonne** les 6
   heuristiques OCI (elles restent instanciables comme templates).

## Conception

### 1. Moteur d'évaluation — `regis/rules/evaluator.py`

| Avant                                                                                       | Après                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `get_default_rules(analyzers_present)`                                                      | **`get_criterion_templates(analyzers_present)`** — contenu identique (cœur `registry-domain-whitelist` + `default_criteria()` par analyzer présent), rôle clarifié : le catalogue.                                          |
| `merge_rules(defaults, custom)` réinjecte les défauts non instanciés                        | **`resolve_rules(templates, declared)`** — `final_dict` démarre **vide** ; le catalogue ne sert plus qu'à résoudre les instanciations `criterion:` (Case A) et les overrides par slug (Case B). Aucune inclusion implicite. |
| `evaluate_rules` : `defaults = get_default_rules(…); final = merge_rules(defaults, custom)` | `templates = get_criterion_templates(…); final = resolve_rules(templates, declared)` — playbook sans règle ⇒ **0 règle évaluée**.                                                                                           |

- Les corps de `default_criteria()` des analyzers **ne changent pas** : les 6
  heuristiques OCI restent définies et instanciables.
- Le template `core:registry-domain-whitelist`, défini en dur dans la fonction
  catalogue, y reste ; le playbook par défaut le référence
  (`provider: core, criterion: registry-domain-whitelist`) et il se résout
  normalement.
- La résolution Case A (instanciation `provider + criterion` + `options`) et le
  « last resort » qui charge un template directement depuis la classe analyzer
  ([evaluator.py:159-170](../../../regis/rules/evaluator.py)) restent inchangés —
  c'est ce qui permet de référencer un template même si l'analyzer n'a pas tourné.
- `get_default_rules` / `merge_rules` sont **internes** (importés seulement par
  `evaluator.py` et `commands/rules.py`) : rename direct, pas de shim public.

### 2. Playbook par défaut — `regis/playbooks/default/playbook.yaml`

Ajout des 3 critères sécurité désormais explicites :

```yaml
# --- Sécurité conteneur (Warning) — désormais explicites ---
- provider: dockle
  criterion: severity-count
  slug: dockle-fatal
  level: warning
- provider: hadolint
  criterion: severity-count
  slug: hadolint-error
  level: warning
- provider: secrets
  criterion: secret-scan
  slug: secret-scan
  level: warning
```

Non ajoutés (abandonnés du run par défaut, toujours instanciables manuellement) :
`oci:max-size`, `layers-count`, `platforms-count`, `exposed-ports-whitelist`,
`required-labels`, `env-blacklist`.

Effet : le score/tier du run par défaut **change** (assumé). Bump du label
`app.kubernetes.io/version` du playbook : **1.0.0 → 2.0.0** (on retire des règles
= cassant pour les consommateurs du rapport par défaut).

### 3. Commande catalogue — `regis/commands/rules.py`

Deux call sites ([:164](../../../regis/commands/rules.py),
[:294](../../../regis/commands/rules.py)) consomment aujourd'hui
`get_default_rules` + `merge_rules`. La commande est un outil de **découverte du
catalogue** (« list all available default rules »), distinct de l'évaluation.
Comme `resolve_rules` ne réinjecte plus :

- Sans fichier de règles, `regis rules` doit continuer à lister le **catalogue
  complet** des templates instanciables — donc s'appuyer sur
  `get_criterion_templates()` directement (et non sur `resolve_rules`, qui
  renverrait du vide). Intention : « voici ce que tu peux instancier ».
- Avec un fichier de règles fourni, la commande montre l'ensemble **résolu**
  (templates instanciés + overrides) via `resolve_rules`.
- Vérifier pendant le plan le format exact attendu par l'option de chemin
  (fichier de règles plat vs enveloppe playbook `spec.rules`) et l'aligner sans
  régression.

Docstrings et libellés « default rules » → « available criteria ».

### 4. Rupture & migration

- **Cassant** : tout playbook tiers qui s'appuyait sur l'auto-injection évalue
  désormais moins de règles. Commit `feat(rules)!` → bump mineur pré-v1.
- **Pas de codemod automatique** : réinjecter les ex-défauts irait à l'encontre
  de la curation (on ré-imposerait les heuristiques OCI). À la place : **note
  d'upgrade** + `regis rules` pour découvrir les templates à déclarer soi-même.
- **Schéma playbook inchangé** : choix « jamais d'héritage » ⇒ aucun champ ajouté.

## Surface de test

- **MAJ** des tests qui assertent l'évaluation implicite (dockle / hadolint / OCI
  dans un run nu) — ils doivent refléter la curation.
- **Nouveaux tests** :
  - un template non référencé n'est **jamais** évalué ;
  - un playbook sans `rules` ⇒ **0 règle** évaluée ;
  - `regis rules` (sans playbook) liste toujours le catalogue complet ;
  - snapshot du playbook par défaut curé (les 3 ajouts présents, les 6 OCI
    absents).
- Couverture ≥ 90 % maintenue (le seuil CI échoue en dessous).

## Docs

- `concepts/rules` : retirer la notion d'héritage implicite des défauts.
- concept `criterion` : insister sur templates ≠ règles évaluées.
- doc du playbook par défaut : refléter la curation.
- **Guide d'upgrade** `upgrade/implicit-defaults-removal.md` : expliquer la
  rupture, lister les 9 critères ex-implicites, montrer comment ré-déclarer ceux
  qu'on veut conserver via `regis rules`.

## Hors périmètre

- Aucun flag CLI ni champ de playbook pour basculer le comportement (rejeté :
  « on n'hérite jamais »).
- Aucun codemod / migration automatique de playbooks.
- Pas de modification des corps `default_criteria()` des analyzers.
- Pas de mode « métriques brutes sans verdict » (motivation retenue =
  auditabilité des playbooks explicites, pas collecte brute).
