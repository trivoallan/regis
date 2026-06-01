# Plan d'implémentation — Format de playbook aligné sur les _kinds_ Kubernetes

> **Pour les workers agentiques :** SOUS-SKILL REQUISE : utiliser superpowers:subagent-driven-development (recommandé) ou superpowers:executing-plans pour exécuter ce plan tâche par tâche. Les étapes utilisent la syntaxe case à cocher (`- [ ]`) pour le suivi.

**Goal :** faire passer les playbooks Regis du format YAML à plat à l'enveloppe Kubernetes `apiVersion` / `kind` / `metadata` / `spec` (`apiVersion: regis.trivoallan.dev/v1alpha1`, `kind: Playbook`), sans changer la sémantique d'évaluation.

**Architecture :** rupture nette (l'entier `schemaVersion` disparaît, l'`apiVersion` string le remplace). Le loader parse l'enveloppe, valide contre un nouveau schéma `v1alpha1`, puis **normalise** le document en un dict aplati interne — les ~12 consommateurs (`evaluator`, `integrations/gitlab`, `commands/*`) restent inchangés (approche A). `regis playbook upgrade` convertit les bundles legacy.

**Tech Stack :** Python 3.11, `jsonschema` (Draft 2020-12) + `referencing`, `ruamel.yaml` (upgrade in-place), `click` (CLI), `pytest` (TDD, couverture ≥ 90 %), `cookiecutter` (scaffolding).

**Spec de référence :** [`docs/superpowers/specs/2026-06-01-playbook-kubernetes-kinds-design.md`](../../superpowers/specs/2026-06-01-playbook-kubernetes-kinds-design.md)

**Branche :** worktree existant `tritri/heuristic-kowalevski-d94f42`. Commit final attendu : `feat(playbook)!: …` (breaking, pré-v1 → bump mineur 0.33 → 0.34).

---

## Structure des fichiers

**Créés :**

- `regis/schemas/playbook/v1alpha1/__init__.py` — package vide (packaging).
- `regis/schemas/playbook/v1alpha1/playbook.schema.json` — schéma du _kind_ `Playbook` (enveloppe).
- `tests/test_playbook_schema_v1alpha1.py` — tests du schéma seul.

**Modifiés :**

- `regis/playbook/schema_registry.py` — clé `int` → clé `apiVersion` string.
- `regis/playbook/loader.py` — dispatch `apiVersion`/`kind` + `normalize_playbook()`.
- `regis/playbook/evaluator.py:197` — `schema_version` → `api_version`.
- `regis/commands/playbook.py` — `validate` (affichage) + `upgrade` (restructuration).
- `regis/playbooks/default/playbook.yaml` — migré vers l'enveloppe.
- `regis/cookiecutters/playbook/{{cookiecutter.project_slug}}/playbook.yaml` — réécrit (depuis `pages:`) en enveloppe.
- `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/playbook.yaml` — migré vers l'enveloppe.
- `tests/test_playbook_loader.py` + fixtures inline des autres tests playbook.
- `tests/commands/test_playbook_validate.py`, `tests/commands/test_playbook_upgrade.py`.
- Docs (`docs/website/docs/...`) + skill `/create-playbook`.

**Supprimés :**

- `regis/schemas/playbook/v1/definition.schema.json` + `regis/schemas/playbook/v1/__init__.py` (plus référencés après la rupture nette).

---

## Task 1 : Nouveau schéma `v1alpha1/playbook.schema.json`

**Files:**

- Create: `regis/schemas/playbook/v1alpha1/__init__.py`
- Create: `regis/schemas/playbook/v1alpha1/playbook.schema.json`
- Test: `tests/test_playbook_schema_v1alpha1.py`
- Référence (copie verbatim) : `regis/schemas/playbook/v1/definition.schema.json`

- [ ] **Step 1 : écrire le test qui échoue**

Créer `tests/test_playbook_schema_v1alpha1.py` :

```python
"""Tests du schéma Playbook v1alpha1 (enveloppe Kubernetes)."""

from __future__ import annotations

import importlib.resources
import json

import jsonschema
import pytest
from referencing import Registry, Resource


def _load_schema() -> dict:
    pkg = importlib.resources.files("regis.schemas.playbook.v1alpha1")
    return json.loads(pkg.joinpath("playbook.schema.json").read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load_schema()
    pb_root = importlib.resources.files("regis.schemas.playbook")
    jsonlogic = json.loads(
        pb_root.joinpath("jsonlogic.schema.json").read_text(encoding="utf-8")
    )
    registry = Registry().with_resources(
        [
            (schema["$id"], Resource.from_contents(schema)),
            ("../jsonlogic.schema.json", Resource.from_contents(jsonlogic)),
        ]
    )
    return jsonschema.Draft202012Validator(schema, registry=registry)


VALID = {
    "apiVersion": "regis.trivoallan.dev/v1alpha1",
    "kind": "Playbook",
    "metadata": {
        "name": "default",
        "title": "RegiS Default Playbook",
        "labels": {"app.kubernetes.io/version": "1.0.0"},
    },
    "spec": {
        "rules": [{"provider": "cve", "rule": "cve-count", "slug": "x", "level": "info"}]
    },
}


def test_valid_envelope_passes() -> None:
    _validator().validate(VALID)


def test_missing_kind_fails() -> None:
    doc = {k: v for k, v in VALID.items() if k != "kind"}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_bad_metadata_name_fails() -> None:
    doc = {**VALID, "metadata": {**VALID["metadata"], "name": "Invalid Name"}}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_missing_version_label_fails() -> None:
    doc = {**VALID, "metadata": {**VALID["metadata"], "labels": {}}}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_non_semver_version_label_fails() -> None:
    doc = {
        **VALID,
        "metadata": {**VALID["metadata"], "labels": {"app.kubernetes.io/version": "1.2"}},
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)


def test_additional_property_in_spec_fails() -> None:
    doc = {**VALID, "spec": {**VALID["spec"], "pages": []}}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(doc)
```

