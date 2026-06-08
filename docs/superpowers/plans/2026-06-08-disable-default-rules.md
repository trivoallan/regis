# Suppression de l'héritage implicite des règles par défaut — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un playbook n'évalue plus que ses règles déclarées ; les `default_criteria()` deviennent un catalogue de templates résolus uniquement sur référence.

**Architecture:** Dans le moteur d'évaluation, `get_default_rules` devient `get_criterion_templates` (catalogue inchangé) et `merge_rules` devient `resolve_rules` qui n'auto-injecte plus les templates non référencés (`final_dict` démarre vide). La commande `regis rules` reste un catalogue de découverte. Le playbook par défaut est curé (ajout de 3 critères sécurité explicites, abandon de 6 heuristiques OCI) et son label de version passe à 2.0.0.

**Tech Stack:** Python 3.10+, pytest, JSON Logic (`json_logic`), Click, YAML (enveloppe playbook Kubernetes-like).

**Spec:** `docs/superpowers/specs/2026-06-08-disable-default-rules-design.md`

---

## Structure des fichiers

| Fichier                                                       | Responsabilité                        | Action                                           |
| ------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------ |
| `regis/rules/evaluator.py`                                    | Catalogue + résolution + évaluation   | Modifier (rename + retrait auto-injection)       |
| `regis/commands/rules.py`                                     | Commande `regis rules` (catalogue)    | Modifier (2 call sites)                          |
| `regis/playbooks/default/playbook.yaml`                       | Playbook par défaut livré             | Modifier (curation + bump version)               |
| `tests/test_rules_evaluator.py`                               | Tests du moteur                       | Modifier (rename + nouveaux tests + MAJ comptes) |
| `tests/test_default_playbook_envelope.py`                     | Test enveloppe du playbook par défaut | Modifier (version 2.0.0)                         |
| `tests/test_rules_command.py`, `tests/test_cli_rules_list.py` | Tests commande `regis rules`          | Vérifier / ajuster                               |
| `docs/website/docs/concepts/rules.md`                         | Concept règles                        | Modifier (retirer héritage implicite)            |
| `docs/website/docs/concepts/analyzers.md`                     | Concept analyzers                     | Vérifier / ajuster                               |
| `docs/website/docs/reference/playbooks/default/index.md`      | Référence du playbook par défaut      | Modifier (tableau Warning)                       |
| `docs/website/docs/upgrade/implicit-defaults-removal.md`      | Guide d'upgrade                       | Créer                                            |

---

## Task 1 : Moteur d'évaluation + commande — retrait de l'auto-injection + rename

**Files:**

- Modify: `regis/rules/evaluator.py` (fonctions `get_default_rules` → `get_criterion_templates`, `merge_rules` → `resolve_rules`, `evaluate_rules`)
- Modify: `regis/commands/rules.py` (call sites `list_rules` ~164-176 et `show_rule` ~294-306)
- Test: `tests/test_rules_evaluator.py`, `tests/test_cli_rules_list.py`, `tests/test_rules_command.py`

### Comportement cible

- Un template non référencé n'est **jamais** évalué.
- Un playbook sans `rules` ⇒ **0 règle** évaluée.
- Une référence Case A (`provider` + `criterion` + `options`) résout toujours le template depuis le catalogue.
- `get_default_rules` / `merge_rules` sont internes : rename direct, aucun shim.

- [ ] **Step 1 : Écrire les tests d'échec (nouveau comportement)**

Ajouter ces deux tests à la fin de `tests/test_rules_evaluator.py` :

```python
def test_unreferenced_template_not_evaluated():
    """A default criterion not referenced by the playbook is never evaluated."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["oci"]},
        "results": {"oci": {"size_mb": 50, "layers": 5}},
    }
    # The oci analyzer ships max-size / layers-count / ... criteria, but the
    # playbook declares nothing: none of them must be evaluated.
    res = evaluate_rules(report, {"rules": []})
    assert res["rules"] == []


def test_only_declared_rules_evaluated():
    """The evaluated set equals exactly the declared rules (no inheritance)."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["oci", "freshness"]},
        "results": {"oci": {"size_mb": 50}, "freshness": {"age_days": 10}},
    }
    rules_def = {
        "rules": [
            {
                "provider": "freshness",
                "criterion": "age",
                "slug": "age",
                "options": {"max_days": 30},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    assert [r["slug"] for r in res["rules"]] == ["age"]
```

- [ ] **Step 2 : Lancer les tests, vérifier l'échec**

