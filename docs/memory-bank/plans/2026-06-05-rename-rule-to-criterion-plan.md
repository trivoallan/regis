# Plan — Désurcharger « rule » : modèle de vocabulaire à 4 couches

> Issu d'un brainstorm produit du 2026-06-05. Statut : **validé, prêt à exécuter**.

## Contexte

La page [`concepts/rules`](https://trivoallan.github.io/regis/docs/concepts/rules)
et le code emploient le mot **« rule »** pour désigner trois choses différentes,
ce qui brouille le modèle mental des auteurs de playbooks :

1. ce qu'un analyzer **mesure** (données brutes : `critical_count`, `has_sbom`…) ;
2. ce qu'un analyzer **livre comme condition réutilisable** (`default_rules()`,
   templates type `cve-count` avec `params` ouverts) ;
3. ce qu'un playbook **décide** (lier une condition à un seuil + une sévérité +
   un tier).

Le mot « rule » n'est juste qu'au niveau 3. Aux niveaux 1 et 2 il écrase la
distinction mesure → condition → décision. Précédents policy-as-code qui ont déjà
tranché ce découpage : Kubernetes Gatekeeper (`ConstraintTemplate` → `Constraint`),
SCAP (`check` → `rule` → `benchmark`), OSCAL/NIST (`control`, `finding`).

## Le modèle cible — 4 couches

```text
finding        détection brute (CVE sur un paquet, secret fuité)          [page analyzers]
   │ agrégée en
metric         mesure (critical_count, has_sbom, score, age_days)         [page analyzers, lue par le criterion]
   │ évaluée par
criterion      condition paramétrée sur des metrics (ex. cve-count)       [page concepts — NOUVEAU]
   │ liée dans le playbook en
rule           décision : seuil + sévérité + tier                         [page concepts — RECADRÉ]
```

Test de qualité du vocabulaire : la chaîne se raconte d'une traite
(« un _finding_ est agrégé en _metric_, évaluée par un _criterion_, lié en _rule_ »).

## Décisions validées

1. **`criterion`**, pas `check`. `check` collisionne avec la commande CLI
   existante `regis check` ([`regis/commands/check.py:21`](../../regis/commands/check.py)) →
   recréerait la surcharge qu'on élimine. `criterion` était l'instinct initial,
   ne collisionne avec rien, et se lit « le critère qu'on lie _constitue_ une rule ».
2. **Rename à fond** : `rule.` → `criterion.` **partout**, y compris le namespace
   interne des conditions JSON Logic (`rule.params` → `criterion.params`). Pas de
   « legacy binding » figé — un binding nommé d'après la couche qu'on désurcharge
   serait la maladie qui survit au traitement.
3. **`rule.` est l'objet entier**, pas seulement `rule.params`.
   [`evaluator.py:343`](../../regis/rules/evaluator.py) fait
   `flat_context["rule"] = rule`. La cible du rename est **tout préfixe `rule.`**
   (`rule.params.*`, mais aussi `rule.level`, `rule.slug`, `rule.tags`…).
4. **Niveau 1 — `metric` est le mot de concept** (lu par les criteria). `finding`
   reste local et déjà correct (`secrets.findings`), **non promu** au vocabulaire
   top-level et **non généralisé**.
5. **Pas de fusion des arrays de détail.** Ne **pas** renommer `cve.targets[]` ni
   `sbom.components[]` en `findings`. Un `component` SBOM est de l'**inventaire**,
   pas une détection — les confondre serait une nouvelle erreur de modèle.
   `results.` (namespace des metrics) **reste inchangé**.
6. **Rollout non cassant** via dual-bind runtime + codemod + fenêtre de
   dépréciation, coupure franche à la prochaine **majeure**. On est en 0.x : le
   breaking reste affordable maintenant, de moins en moins ensuite.

## Surface du rename

| Surface           | Détail                                                                                            | Scope commit                       |
| ----------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Doc concept       | Page `concepts/rules` + nouvelle notion `criterion` ; page `analyzers` (metric/finding/component) | `docs`                             |
| API analyzer      | `BaseAnalyzer.default_rules()` → `default_criteria()`                                             | `analyzer`                         |
| Défauts analyzers | conditions + messages `rule.*` → `criterion.*` dans `regis/analyzers/*.py` (~9 fichiers)          | `analyzer/cve`, `analyzer/sbom`, … |
| Moteur            | `flat_context["rule"]` → `criterion` (+ dual-bind), logique de merge templates                    | `playbook`                         |
| Clé playbook      | `rule: <slug>` → `criterion: <slug>` (le merge `provider`+`rule`+`options`)                       | `playbook`                         |
| Schémas           | schémas playbook / analyzer référençant `rule`                                                    | `schema`                           |
| Codemod           | nouvelle commande `regis playbook migrate`                                                        | `cli`                              |