- [ ] **Step 2 : lancer le test, vérifier qu'il échoue**

Run: `pipenv run pytest tests/test_playbook_schema_v1alpha1.py -q --no-cov`
Expected: FAIL — `ModuleNotFoundError` / fichier `playbook.schema.json` absent.

- [ ] **Step 3 : créer le package et le schéma**

Créer `regis/schemas/playbook/v1alpha1/__init__.py` **vide**.

Créer `regis/schemas/playbook/v1alpha1/playbook.schema.json`. Partir du squelette ci-dessous, puis **copier verbatim** depuis l'ancien `regis/schemas/playbook/v1/definition.schema.json` les définitions de propriétés `rules`, `tiers`, `badges`, `integrations`, `links` (telles quelles, y compris leurs `$ref: "../jsonlogic.schema.json"` — le chemin reste correct, le fichier est à la même profondeur) à l'emplacement marqué dans `spec.properties`, ainsi que le `$def` `checklist_item` :

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://trivoallan.github.io/regis/schemas/playbook/v1alpha1/playbook.schema.json",
  "title": "playbook.v1alpha1.Playbook",
  "description": "Schema for regis Playbook resources (Kubernetes-style envelope).",
  "type": "object",
  "required": ["apiVersion", "kind", "metadata", "spec"],
  "additionalProperties": false,
  "properties": {
    "apiVersion": {
      "const": "regis.trivoallan.dev/v1alpha1",
      "description": "API group and version. Must equal 'regis.trivoallan.dev/v1alpha1'."
    },
    "kind": {
      "const": "Playbook",
      "description": "Resource kind. Must equal 'Playbook'."
    },
    "metadata": {
      "type": "object",
      "required": ["name", "labels"],
      "additionalProperties": false,
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
          "maxLength": 63,
          "description": "Machine identifier (RFC 1123 DNS label): lowercase alphanumerics and '-'."
        },
        "title": {
          "type": "string",
          "description": "Human-readable display name."
        },
        "description": {
          "type": "string",
          "description": "Human-readable description of what this playbook evaluates."
        },
        "labels": {
          "type": "object",
          "required": ["app.kubernetes.io/version"],
          "additionalProperties": { "type": "string" },
          "properties": {
            "app.kubernetes.io/version": {
              "type": "string",
              "pattern": "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$",
              "description": "SemVer of the playbook bundle (e.g. \"1.2.3\")."
            }
          }
        },
        "annotations": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Free-form non-identifying metadata."
        }
      }
    },
    "spec": {
      "type": "object",
      "additionalProperties": false,
      "description": "Playbook body: rules, tiers, badges, integrations, links.",
      "properties": {
        "__COPY_FROM_V1__": "rules, tiers, badges, integrations, links property definitions copied verbatim from v1/definition.schema.json — remove this placeholder key"
      }
    }
  },
  "$defs": {
    "__COPY_FROM_V1__": "checklist_item $def copied verbatim from v1/definition.schema.json — remove this placeholder key"
  }
}
```

> Après copie, **supprimer les deux clés `__COPY_FROM_V1__`**. Ne PAS recopier `pages`/`sections`/`sidebar` ni leurs `$defs` (`page`, `section`, `display`, `widget`, `level`, `scorecard`) : ils sont supprimés. Seul `checklist_item` survit dans `$defs` (référencé par `integrations.gitlab.checklists`).

- [ ] **Step 4 : lancer le test, vérifier qu'il passe**

Run: `pipenv run pytest tests/test_playbook_schema_v1alpha1.py -q --no-cov`
Expected: PASS (6 tests).

- [ ] **Step 5 : commit**

```bash
git add regis/schemas/playbook/v1alpha1/ tests/test_playbook_schema_v1alpha1.py
git commit -m "feat(playbook): add v1alpha1 Playbook JSON Schema (k8s envelope)"
```

---

## Task 2 : Registre de schémas indexé par `apiVersion`

**Files:**

- Modify: `regis/playbook/schema_registry.py` (intégralité)
- Test: `tests/test_schema_registry.py`

- [ ] **Step 1 : écrire le test qui échoue**

Créer `tests/test_schema_registry.py` :

```python
"""Tests du registre de schémas playbook (clé = apiVersion)."""

from __future__ import annotations

import pytest

from regis.playbook import schema_registry


def test_supported_versions_lists_v1alpha1() -> None:
    assert "regis.trivoallan.dev/v1alpha1" in schema_registry.supported_versions()


def test_get_schema_returns_playbook_kind() -> None:
    schema = schema_registry.get_schema("regis.trivoallan.dev/v1alpha1")
    assert schema["properties"]["kind"]["const"] == "Playbook"