Run: `pipenv run pytest tests/test_rules_evaluator.py::test_unreferenced_template_not_evaluated tests/test_rules_evaluator.py::test_only_declared_rules_evaluated --no-cov -v`
Expected: FAIL — aujourd'hui `res["rules"]` contient les défauts oci auto-injectés (max-size, layers-count, …) en plus.

- [ ] **Step 3 : Renommer `get_default_rules` → `get_criterion_templates`**

Dans `regis/rules/evaluator.py`, remplacer la signature et le docstring (le corps reste identique) :

```python
def get_criterion_templates(analyzers_present: list[str]) -> list[dict[str, Any]]:
    """Gather the criterion template catalog from analyzers present in the report.

    This is a *catalogue* of reusable, parameterized conditions (the core
    ``registry-domain-whitelist`` plus each present analyzer's
    ``default_criteria()``). Templates are resolved on reference by
    :func:`resolve_rules`; they are never evaluated unless a playbook declares
    them.
    """
```

(Le corps `from regis.analyzers.discovery import ...` jusqu'à `return default_rules` est inchangé ; la variable locale `default_rules` peut rester telle quelle.)

- [ ] **Step 4 : Renommer `merge_rules` → `resolve_rules` et retirer l'auto-injection**

Remplacer la signature/docstring :

```python
def resolve_rules(
    templates: list[dict[str, Any]], declared: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Resolve declared playbook rules against the criterion template catalogue.

    The final set contains EXACTLY the declared rules: each is either an
    instantiation of a catalogue template (Case A: ``provider`` + ``criterion``)
    or a standalone/override rule (Case B). Catalogue templates that are not
    referenced are intentionally NOT included — there is no implicit inheritance.
    """
```

Dans le corps, renommer les usages locaux pour rester cohérent :

- la boucle `for rule in default_rules:` (construction de `merged`) devient `for rule in templates:`
- la boucle `for rule_def in custom_rules:` devient `for rule_def in declared:`

Supprimer le suivi des templates instanciés, devenu inutile. Retirer la déclaration :

```python
    # Track template keys that are explicitly instantiated under a new slug so that
    # the original template entry can be removed from the final set (prevents duplicates).
    instantiated_template_keys: set[tuple[str, str]] = set()
```

et, dans le bloc Case A, retirer les lignes :

```python
                # Mark the source template as consumed so it is not included twice
                # in the final rule set (the instance takes its place).
                instantiated_template_keys.add((provider, template_name))
```

Enfin, remplacer le seeding de `final_dict` (l'auto-injection) :

```python
    # 3. Merge processed custom rules into the final set
    # Final result is still a list of rules with their (provider, slug) identity
    final_dict: dict[tuple[str, str], dict[str, Any]] = {}
    # Re-initialize with defaults, skipping templates that were explicitly
    # instantiated under a new slug by a custom rule (avoids duplicates).
    for k, v in merged.items():
        if k not in instantiated_template_keys:
            final_dict[k] = v
```

par :

```python
    # 3. Assemble the final set from DECLARED rules only.
    # `merged` is the template catalogue, used above solely to resolve Case A
    # instantiations. Unreferenced templates are never auto-included.
    final_dict: dict[tuple[str, str], dict[str, Any]] = {}
```

- [ ] **Step 5 : Mettre à jour `evaluate_rules`**

Remplacer (vers la ligne 351) :

```python
    defaults = get_default_rules(analyzers_present)

    custom = []
    if rules_def and isinstance(rules_def.get("rules"), list):
        custom = rules_def["rules"]

    final_rules = merge_rules(defaults, custom)
```

par :

```python
    templates = get_criterion_templates(analyzers_present)

    declared = []
    if rules_def and isinstance(rules_def.get("rules"), list):
        declared = rules_def["rules"]

    final_rules = resolve_rules(templates, declared)
```

- [ ] **Step 6 : Mettre à jour les tests existants cassés par le rename / le nouveau comportement**

Dans `tests/test_rules_evaluator.py` :

a) L'import en tête :

```python
from regis.rules.evaluator import evaluate_rules, get_default_rules, merge_rules
```

devient :

```python
from regis.rules.evaluator import (
    evaluate_rules,
    get_criterion_templates,
    resolve_rules,
)
```

b) Renommer `test_get_default_rules` et adapter son corps :

