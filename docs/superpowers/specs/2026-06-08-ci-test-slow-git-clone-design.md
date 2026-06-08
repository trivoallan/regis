# Spec — `ci-test.yml` ~10 min : le playbook par défaut clone le dépôt regis

- **Date** : 2026-06-08
- **Statut** : validé (design), implémenté
- **Type** : `fix` (cœur + tests) — corrige aussi un comportement runtime user-facing

## Problème

Le job `pytest` de `.github/workflows/ci-test.yml` prend **~590s** par run, alors
que la même suite tourne en **~12s en local**. L'écart n'est pas un coût
d'exécution : c'est une anomalie spécifique au runner CI.

## Cause racine (mesurée, reproduite)

Le playbook par défaut (`regis/playbooks/default/playbook.yaml`) déclarait un
template de présentation **par URL git** :

```yaml
presentation:
  templates:
    - url: https://github.com/trivoallan/regis
      directory: regis/cookiecutters/mr-evidence
```

`regis analyze` appelle `render_presentation_templates()` →
`cookiecutter(<url>)`. Comme l'URL est un dépôt git (`is_repo_url() == True`),
**Cookiecutter fait un `git clone` du dépôt regis entier** (un sous-processus)
— pour un template que regis **embarque déjà** dans son package
(`regis/cookiecutters/mr-evidence`). Autrement dit, regis se clone lui-même à
chaque analyse.

Sur le runner CI (cache cookiecutter froid, egress git lent/filtré), ce clone
**traîne ~25s par test** puis est avalé par un `except Exception` (« Warning:
Failed to render template ») → le test passe, mais après 25s. ~24 tests CLI
qui invoquent un `analyze` complet × ~25s ≈ ~600s.

### Pourquoi invisible en local

`~/.cookiecutters/regis` est **mis en cache** localement → Cookiecutter réutilise
le clone, pas d'accès réseau. Reproduction : en vidant ce cache, un seul test
analyze passe de **0,1s à 61s**.

### Fausses pistes écartées (preuves)

- **Réseau des analyzers / RegistryClient** : les tests lents mockent
  `RegistryClient` **et** `_discover_analyzers` → aucun analyzer réel.
- **pytest-socket** : un `git clone` est un sous-processus, **non blocable** par
  pytest-socket ; le blocage socket n'a rien changé au runtime.
- **Traceur de couverture** : CTracer (C) confirmé en CI ; ~2× en local, pas 50×.
- **DNS/retries** : `getaddrinfo` instantané, pas de retry/backoff dans
  `RegistryClient`.

## Décision

Référencer le template mr-evidence comme un **template packagé local** au lieu
d'un dépôt git distant. Résout la lenteur CI **et** rend chaque `regis analyze`
en production plus rapide et indépendant du réseau (plus d'auto-clone).

## Changements

1. **Schémas** (`playbook/v1alpha1/playbook.schema.json`,
   `playbook/result.schema.json`) : les entrées `templates` acceptent désormais
   `package` (paquet Python installé qui livre le template) **en alternative à**
   `url` (`anyOf` : `url` **ou** `package`). Champ `directory` réinterprété
   relativement à la racine du package quand `package` est fourni.
2. **`regis/playbook/presentation.py`** (`_resolve_template_conditions`) :
   propage `package` (et `url`) dans le template résolu injecté au rapport.
3. **`regis/utils/report.py`** (`render_presentation_templates`) : si `package`
   est présent, résout `importlib.resources.files(package) / directory` en chemin
   local et appelle `cookiecutter(<chemin local>)` (aucun `directory` kwarg,
   aucun clone). Le chemin `url` (templates distants tiers) reste supporté.
4. **`regis/playbooks/default/playbook.yaml`** : le template mr-evidence passe à
   `package: regis` + `directory: cookiecutters/mr-evidence`.
5. **`tests/conftest.py`** (nouveau) : fixture `autouse` qui **rejette tout
   clone distant** de Cookiecutter (`is_repo_url` → `RuntimeError`), tout en
   laissant passer les templates packagés/locaux. Filet anti-régression : aucun
   test ne doit plus cloner sur le réseau.
6. **`tests/test_presentation_templates.py`** (nouveau) : rendu local d'un
   template packagé (sans réseau) + garde anti-régression sur le playbook par
   défaut (aucun `url`, un `package`).

## Hors périmètre (non-objectifs)

- Pas de `pytest-socket` ni de blocage socket : sans rapport avec la cause (le
  clone est un sous-processus) ; la piste a été écartée.
- Pas de refonte du mécanisme de templates au-delà de l'ajout `package`.

## Vérification

- **Local, cache cookiecutter vidé** (simule un runner CI neuf) : suite complète
  **574 passed en ~12s** (vs un seul test à 61s avant le fix).
- **CI** : run `ci-test.yml` attendu **< ~90s** (vs ~590s).
- **Compat** : changement de schéma additif (`url` toujours accepté). Les
  playbooks tiers utilisant `url` continuent de fonctionner.

## Risques & mitigations

- **Un template tiers légitimement distant** → toujours possible via `url` ; le
  filet conftest ne s'applique qu'aux tests.
- **Résolution `package` sur install editable vs wheel** →
  `importlib.resources.files` gère les deux ; mr-evidence est packagé via
  `tool.setuptools.package-data` (`cookiecutters/**/*`).