def test_get_schema_unknown_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        schema_registry.get_schema("regis.trivoallan.dev/v9")
```

- [ ] **Step 2 : lancer le test, vérifier qu'il échoue**

Run: `pipenv run pytest tests/test_schema_registry.py -q --no-cov`
Expected: FAIL — `get_schema("regis.trivoallan.dev/v1alpha1")` lève `KeyError` (registre encore indexé par entier).

- [ ] **Step 3 : réécrire le registre**

Remplacer **tout** le corps après les imports de `regis/playbook/schema_registry.py` par :

```python
@functools.cache
def _load_schema_v1alpha1() -> dict[str, Any]:
    pkg = importlib.resources.files("regis.schemas.playbook.v1alpha1")
    text = pkg.joinpath("playbook.schema.json").read_text(encoding="utf-8")
    return json.loads(text)


_SCHEMAS: dict[str, Callable[[], dict[str, Any]]] = {
    "regis.trivoallan.dev/v1alpha1": _load_schema_v1alpha1,
}


def supported_versions() -> list[str]:
    """Return the sorted list of supported apiVersions."""
    return sorted(_SCHEMAS.keys())


def get_schema(api_version: str) -> dict[str, Any]:
    """Return the JSON Schema for *api_version*.

    Raises KeyError if the apiVersion is not supported.
    """
    try:
        loader = _SCHEMAS[api_version]
    except KeyError:
        raise KeyError(
            f"Unsupported apiVersion {api_version!r}. "
            f"Supported: {supported_versions()}."
        ) from None
    return loader()
```

- [ ] **Step 4 : lancer le test, vérifier qu'il passe**

Run: `pipenv run pytest tests/test_schema_registry.py -q --no-cov`
Expected: PASS (3 tests).

- [ ] **Step 5 : commit**

```bash
git add regis/playbook/schema_registry.py tests/test_schema_registry.py
git commit -m "feat(playbook): key schema registry by apiVersion string"
```

---

## Task 3 : Loader — dispatch `apiVersion`/`kind` + normalisation

**Files:**

- Modify: `regis/playbook/loader.py` (`load_playbook`, `_extract_schema_version`→`_extract_api_version`, `_get_schema_or_raise`, `_validate`, ajout `normalize_playbook`)
- Test: `tests/test_playbook_loader.py` (réécriture des fixtures + cas de version)

- [ ] **Step 1 : réécrire les tests (ils échoueront)**

Dans `tests/test_playbook_loader.py`, remplacer la constante `MINIMAL_PLAYBOOK` par l'enveloppe :

```python
MINIMAL_PLAYBOOK = {
    "apiVersion": "regis.trivoallan.dev/v1alpha1",
    "kind": "Playbook",
    "metadata": {
        "name": "bundle-playbook",
        "title": "Bundle Playbook",
        "labels": {"app.kubernetes.io/version": "1.0.0"},
    },
    "spec": {
        "rules": [
            {"provider": "cve", "rule": "cve-count", "slug": "always", "level": "info"}
        ]
    },
}
```

Dans `TestLoadPlaybookBundle`, remplacer l'assertion `assert len(loaded["sections"][0]["scorecards"]) == 1` (test `test_load_from_bundle_directory`) par :

```python
        assert loaded["slug"] == "bundle-playbook"
        assert loaded["version"] == "1.0.0"
        assert loaded["rules"][0]["slug"] == "always"
```

Remplacer les fonctions de test de version (de `test_loads_valid_v1_playbook` jusqu'à la fin du fichier) par :

```python
def test_loads_valid_envelope(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n"
        "  name: valid\n"
        "  title: Valid Playbook\n"
        "  labels:\n"
        '    app.kubernetes.io/version: "1.0.0"\n'
        "spec: {}\n"
    )
    pb = load_playbook(_write(tmp_path, content))
    assert pb["apiVersion"] == "regis.trivoallan.dev/v1alpha1"
    assert pb["kind"] == "Playbook"
    assert pb["name"] == "Valid Playbook"  # ← metadata.title
    assert pb["slug"] == "valid"  # ← metadata.name
    assert pb["version"] == "1.0.0"  # ← label


def test_name_falls_back_to_metadata_name_when_no_title(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n"
        "  name: no-title\n"
        "  labels:\n"
        '    app.kubernetes.io/version: "1.0.0"\n'
        "spec: {}\n"
    )
    pb = load_playbook(_write(tmp_path, content))
    assert pb["name"] == "no-title"


def test_missing_api_version_raises(tmp_path) -> None:
    content = "kind: Playbook\nmetadata:\n  name: x\nspec: {}\n"
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    msg = str(exc.value)
    assert "apiVersion" in msg
    assert "Add `apiVersion: regis.trivoallan.dev/v1alpha1`" in msg


def test_wrong_kind_raises(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: RuleSet\n"
        "metadata:\n  name: x\nspec: {}\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "expected 'Playbook'" in str(exc.value)


def test_unknown_api_version_raises(tmp_path) -> None:
    content = (
        "apiVersion: regis.trivoallan.dev/v9\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\nspec: {}\n"
    )
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    msg = str(exc.value)
    assert "apiVersion=" in msg
    assert "regis playbook upgrade" in msg


def test_legacy_flat_format_rejected(tmp_path) -> None:
    content = 'schemaVersion: 1\nversion: "1.0.0"\nname: Legacy\n'
    with pytest.raises(PlaybookVersionError) as exc:
        load_playbook(_write(tmp_path, content))
    assert "apiVersion" in str(exc.value)


def test_missing_version_label_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\n  labels: {}\n"
        "spec: {}\n"
    )
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))