```python
def test_get_criterion_templates():
    rules = get_criterion_templates(["oci", "freshness"])
    slugs = [r.get("slug") for r in rules]
    assert "registry-domain-whitelist" in slugs
    assert "user-blacklist" in slugs
    assert "age" in slugs
```

c) Renommer `test_merge_rules` et adapter au nouveau contrat (une règle Case A est instanciée depuis le catalogue ; une règle Case B est autonome, sans héritage du catalogue) :

```python
def test_resolve_rules_instantiates_template():
    templates = [
        {
            "provider": "freshness",
            "slug": "age",
            "description": "Age check",
            "params": {"max_days": 30},
            "condition": {"<": [{"var": "results.freshness.age_days"}, 30]},
            "messages": {"pass": "fresh", "fail": "stale"},
        }
    ]
    declared = [
        {
            "provider": "freshness",
            "criterion": "age",
            "slug": "age",
            "options": {"max_days": 7},
        }
    ]
    resolved = resolve_rules(templates, declared)
    assert len(resolved) == 1
    assert resolved[0]["slug"] == "age"
    # Option override merged onto the template params.
    assert resolved[0]["params"]["max_days"] == 7
    # Template message preserved.
    assert resolved[0]["messages"]["pass"] == "fresh"


def test_resolve_rules_drops_unreferenced_templates():
    templates = [
        {"provider": "oci", "slug": "max-size", "condition": {"==": [1, 1]}},
    ]
    # Nothing declared -> nothing resolved.
    assert resolve_rules(templates, []) == []
```

d) Dans `test_evaluate_rules`, corriger le compte final (la règle cœur n'est plus auto-injectée) :

```python
    # Disabled rule should not be in results
    assert (
        len(res2["rules"]) == 3
    )  # core.registry-domain-whitelist + freshness.age + missing-data-rule
```

devient :

```python
    # Disabled rule should not be in results. Only declared rules are evaluated:
    # core.registry-domain-whitelist is no longer auto-injected.
    assert (
        len(res2["rules"]) == 2
    )  # freshness.age + missing-data-rule
```

e) Dans `test_evaluate_rule_params`, déclarer explicitement le critère `age` (un run nu n'évalue plus rien) :

```python
    # 1. Defaults: freshness max_days is 30. Age is 15. Condition: 15 < 30 -> Pass.
    res1 = evaluate_rules(report)
    freshness = next(r for r in res1["rules"] if r["slug"] == "age")
    assert freshness["passed"] is True
```

devient :

```python
    # 1. Declare the age criterion; template default max_days is 30. Age is 15 -> Pass.
    res1 = evaluate_rules(
        report,
        {"rules": [{"provider": "freshness", "criterion": "age", "slug": "age"}]},
    )
    freshness = next(r for r in res1["rules"] if r["slug"] == "age")
    assert freshness["passed"] is True
```

- [ ] **Step 7 : Lancer toute la suite du moteur**

Run: `pipenv run pytest tests/test_rules_evaluator.py --no-cov -v`
Expected: PASS (tous, dont les 2 nouveaux et les 4 adaptés).

- [ ] **Step 8 : Migrer les call sites de `regis rules` (même commit — garder tout vert)**

Le rename casserait `regis rules` (imports paresseux des anciens noms dans `regis/commands/rules.py`). On migre les deux call sites dans le même commit. D'abord, ajouter le test catalogue à la classe `TestCliRulesList` de `tests/test_cli_rules_list.py` (mêmes imports `CliRunner` / `main` ; `rules list` n'accepte que `text`/`markdown`) :

```python
    def test_rules_list_shows_full_catalogue_without_rules_file(self):
        """Discovery surfaces analyzer templates the default playbook omits."""
        result = CliRunner().invoke(main, ["rules", "list"])
        assert result.exit_code == 0
        # oci:max-size is a template the default playbook does NOT declare; the
        # catalogue must still list it.
        assert "max-size" in result.output
        assert "registry-domain-whitelist" in result.output
```

Puis migrer `list_rules`. Remplacer :

```python
    from regis.rules.evaluator import get_default_rules, merge_rules

    analyzers = discover_analyzers()
    defaults = get_default_rules(list(analyzers.keys()))

    custom = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("rules", [])

    final_rules = merge_rules(defaults, custom)
```

par :

```python
    from regis.rules.evaluator import get_criterion_templates, resolve_rules

    analyzers = discover_analyzers()
    templates = get_criterion_templates(list(analyzers.keys()))

    declared = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            declared = data.get("rules", [])

    # No rules file -> show the full catalogue (discovery). With a rules file ->
    # show exactly what that file evaluates.
    final_rules = resolve_rules(templates, declared) if declared else list(templates)
```