## Observations qui dérisquent (issues du brainstorm)

- **Le dual-bind runtime coûte une ligne.** Point d'injection unique
  ([`evaluator.py:343`](../../regis/rules/evaluator.py)) :
  ```python
  flat_context["criterion"] = rule
  flat_context["rule"] = rule   # legacy — gardé pendant la fenêtre + warn si touché
  ```
  Réécriture vers `criterion.` partout **et** runtime tolérant `rule.` pendant la
  transition → un client non-migré n'est pas cassé, juste averti. La ligne legacy
  saute à la majeure.
- **Le JSON Logic imbriqué qui fait peur est dans NOTRE code.** Toutes les
  conditions `rule.params` imbriquées (`{"cat": [{"var": "rule.params.level"}, "_count"]}`…)
  vivent dans `regis/analyzers/*.py` — réécrites une fois, sous tests. Les
  playbooks **utilisateurs** référencent surtout des templates par slug + `options:`
  et **ne portent pas l'arbre de condition** ; seules les rules custom qui ont
  paramétré via `rule.params` sont concernées (rare — une custom hardcode
  d'ordinaire ses valeurs). Blast radius client petit.

## Phasage

### Phase 0 — Filet avant de toucher quoi que ce soit

- Test d'invariant : `evaluate(report, pb) == evaluate(report, migrate(pb))` sur le
  playbook par défaut + corpus de fixtures.
- Test de dual-bind : un playbook non-migré et son jumeau migré produisent un
  rapport **identique**. (Prouve que la fenêtre de dépréciation tient.)
- **Premier test à écrire** : le loader lit indifféremment `rule:` et `criterion:`
  et produit le même rapport. S'il passe, le reste est mécanique.

### Phase 1 — Moteur tolérant (non cassant, livrable seul)

- `_build_context` / `evaluate_rules` : dual-bind `criterion`/`rule` ; warn de
  dépréciation si une condition ou un message touche `rule.`.
- Loader playbook : accepte `criterion:` **et** `rule:` (warn sur l'ancien).

### Phase 2 — Réécriture des défauts (notre code)

- `BaseAnalyzer.default_rules()` → `default_criteria()` (garder un alias déprécié
  le temps de la fenêtre).
- Réécrire conditions **et** messages dans `regis/analyzers/*.py` :
  `rule.*` → `criterion.*`. **Deux passes distinctes** :
  1. conditions — walk structuré de l'arbre JSON Logic (grammaire fermée,
     déterministe), réécrire tout opérande `var` à préfixe `rule.` ;
  2. messages — passe texte sur les `${…}`. **Cas gratiné** : le fail message CVE
     `${results.cve.${rule.params.level}_count}` (interpolation imbriquée) — réécrire
     le `${rule.…}` interne sans casser le `${results.…}` externe.
- Schémas mis à jour.

### Phase 3 — Codemod `regis playbook migrate`

- Réutilise les deux passes de la Phase 2 sur les playbooks utilisateurs :
  clé YAML `rule:` → `criterion:`, conditions + messages des rules custom.
- Idempotent ; couvert par l'invariant de la Phase 0.

### Phase 4 — Doc

- Page `concepts/rules` recadrée (criterion → rule) ; notion `criterion` introduite.
- Page `analyzers` : metric (lu par criteria) vs finding (détection) vs component
  (inventaire).
- Guide de migration + mention du codemod.

### Phase 5 — Coupure (prochaine majeure)

- Retirer le dual-bind `rule.`, l'alias `default_rules()`, l'acceptation de la clé
  `rule:`. `criterion.` seul.

## Risques

- **Interpolation imbriquée dans les messages** (`${…${rule.…}…}`) — la passe texte
  est le maillon faible ; couvrir explicitement par fixtures.
- **Codemod sur `.gitlab-ci.yml` client** — le `.gitlab-ci.yml` racine est un
  exemple client confidentiel : ne jamais le stager/commiter. Le codemod doit
  pouvoir tourner sans toucher au versionnement.
- **Fenêtre de dépréciation** — documenter combien de minor versions avant la
  coupure ; les warns doivent être actionnables (pointer vers `regis playbook migrate`).

## Ouvert (post-MVP)

- `finding` vs `component` mérite-t-il une formalisation schéma sur la page
  analyzers, ou reste-t-il purement documentaire ? (Tranché « local » pour ce
  plan ; à rouvrir si une 2ᵉ analyzer d'inventaire apparaît.)