def test_invalid_semver_label_fails_schema_validation(tmp_path) -> None:
    import jsonschema

    content = (
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\n  labels:\n"
        '    app.kubernetes.io/version: "1.2"\n'
        "spec: {}\n"
    )
    with pytest.raises(jsonschema.ValidationError):
        load_playbook(_write(tmp_path, content))
```

- [ ] **Step 2 : lancer les tests, vérifier qu'ils échouent**

Run: `pipenv run pytest tests/test_playbook_loader.py -q --no-cov`
Expected: FAIL (le loader lit encore `schemaVersion`, l'enveloppe est rejetée).

- [ ] **Step 3 : réécrire le loader**

Dans `regis/playbook/loader.py` :

(a) Remplacer le corps de `load_playbook` :

```python
def load_playbook(path: str | Path) -> dict[str, Any]:
    """Load and validate a playbook from a file, bundle dir, or URL."""
    raw = _read_raw(path)
    api_version = _extract_api_version(raw, path)
    schema = _get_schema_or_raise(api_version, path)
    _validate(raw, schema, path, api_version)
    return normalize_playbook(raw)
```

(b) Remplacer `_extract_schema_version` par :

```python
def _extract_api_version(raw: dict[str, Any], path: str | Path) -> str:
    if "apiVersion" not in raw:
        raise PlaybookVersionError(
            f"playbook '{path}' is missing required field 'apiVersion'.\n"
            f"Add `apiVersion: regis.trivoallan.dev/v1alpha1` and `kind: Playbook` "
            f"at the top of the file (run `regis playbook upgrade` to migrate a "
            f"legacy playbook).\n"
            f"Supported: {schema_registry.supported_versions()}."
        )
    api_version = raw["apiVersion"]
    if not isinstance(api_version, str):
        raise PlaybookVersionError(
            f"playbook '{path}' has an invalid apiVersion: {api_version!r} "
            f"must be a string.\n"
            f"Supported: {schema_registry.supported_versions()}."
        )
    kind = raw.get("kind")
    if kind != "Playbook":
        raise PlaybookVersionError(
            f"playbook '{path}' has kind={kind!r}; expected 'Playbook'."
        )
    return api_version
```

(c) Remplacer `_get_schema_or_raise` :

```python
def _get_schema_or_raise(api_version: str, path: str | Path) -> dict[str, Any]:
    try:
        return schema_registry.get_schema(api_version)
    except KeyError:
        from importlib.metadata import version as _pkg_version

        raise PlaybookVersionError(
            f"playbook '{path}' declares apiVersion={api_version!r} but this "
            f"regis (v{_pkg_version('regis')}) only supports "
            f"{schema_registry.supported_versions()}. "
            f"Upgrade regis or run `regis playbook upgrade`."
        ) from None
```

(d) Modifier la signature et le message de `_validate` :

```python
def _validate(
    raw: dict[str, Any],
    schema: dict[str, Any],
    path: str | Path,
    api_version: str,
) -> None:
    registry = _build_validator_registry(schema)
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    try:
        validator.validate(raw)
    except jsonschema.ValidationError as exc:
        exc.message = (
            f"playbook '{path}' failed validation against apiVersion={api_version}: "
            f"{exc.message}"
        )
        raise