Mettre à jour le docstring de `list_rules` : `"""List all available default rules and any overrides."""` → `"""List the available criteria catalogue (or the resolved set for a rules file)."""`

- [ ] **Step 9 : Migrer `show_rule`**

Remplacer le bloc analogue (~294-306) :

```python
    from regis.rules.evaluator import get_default_rules, merge_rules

    analyzers = discover_analyzers()
    defaults = get_default_rules(list(analyzers.keys()))

    custom = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = data.get("rules", [])

    final_rules = merge_rules(defaults, custom)
```

par :

```python
    from regis.rules.evaluator import get_criterion_templates, resolve_rules

    analyzers = discover_analyzers()
    templates = get_criterion_templates(list(analyzers.keys()))

    declared = []
    if rules_path:
        path = Path(rules_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            declared = data.get("rules", [])

    final_rules = resolve_rules(templates, declared) if declared else list(templates)
```

- [ ] **Step 10 : Lancer les tests moteur + commande**

Run: `pipenv run pytest tests/test_rules_evaluator.py tests/test_cli_rules_list.py tests/test_rules_command.py --no-cov -v`
Expected: PASS. Si un test asserte un comportement « override fusionné sur défaut sans fichier », l'ajuster pour refléter le catalogue (les overrides ne s'appliquent qu'avec un fichier de règles).

- [ ] **Step 11 : Vérifier qu'aucun ancien nom ne subsiste**

Run: `pipenv run grep -rn "get_default_rules\|merge_rules" regis/ tests/ || grep -rn "get_default_rules\|merge_rules" regis/ tests/`
Expected: aucun résultat.

- [ ] **Step 12 : Commit (atomique, tout vert)**

```bash
git add regis/rules/evaluator.py regis/commands/rules.py tests/test_rules_evaluator.py tests/test_cli_rules_list.py tests/test_rules_command.py
git commit -m "feat(rules)!: stop auto-injecting unreferenced default criteria

Playbooks evaluate only their declared rules. get_default_rules ->
get_criterion_templates (catalogue), merge_rules -> resolve_rules with no
implicit inheritance. regis rules now lists the catalogue for discovery and
resolves only when a rules file is provided.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2 : Curation du playbook par défaut

**Files:**

- Modify: `regis/playbooks/default/playbook.yaml`
- Test: `tests/test_default_playbook_envelope.py`

### Comportement cible

- Ajout explicite de `dockle:severity-count`, `hadolint:severity-count`, `secrets:secret-scan`.
- Aucune des 6 heuristiques OCI ajoutée (elles restent des templates).
- Label `app.kubernetes.io/version` : 1.0.0 → 2.0.0.

- [ ] **Step 1 : Mettre à jour le test enveloppe**

Dans `tests/test_default_playbook_envelope.py`, remplacer :

```python
    assert pb["version"] == "1.0.0"
    assert any(r["slug"] == "cve-critical" for r in pb["rules"])
```

par :

```python
    assert pb["version"] == "2.0.0"
    assert any(r["slug"] == "cve-critical" for r in pb["rules"])
    # Security criteria previously auto-injected are now declared explicitly.
    declared_slugs = {r["slug"] for r in pb["rules"]}
    assert {"dockle-fatal", "hadolint-error", "secret-scan"} <= declared_slugs
    # OCI heuristics are NOT declared by the default playbook.
    assert "max-size" not in declared_slugs
    assert "layers-count" not in declared_slugs
```

- [ ] **Step 2 : Lancer le test, vérifier l'échec**

Run: `pipenv run pytest tests/test_default_playbook_envelope.py --no-cov -v`
Expected: FAIL (version 1.0.0 ≠ 2.0.0 ; slugs dockle-fatal/hadolint-error/secret-scan absents).

- [ ] **Step 3 : Bump du label de version**

Dans `regis/playbooks/default/playbook.yaml`, remplacer :

```yaml
labels:
  app.kubernetes.io/version: 1.0.0
```

par :

```yaml
labels:
  app.kubernetes.io/version: 2.0.0
```

- [ ] **Step 4 : Déclarer les 3 critères sécurité**

Dans la section `rules:`, juste après le bloc `# --- Security (Warning) ---` existant (après la règle `sbom:has-sbom`, slug `has-sbom`), insérer :

```yaml
# --- Container hygiene (Warning) — now explicit (were auto-injected) ---
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

- [ ] **Step 5 : Lancer le test enveloppe**

Run: `pipenv run pytest tests/test_default_playbook_envelope.py --no-cov -v`
Expected: PASS.

- [ ] **Step 6 : Valider le playbook par défaut**

Run: `pipenv run regis playbook validate regis/playbooks/default`
Expected: validation OK, aucune erreur de schéma.

- [ ] **Step 7 : Commit**

```bash
git add regis/playbooks/default/playbook.yaml tests/test_default_playbook_envelope.py
git commit -m "feat(playbook)!: make default playbook fully explicit

Declare dockle/hadolint severity + secret-scan (were auto-injected); drop
the 6 opinionated OCI heuristics from the default run. Bump default
playbook version 1.0.0 -> 2.0.0.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3 : Documentation + guide d'upgrade

**Files:**

- Modify: `docs/website/docs/concepts/rules.md`
- Modify: `docs/website/docs/concepts/analyzers.md`
- Modify: `docs/website/docs/reference/playbooks/default/index.md`
- Create: `docs/website/docs/upgrade/implicit-defaults-removal.md`

- [ ] **Step 1 : Réécrire la mécanique d'évaluation dans `concepts/rules.md`**

Remplacer (autour de la ligne 77) :

```markdown
1. **Collects default rules** from every analyzer that participated in the run.
2. **Merges playbook rules** on top — overriding defaults or instantiating new rules by binding a criterion.
```

par :

```markdown
1. **Builds the criterion catalogue** — the reusable, parameterized conditions
   shipped by every analyzer that participated in the run, plus the core
   `registry-domain-whitelist`. The catalogue is _not_ evaluated on its own.
2. **Resolves the playbook's declared rules** against that catalogue. The
   evaluated set is exactly what the playbook declares: there is no implicit
   inheritance of analyzer defaults.
```

- [ ] **Step 2 : Réécrire la section « Built-in default rules »**

Remplacer la section autour de la ligne 99 :

```markdown
## Built-in default rules

Each analyzer ships its own built-in rules, automatically activated when that
```