```

(e) Ajouter `normalize_playbook` (par exemple juste après `load_playbook`) :

```python
def normalize_playbook(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten the envelope into the internal shape consumers expect.

    Projects ``metadata``/``spec`` back onto the historical top-level keys
    (``name``, ``slug``, ``version``, ``description`` + ``spec.*``) so the
    evaluator, integrations and report code need no changes.
    """
    meta = raw.get("metadata", {})
    spec = raw.get("spec", {})
    labels = meta.get("labels", {})
    return {
        "apiVersion": raw["apiVersion"],
        "kind": raw["kind"],
        "metadata": meta,
        "spec": spec,
        "name": meta.get("title") or meta.get("name"),
        "slug": meta.get("name"),
        "version": labels.get("app.kubernetes.io/version"),
        "description": meta.get("description"),
        **spec,
    }
```

- [ ] **Step 4 : lancer les tests, vérifier qu'ils passent**

Run: `pipenv run pytest tests/test_playbook_loader.py -q --no-cov`
Expected: PASS.

- [ ] **Step 5 : commit**

```bash
git add regis/playbook/loader.py tests/test_playbook_loader.py
git commit -m "feat(playbook)!: dispatch on apiVersion/kind and normalize the envelope"
```

---

## Task 4 : Rapport — `schema_version` → `api_version`

**Files:**

- Modify: `regis/playbook/evaluator.py:197`
- Test: `tests/test_playbook_engine.py` (ajout d'un test ciblé)

- [ ] **Step 1 : écrire le test qui échoue**

Ajouter à `tests/test_playbook_engine.py` :

```python
def test_evaluate_propagates_api_version() -> None:
    from regis.playbook.evaluator import evaluate

    playbook = {
        "apiVersion": "regis.trivoallan.dev/v1alpha1",
        "kind": "Playbook",
        "name": "X",
        "version": "1.0.0",
        "rules": [],
    }
    result = evaluate(playbook, {"analyzers": {}})
    assert result["api_version"] == "regis.trivoallan.dev/v1alpha1"
    assert result["playbook_version"] == "1.0.0"
    assert "schema_version" not in result
```

- [ ] **Step 2 : lancer le test, vérifier qu'il échoue**

Run: `pipenv run pytest tests/test_playbook_engine.py::test_evaluate_propagates_api_version -q --no-cov`
Expected: FAIL — `result` contient encore `schema_version` (= `None`) et pas `api_version`.

- [ ] **Step 3 : modifier l'évaluateur**

Dans `regis/playbook/evaluator.py`, remplacer la ligne 197 :

```python
        "schema_version": playbook.get("schemaVersion"),
```

par :

```python
        "api_version": playbook.get("apiVersion"),
```

- [ ] **Step 4 : lancer le test, vérifier qu'il passe**

Run: `pipenv run pytest tests/test_playbook_engine.py::test_evaluate_propagates_api_version -q --no-cov`
Expected: PASS.

- [ ] **Step 5 : commit**

```bash
git add regis/playbook/evaluator.py tests/test_playbook_engine.py
git commit -m "feat(playbook)!: record api_version instead of schema_version in report"
```

---

## Task 5 : `regis playbook validate` — sortie mise à jour

**Files:**

- Modify: `regis/commands/playbook.py` (`validate_playbook`, lignes 47-50)
- Test: `tests/commands/test_playbook_validate.py`

- [ ] **Step 1 : écrire le test qui échoue**

Ajouter à `tests/commands/test_playbook_validate.py` (adapter le helper d'écriture de bundle existant si présent ; sinon écrire le fichier directement) :

```python
def test_validate_prints_api_version(tmp_path) -> None:
    from click.testing import CliRunner

    from regis.commands.playbook import playbook_group

    pb = tmp_path / "playbook.yaml"
    pb.write_text(
        "apiVersion: regis.trivoallan.dev/v1alpha1\n"
        "kind: Playbook\n"
        "metadata:\n  name: x\n  labels:\n"
        '    app.kubernetes.io/version: "1.0.0"\n'
        "spec: {}\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(playbook_group, ["validate", str(pb)])
    assert result.exit_code == 0
    assert "regis.trivoallan.dev/v1alpha1" in result.output
    assert "Playbook" in result.output
```

- [ ] **Step 2 : lancer le test, vérifier qu'il échoue**

Run: `pipenv run pytest tests/commands/test_playbook_validate.py::test_validate_prints_api_version -q --no-cov`
Expected: FAIL — `validate` accède à `playbook['schemaVersion']` (KeyError) sur l'enveloppe normalisée.

- [ ] **Step 3 : modifier la commande**

Dans `regis/commands/playbook.py`, remplacer le bloc final de `validate_playbook` (lignes ~47-50) :

```python
    click.echo(
        f"  ✓ {path} is valid (schemaVersion={playbook['schemaVersion']}, "
        f"version={playbook['version']})."
    )
```

par :

```python
    click.echo(
        f"  ✓ {path} is valid (apiVersion={playbook['apiVersion']}, "
        f"kind={playbook['kind']}, version={playbook.get('version')})."
    )
```

- [ ] **Step 4 : lancer le test, vérifier qu'il passe**

Run: `pipenv run pytest tests/commands/test_playbook_validate.py -q --no-cov`
Expected: PASS (vérifier qu'aucun ancien test du fichier ne dépend du format à plat ; sinon migrer ses fixtures vers l'enveloppe).

- [ ] **Step 5 : commit**

```bash
git add regis/commands/playbook.py tests/commands/test_playbook_validate.py
git commit -m "feat(playbook): print apiVersion/kind in playbook validate output"
```

---

## Task 6 : `regis playbook upgrade` — restructuration en enveloppe

**Files:**

- Modify: `regis/commands/playbook.py` (`upgrade_playbook`, intégralité)
- Test: `tests/commands/test_playbook_upgrade.py`

- [ ] **Step 1 : écrire les tests qui échouent**

Remplacer le contenu de `tests/commands/test_playbook_upgrade.py` par :

```python
"""Tests de `regis playbook upgrade` (legacy plat → enveloppe k8s)."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from regis.commands.playbook import playbook_group
from regis.playbook.loader import load_playbook


def _run(path) -> str:
    result = CliRunner().invoke(playbook_group, ["upgrade", str(path)])
    assert result.exit_code == 0, result.output
    return result.output


def test_upgrade_flat_to_envelope(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text(
        "schemaVersion: 1\n"
        'version: "2.1.0"\n'
        "name: My Playbook\n"
        "slug: my-pb\n"
        "rules:\n"
        "  - provider: cve\n"
        "    rule: cve-count\n"
        "    slug: c\n"
        "    level: info\n",
        encoding="utf-8",
    )
    _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert data["apiVersion"] == "regis.trivoallan.dev/v1alpha1"
    assert data["kind"] == "Playbook"
    assert data["metadata"]["name"] == "my-pb"
    assert data["metadata"]["title"] == "My Playbook"
    assert data["metadata"]["labels"]["app.kubernetes.io/version"] == "2.1.0"
    assert data["spec"]["rules"][0]["slug"] == "c"
    # Le résultat est rechargeable et valide.
    assert load_playbook(pb)["name"] == "My Playbook"


def test_upgrade_slugifies_name_when_no_slug(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text("name: My Cool Playbook\nrules: []\n", encoding="utf-8")
    _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert data["metadata"]["name"] == "my-cool-playbook"
    assert data["metadata"]["labels"]["app.kubernetes.io/version"] == "1.0.0"


def test_upgrade_drops_deprecated_pages(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text(
        "name: P\nslug: p\npages:\n  - title: Overview\n    sections: []\n",
        encoding="utf-8",
    )
    out = _run(pb)
    data = yaml.safe_load(pb.read_text(encoding="utf-8"))
    assert "pages" not in data and "pages" not in data.get("spec", {})
    assert "Dropped deprecated: pages" in out


def test_upgrade_is_idempotent(tmp_path) -> None:
    pb = tmp_path / "playbook.yaml"
    pb.write_text("name: P\nslug: p\nrules: []\n", encoding="utf-8")
    _run(pb)
    first = pb.read_text(encoding="utf-8")
    out = _run(pb)
    assert pb.read_text(encoding="utf-8") == first
    assert "nothing to do" in out
```

- [ ] **Step 2 : lancer les tests, vérifier qu'ils échouent**

Run: `pipenv run pytest tests/commands/test_playbook_upgrade.py -q --no-cov`
Expected: FAIL — l'`upgrade` actuel injecte seulement `schemaVersion`/`version`, ne crée pas l'enveloppe.

- [ ] **Step 3 : réécrire la commande `upgrade`**

Dans `regis/commands/playbook.py`, remplacer **toute** la fonction `upgrade_playbook` (et sa docstring) par :

```python
@playbook_group.command(name="upgrade")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def upgrade_playbook(path: Path) -> None:
    """Convert a legacy flat playbook into the apiVersion/kind/metadata/spec envelope.

    Idempotent: if the document already declares an ``apiVersion`` it is left
    untouched. Deprecated ``pages``/``sections``/``sidebar`` are dropped.
    """
    import re

    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(path, encoding="utf-8") as f:
        data = yaml.load(f)

    if data is None:
        raise click.ClickException(
            f"{path}: file is empty or not a valid YAML document."
        )

    if "apiVersion" in data:
        click.echo(
            f"  {path}: already uses the apiVersion/kind envelope, nothing to do."
        )
        return

    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
        return slug or "playbook"

    display_name = data.get("name")
    slug = data.get("slug") or (_slugify(display_name) if display_name else "playbook")
    version = data.get("version") or "1.0.0"

    metadata = CommentedMap()
    metadata["name"] = slug
    if display_name:
        metadata["title"] = display_name
    if data.get("description"):
        metadata["description"] = data["description"]
    labels = CommentedMap()
    labels["app.kubernetes.io/version"] = version
    metadata["labels"] = labels

    spec = CommentedMap()
    for key in ("tiers", "rules", "badges", "integrations", "links"):
        if key in data:
            spec[key] = data[key]

    dropped = [k for k in ("pages", "sections", "sidebar") if k in data]

    new_doc = CommentedMap()
    new_doc["apiVersion"] = "regis.trivoallan.dev/v1alpha1"
    new_doc["kind"] = "Playbook"
    new_doc["metadata"] = metadata
    new_doc["spec"] = spec

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(new_doc, f)

    msg = f"  Upgraded {path} to the apiVersion/kind envelope."
    if dropped:
        msg += f" Dropped deprecated: {', '.join(dropped)}."
    click.echo(msg)
```

> Note : la restructuration complète ne préserve pas les commentaires inline (acceptable pour une migration ponctuelle). Les imports `DoubleQuotedScalarString` devenus inutiles sont retirés de fait (ils étaient locaux à la fonction).

- [ ] **Step 4 : lancer les tests, vérifier qu'ils passent**

Run: `pipenv run pytest tests/commands/test_playbook_upgrade.py -q --no-cov`
Expected: PASS (4 tests).

- [ ] **Step 5 : commit**

```bash
git add regis/commands/playbook.py tests/commands/test_playbook_upgrade.py
git commit -m "feat(playbook)!: upgrade restructures legacy playbooks into the envelope"
```

---

## Task 7 : Migrer le playbook par défaut + les cookiecutters

**Files:**

- Modify: `regis/playbooks/default/playbook.yaml`
- Modify: `regis/cookiecutters/playbook/{{cookiecutter.project_slug}}/playbook.yaml`
- Modify: `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/playbook.yaml`
- Test: `tests/test_default_playbook_envelope.py` (nouveau) + suites bootstrap existantes

- [ ] **Step 1 : écrire le test qui échoue**

Créer `tests/test_default_playbook_envelope.py` :

```python
"""Le playbook par défaut livré est au format enveloppe et chargeable."""

from __future__ import annotations

import importlib.resources

from regis.playbook.loader import load_playbook


def test_default_playbook_loads_as_envelope() -> None:
    path = importlib.resources.files("regis.playbooks.default").joinpath("playbook.yaml")
    with importlib.resources.as_file(path) as p:
        pb = load_playbook(p)
    assert pb["apiVersion"] == "regis.trivoallan.dev/v1alpha1"
    assert pb["kind"] == "Playbook"
    assert pb["slug"] == "default"
    assert pb["version"] == "1.0.0"
    # Sémantique préservée : les règles et tiers sont toujours là.
    assert any(r["slug"] == "cve-critical" for r in pb["rules"])
    assert [t["name"] for t in pb["tiers"]] == ["Gold", "Silver", "Bronze"]
```

- [ ] **Step 2 : lancer le test, vérifier qu'il échoue**

Run: `pipenv run pytest tests/test_default_playbook_envelope.py -q --no-cov`
Expected: FAIL — le défaut est encore au format à plat (rejeté par le loader).

- [ ] **Step 3 : migrer le playbook par défaut**

Remplacer l'en-tête de `regis/playbooks/default/playbook.yaml` (lignes 1-4) par l'enveloppe, et **indenter** tout le reste (`tiers`, `rules`, `badges`, `integrations`, `links`) de 2 espaces sous `spec:` :

```yaml
# yaml-language-server: $schema=../../schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: default
  title: RegiS Default Playbook
  labels:
    app.kubernetes.io/version: "1.0.0"
spec:
  tiers:
    - name: Gold
      condition:
        ">": [{ var: rules_summary.score }, 90]
    # … (reste des tiers/rules/badges/integrations/links existants, indentés de 2 espaces)
```

> Le corps (`tiers`…`links`) est repris **verbatim** depuis l'actuel fichier, simplement décalé de 2 espaces sous `spec:`. Ne rien changer aux règles/conditions.

- [ ] **Step 4 : migrer le cookiecutter `playbook/`**

Remplacer **tout** le contenu de `regis/cookiecutters/playbook/{{cookiecutter.project_slug}}/playbook.yaml` par :

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/trivoallan/regis/main/regis/schemas/playbook/v1alpha1/playbook.schema.json
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: "{{ cookiecutter.project_slug }}"
  title: "{{ cookiecutter.project_name }}"
  description: "{{ cookiecutter.description }}"
  labels:
    app.kubernetes.io/version: "1.0.0"
spec:
  tiers:
    - name: Gold
      condition:
        ">": [{ var: rules_summary.score }, 90]
    - name: Silver
      condition:
        ">": [{ var: rules_summary.score }, 70]
    - name: Bronze
      condition:
        ">": [{ var: rules_summary.score }, 50]
  rules:
    - provider: cve
      rule: cve-count
      slug: cve-critical
      level: critical
      options:
        level: critical
        max_count: 0
    - provider: sbom
      rule: has-sbom
      slug: has-sbom
      level: warning
```

- [ ] **Step 5 : migrer le cookiecutter `gitlab-ci/`**

Dans `regis/cookiecutters/gitlab-ci/{{cookiecutter.project_slug}}/playbook.yaml`, remplacer les lignes 1-5 (commentaires + `name:`) par l'enveloppe, puis indenter `tiers`/`rules`/`badges`/`integrations`/`links` de 2 espaces sous `spec:` :

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/trivoallan/regis/main/regis/schemas/playbook/v1alpha1/playbook.schema.json
# Regis Playbook — {{ cookiecutter.project_name }}
# Scaffolded by: regis bootstrap gitlab-ci
# Docs: https://trivoallan.github.io/regis/docs/concepts/playbooks
apiVersion: regis.trivoallan.dev/v1alpha1
kind: Playbook
metadata:
  name: "{{ cookiecutter.project_slug }}"
  title: "{{ cookiecutter.project_name }}"
  labels:
    app.kubernetes.io/version: "1.0.0"
spec:
  tiers:
    - name: Gold
      condition:
        ">": [{ var: rules_summary.score }, 90]
    # … (reste des tiers/rules/badges/integrations/links existants, indentés de 2 espaces)
```

- [ ] **Step 6 : lancer les tests concernés, vérifier qu'ils passent**

Run: `pipenv run pytest tests/test_default_playbook_envelope.py tests/test_bootstrap.py tests/test_bootstrap_gitlab_ci.py -q --no-cov`
Expected: PASS. Si un test bootstrap valide le playbook scaffoldé contre l'ancien format ou l'ancien `$schema`, migrer son attendu.

- [ ] **Step 7 : commit**

```bash
git add regis/playbooks/default/playbook.yaml regis/cookiecutters/ tests/test_default_playbook_envelope.py
git commit -m "feat(playbook)!: migrate default playbook and cookiecutters to the envelope"
```

---

## Task 8 : Migrer les fixtures inline restantes + supprimer le schéma v1

**Files:**

- Modify: fixtures inline dans `tests/test_playbook_engine.py`, `tests/test_coverage_engine.py`, `tests/test_remote_playbook.py`, `tests/test_analyze_rerun.py`, `tests/test_utils_report.py`, `tests/test_cli.py` (et tout autre détecté)
- Delete: `regis/schemas/playbook/v1/`

- [ ] **Step 1 : lancer la suite complète, recenser les échecs**

Run: `pipenv run pytest -q --no-cov`
Expected: échecs concentrés sur les tests portant des playbooks inline au format à plat (`schemaVersion`/`name`/`sections`/`pages`).

- [ ] **Step 2 : migrer chaque fixture inline**

Pour chaque playbook inline en format plat, appliquer la même transformation (dict ou YAML) :

- ajouter `"apiVersion": "regis.trivoallan.dev/v1alpha1"`, `"kind": "Playbook"` ;
- déplacer `name`→`metadata.title`, `slug`→`metadata.name` (ou slugifier), `version`→`metadata.labels["app.kubernetes.io/version"]` ;
- déplacer `rules`/`tiers`/`badges`/`integrations`/`links` sous `spec` ;
- supprimer `pages`/`sections`.

> Astuce : les tests appelant **directement** `evaluate(playbook, report)` (et non `load_playbook`) peuvent garder la forme **aplatie** (`name`/`version`/`rules` au top-level) — c'est exactement ce que `normalize_playbook` produit. Seuls les tests qui passent par `load_playbook`/`validate`/fichiers exigent l'enveloppe complète.

- [ ] **Step 3 : supprimer l'ancien schéma v1**

```bash
git rm -r regis/schemas/playbook/v1
```

Vérifier qu'aucune référence ne subsiste :

Run: `grep -rn "playbook/v1/\|definition.schema.json\|_load_schema_v1\b" regis/ tests/`
Expected: aucun résultat.

- [ ] **Step 4 : suite complète + couverture**

Run: `pipenv run pytest -q`
Expected: PASS, couverture ≥ 90 %.

- [ ] **Step 5 : commit**

```bash
git add -A
git commit -m "test(playbook): migrate inline fixtures and drop v1 schema"
```

---

## Task 9 : Documentation + skill `/create-playbook`

**Files:**

- Modify: docs playbooks sous `docs/website/docs/` (concepts + référence)
- Modify: le template/skill de génération `/create-playbook`

- [ ] **Step 1 : repérer les exemples à jour**

Run: `grep -rln "schemaVersion\|^name:\|pages:\|sections:" docs/website/docs`
Run: `grep -rln "schemaVersion\|playbook.yaml" .claude/skills 2>/dev/null; ls .claude/skills 2>/dev/null`
Expected : liste des fichiers de doc/skill mentionnant l'ancien format.

- [ ] **Step 2 : réécrire les exemples de doc**

Dans chaque page concernée, remplacer les blocs YAML par l'enveloppe (`apiVersion`/`kind`/`metadata`/`spec`) et mettre à jour la table des champs (mapping de la spec, section « Règles de mapping »). Mentionner `regis playbook upgrade` pour migrer.

- [ ] **Step 3 : mettre à jour le skill `/create-playbook`**

Faire générer au skill un bundle au format enveloppe : `metadata.name` = slug saisi, `metadata.title` = nom, `metadata.labels["app.kubernetes.io/version"] = "1.0.0"`, règles sous `spec.rules`. Vérifier que le `meta.schema.json` du bundle (métadonnées projet) reste inchangé — il est distinct du schéma du playbook.

- [ ] **Step 4 : vérifier qu'un playbook documenté est valide**

Copier un exemple de la doc dans un fichier temporaire et le valider :

Run: `pipenv run regis playbook validate /tmp/example-playbook.yaml`
Expected: `✓ … is valid (apiVersion=regis.trivoallan.dev/v1alpha1, kind=Playbook, version=1.0.0).`

- [ ] **Step 5 : commit**

```bash
git add docs/ .claude/
git commit -m "docs(playbook): document the apiVersion/kind playbook format"
```

---

## Task 10 : Vérifications finales + lint

**Files:** —

- [ ] **Step 1 : vérifier l'absence de fuite de `schema_version` dans le contrat rapport**

Run: `grep -rn "schema_version\|schemaVersion" regis/ | grep -v "schemas/playbook/v1alpha1"`
Inspecter chaque occurrence. Confirmer que :

- le `schemaVersion` **entier du `report.json`** (contrat dashboard, `REPORT_SCHEMA_VERSION` dans `regis/utils/report.py`) est **intact** ;
- plus aucune lecture de `playbook.get("schemaVersion")` ne subsiste ;
- aucune règle JSON Logic du playbook par défaut ne référence `var: schema_version`.

- [ ] **Step 2 : lint + format**

Run: `pipenv run ruff check . && pipenv run ruff format --check .`
Expected: clean (sinon `ruff format .` puis recommit).

- [ ] **Step 3 : suite complète + couverture (gate CI)**

Run: `pipenv run pytest`
Expected: PASS, couverture ≥ 90 %.

- [ ] **Step 4 : commit de clôture (si lint a produit des changements)**

```bash
git add -A
git commit -m "chore(playbook): lint and format the k8s-envelope migration"
```

> Le caractère breaking (`feat(playbook)!:`) est déjà porté par les commits des Tasks 3/4/6/7 ; release-please bumpera 0.33 → 0.34 (`bump-minor-pre-major`).

---

## Auto-revue (effectuée à la rédaction)

**1. Couverture de la spec :**

- Format cible + mapping → Tasks 1, 3, 7. ✓
- Nettoyages (drop `pages`/`sections`/`sidebar`, fix `$schema`) → Tasks 1 (schéma), 6 (upgrade), 7 (fichiers). ✓
- Schéma & nommage (`v1alpha1/playbook.schema.json`, registre par apiVersion) → Tasks 1, 2. ✓
- Normalisation (approche A) → Task 3. ✓
- `upgrade`/`validate` → Tasks 5, 6. ✓
- Propagation rapport (`api_version`) → Task 4. ✓
- Fichiers à migrer + tests → Tasks 7, 8. ✓
- Docs & skill → Task 9. ✓
- Points « à vérifier au plan » (fuite `schema_version`, distinction report schemaVersion, `--rules` hors périmètre) → Task 10 + note. ✓

**2. Placeholders :** les `__COPY_FROM_V1__` sont des marqueurs explicites avec instruction de suppression ; les `# … (reste …)` désignent un corps repris verbatim d'un fichier source identifié — pas du contenu manquant. Aucun `TODO`/`TBD`. ✓

**3. Cohérence des types/noms :** `apiVersion` (string), `kind == "Playbook"`, `normalize_playbook`, `get_schema(api_version)`, `supported_versions() -> list[str]`, champ rapport `api_version` — cohérents entre toutes les tâches. ✓

**Hors périmètre confirmé :** le fichier d'override `--rules` (liste de règles nue) n'est pas un _kind_ `Playbook` → inchangé.