(et le paragraphe qui suit décrivant l'activation automatique) par :

```markdown
## The criterion catalogue

Each analyzer ships reusable **criterion templates** (e.g. `cve:cve-count`,
`oci:max-size`). These templates are a catalogue you bind from a playbook — they
are **never evaluated unless a playbook declares them**. To evaluate one, add a
rule under `spec.rules` that binds the criterion:
```

Conserver l'exemple `regis rules` qui suit (la commande reste un catalogue). Ajuster toute phrase environnante affirmant l'activation automatique.

- [ ] **Step 3 : Vérifier `concepts/analyzers.md`**

Run: `pipenv run grep -n "default\|auto\|built-in\|automatically" docs/website/docs/concepts/analyzers.md || grep -n "default\|auto\|built-in\|automatically" docs/website/docs/concepts/analyzers.md`
Si une phrase y affirme que les `default_criteria()` sont évaluées automatiquement, la corriger pour dire qu'elles forment un catalogue de templates résolus sur référence. (Si rien de tel, ne rien changer.)

- [ ] **Step 4 : Mettre à jour le tableau de référence du playbook par défaut**

Dans `docs/website/docs/reference/playbooks/default/index.md`, le tableau « Warning » liste un sous-jeu de règles. Y ajouter les 3 critères désormais explicites. Remplacer :

```markdown
| Slug            | Provider       | Description                                      |
| :-------------- | :------------- | :----------------------------------------------- |
| `cve-high`      | `cve`          | No more than 10 `HIGH` CVEs.                     |
| `cve-fixable`   | `cve`          | No unpatched CVEs with an available fix.         |
| `has-sbom`      | `sbom`         | Image must provide a Software Bill of Materials. |
| `scorecard-min` | `scorecarddev` | OpenSSF Scorecard score must be ≥ 5.0.           |
```

par :

```markdown
| Slug             | Provider       | Description                                      |
| :--------------- | :------------- | :----------------------------------------------- |
| `cve-high`       | `cve`          | No more than 10 `HIGH` CVEs.                     |
| `cve-fixable`    | `cve`          | No unpatched CVEs with an available fix.         |
| `has-sbom`       | `sbom`         | Image must provide a Software Bill of Materials. |
| `scorecard-min`  | `scorecarddev` | OpenSSF Scorecard score must be ≥ 5.0.           |
| `dockle-fatal`   | `dockle`       | No `FATAL` Dockle findings.                      |
| `hadolint-error` | `hadolint`     | No `error`-level Hadolint findings.              |
| `secret-scan`    | `secrets`      | No secrets detected (verified or not).           |
```

- [ ] **Step 5 : Créer le guide d'upgrade**

Créer `docs/website/docs/upgrade/implicit-defaults-removal.md` :

````markdown
---
title: Removal of implicit default-rule inheritance
sidebar_label: Implicit defaults removed
---

# Removal of implicit default-rule inheritance

**Breaking change.** Playbooks now evaluate **only the rules they declare**.
Previously, every analyzer's `default_criteria()` was auto-injected and evaluated
even when a playbook did not mention it. That implicit inheritance is gone:
`default_criteria()` is now a **catalogue of templates**, resolved only when a
playbook binds them via `criterion:`.

## What changed in the default playbook

Three security criteria that used to be auto-injected are now declared explicitly
and keep running by default:

- `dockle:severity-count` (slug `dockle-fatal`)
- `hadolint:severity-count` (slug `hadolint-error`)
- `secrets:secret-scan` (slug `secret-scan`)

Six opinionated OCI heuristics are **no longer evaluated by the default
playbook** (they remain available as templates you can bind yourself):

`oci:max-size`, `oci:layers-count`, `oci:platforms-count`,
`oci:exposed-ports-whitelist`, `oci:required-labels`, `oci:env-blacklist`.

The default playbook version label is bumped to `2.0.0` accordingly.

## Migrating your own playbook

If your playbook relied on analyzer defaults being applied automatically, declare
them explicitly. Discover what each analyzer offers with:

```bash
regis rules list
```

Then bind the criteria you want under `spec.rules`, for example:

```yaml
spec:
  rules:
    - provider: oci
      criterion: max-size
      slug: max-size
      level: warning
      options:
        max_mb: 1000
```

There is no automatic codemod: re-injecting former defaults would reintroduce the
heuristics the default playbook intentionally dropped.

````

- [ ] **Step 6 : Vérifier l'enregistrement du guide dans la navigation**

Run: `pipenv run cat docs/website/docs/upgrade/_category_.json || cat docs/website/docs/upgrade/_category_.json`
Si la sidebar est gérée par `_category_.json` (autogen), aucune action. Si une sidebar manuelle liste les guides, y ajouter `implicit-defaults-removal`.

- [ ] **Step 7 : Commit**

```bash
git add docs/website/docs/concepts/rules.md docs/website/docs/concepts/analyzers.md docs/website/docs/reference/playbooks/default/index.md docs/website/docs/upgrade/implicit-defaults-removal.md
git commit -m "docs(rules): document criteria catalogue + implicit-defaults removal

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
````

---

## Task 4 : Suite complète + linters

**Files:** aucun (vérification)

- [ ] **Step 1 : Suite complète avec couverture**

Run: `pipenv run pytest`
Expected: PASS, couverture ≥ 90 %. Diagnostiquer et corriger tout test ailleurs qui présupposait l'auto-injection (rechercher les usages de slugs OCI/dockle/hadolint dans `tests/` non couverts plus haut).

- [ ] **Step 2 : Lint + format**

Run: `pipenv run ruff check . && pipenv run ruff format --check .`
Expected: aucune erreur. Corriger au besoin (`ruff format .`).

- [ ] **Step 3 : Trunk**

Run: `trunk check`
Expected: aucun problème bloquant.

- [ ] **Step 4 : Commit final si des corrections ont été nécessaires**

```bash
git add -A
git commit -m "test(rules): align remaining tests with explicit-rules semantics

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-review (auteur du plan)

- **Couverture spec** : moteur + `regis rules` catalogue (Task 1) ✓ ; playbook curé + bump (Task 2) ✓ ; rupture + pas de codemod + schéma inchangé (Task 1/2/3) ✓ ; tests (Tasks 1-2-4) ✓ ; docs + guide d'upgrade (Task 3) ✓.
- **Cohérence des noms** : `get_criterion_templates` et `resolve_rules` utilisés à l'identique dans evaluator.py, commands/rules.py et les tests. Slugs du playbook par défaut (`dockle-fatal`, `hadolint-error`, `secret-scan`) identiques entre playbook et test enveloppe.
- **Pas de placeholder** : chaque étape de code montre le code exact ; les vérifications conditionnelles (analyzers.md, sidebar) bornent l'action attendue.
