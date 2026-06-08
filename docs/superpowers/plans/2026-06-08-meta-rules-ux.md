# UX du `meta` dans les règles — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Faire du `metadata.*` un namespace de première classe pour les règles : helpers JSON Logic ergonomiques, absence de meta testable sans `incomplete`, emplacement report unique documenté, et validation well-known qui fonctionne réellement.

**Architecture:** Cinq changements indépendants puis un volet doc. (1) Des prédicats purs partagés (`regis/utils/predicates.py`) alimentent à la fois de nouveaux opérateurs JSON Logic et le format-checker du schéma. (2) `MissingDataTracker` exempte le namespace `metadata.*` du marquage `incomplete`. (3) Le schéma well-known passe en structure imbriquée (cohérente avec le meta réellement stocké) et `MetadataAnalyzer` est retravaillé en conséquence. (4) Le report cesse de dupliquer le meta : top-level `metadata.*` devient l'unique emplacement (`request.metadata` retiré), `REPORT_SCHEMA_VERSION` 2 → 3.

**Tech Stack:** Python 3.11, `json-logic-qubit`, `jsonschema` (Draft 2020-12), pytest. Spec : `docs/superpowers/specs/2026-06-08-meta-rules-ux-design.md`.

**Référence de commandes :** `pipenv run pytest --no-cov <path>` pour la boucle rapide ; `pipenv run pytest` (couverture ≥ 90 %) avant PR ; `pipenv run ruff format . && pipenv run ruff check .` avant chaque commit.

---

## File Structure

| Fichier                                                  | Rôle                                                                                            | Action                                                 |
| :------------------------------------------------------- | :---------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
| `regis/utils/predicates.py`                              | Prédicats purs (truthy/falsy/url/empty/matches), sans dépendance json_logic                     | **Créer**                                              |
| `regis/rules/evaluator.py`                               | Enregistre les prédicats comme opérateurs JSON Logic                                            | Modifier (`_add_custom_operations`)                    |
| `regis/playbook/context.py`                              | `MissingDataTracker` : exemption namespace `metadata.*`                                         | Modifier                                               |
| `regis/schemas/meta/well-known.schema.json`              | Schéma meta well-known                                                                          | Réécrire (imbriqué)                                    |
| `regis/analyzers/metadata.py`                            | Validation meta : schéma imbriqué + format `uri` réel + `metadata_validation` par chemin pointé | Réécrire `analyze()` + helpers                         |
| `regis/schemas/report/report.schema.json`                | Enveloppe report                                                                                | Modifier (retrait `request.metadata`)                  |
| `regis/commands/analyze.py`                              | Producteur report                                                                               | Modifier (2 sites : ne plus écrire `request.metadata`) |
| `regis/utils/report.py`                                  | `REPORT_SCHEMA_VERSION`                                                                         | Modifier (2 → 3)                                       |
| `tests/fixtures/report.v3.json`                          | Fixture contrat v3                                                                              | **Créer**                                              |
| `tests/test_predicates.py`                               | Tests unitaires prédicats purs                                                                  | **Créer**                                              |
| `tests/test_rules_evaluator.py`                          | Opérateurs via json_logic + exemption namespace + e2e                                           | Modifier (ajouts)                                      |
| `tests/test_analyzer_metadata.py`                        | Validation imbriquée + format uri                                                               | Réécrire                                               |
| `tests/test_report_schema_version.py`                    | Bump version + rejet `request.metadata` + fixture v3                                            | Modifier                                               |
| `tests/test_gh_env.py`                                   | Assert `request.metadata` absent                                                                | Modifier (1 assert)                                    |
| `docs/website/docs/concepts/rules.md`                    | Section « Référencer le meta » + table opérateurs                                               | Modifier                                               |
| `docs/website/docs/upgrade/report-metadata-namespace.md` | Note de migration                                                                               | **Créer**                                              |

> Les `.md` de référence de schéma (`docs/website/docs/reference/schemas/meta/...`) et les copies `docs/website/static/schemas/...` sont **régénérés en CI** (`cd-docs.yml`, `generate-schema-doc` + `cp -rv regis/schemas/*`). Ne pas les éditer à la main : seule la source `regis/schemas/...` est modifiée.

---

## Task 1 : Prédicats purs partagés

Fonctions pures, sans json_logic, réutilisées par les opérateurs (Task 2) et le format-checker meta (Task 4).

**Files:**

- Create: `regis/utils/predicates.py`
- Test: `tests/test_predicates.py`

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `tests/test_predicates.py` :

```python
"""Tests for shared rule/meta predicate helpers."""

import pytest

from regis.utils.predicates import is_empty, is_falsy, is_truthy, is_url, matches


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "On", " true "])
def test_is_truthy_true(value):
    assert is_truthy(value) is True


def test_is_truthy_bool():
    assert is_truthy(True) is True


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "maybe", "", None, 1, 0])
def test_is_truthy_false(value):
    assert is_truthy(value) is False


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no", "Off", " false "])
def test_is_falsy_true(value):
    assert is_falsy(value) is True


def test_is_falsy_bool():
    assert is_falsy(False) is True


@pytest.mark.parametrize("value", ["true", "1", "maybe", "", None, 0])
def test_is_falsy_false(value):
    assert is_falsy(value) is False


@pytest.mark.parametrize(
    "value", ["http://x.io", "https://github.com/org/repo/actions/runs/1"]
)
def test_is_url_true(value):
    assert is_url(value) is True


@pytest.mark.parametrize(
    "value", ["not a url", "ftp://x.io", "github.com", "", None, 123, "https://"]
)
def test_is_url_false(value):
    assert is_url(value) is False


@pytest.mark.parametrize("value", [None, "", "   "])
def test_is_empty_true(value):
    assert is_empty(value) is True


@pytest.mark.parametrize("value", ["x", "0", 0, False])
def test_is_empty_false(value):
    assert is_empty(value) is False


def test_matches_hit():
    assert matches("job-42", r"^job-[0-9]+$") is True


def test_matches_miss():
    assert matches("job-x", r"^job-[0-9]+$") is False


def test_matches_invalid_regex_is_false():
    assert matches("anything", r"[unclosed") is False


@pytest.mark.parametrize("value", [None, 123])
def test_matches_non_string_is_false(value):
    assert matches(value, r".*") is False
```

- [ ] **Step 2: Lancer pour vérifier l'échec**

Run: `pipenv run pytest --no-cov tests/test_predicates.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'regis.utils.predicates'`.

- [ ] **Step 3: Écrire l'implémentation**

Créer `regis/utils/predicates.py` :

```python
"""Pure predicate helpers shared by rule operators and meta validation.

These functions are intentionally free of any ``json_logic`` dependency so they
can be reused by :mod:`regis.analyzers.metadata` (format checking) and unit-tested
in isolation. They follow a defensive style: unexpected input types yield a falsy
result rather than raising.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_TRUTHY = {"true", "1", "yes", "on"}
_FALSY = {"false", "0", "no", "off"}


def is_truthy(value: Any) -> bool:
    """True for boolean ``True`` or a truthy string (true/1/yes/on, case-insensitive)."""
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() in _TRUTHY


def is_falsy(value: Any) -> bool:
    """True for boolean ``False`` or a falsy string (false/0/no/off, case-insensitive).

    Not the strict complement of :func:`is_truthy`: a junk string ("maybe") is
    neither truthy nor falsy.
    """
    if value is False:
        return True
    return isinstance(value, str) and value.strip().lower() in _FALSY


def is_url(value: Any) -> bool:
    """True if ``value`` is a well-formed http/https URL (scheme + netloc)."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except (ValueError, AttributeError):
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_empty(value: Any) -> bool:
    """True if ``value`` is None, an empty string, or whitespace-only."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def matches(value: Any, pattern: Any) -> bool:
    """True if ``value`` (a string) matches the regular expression ``pattern``.

    Non-string input or an invalid regex yields ``False`` (a warning is logged for
    the latter).
    """
    if not isinstance(value, str) or not isinstance(pattern, str):
        return False
    try:
        return bool(re.search(pattern, value))
    except re.error:
        logger.warning("matches: invalid regex pattern %r", pattern)
        return False
```

- [ ] **Step 4: Lancer pour vérifier le succès**

Run: `pipenv run pytest --no-cov tests/test_predicates.py -q`
Expected: PASS (tous les cas).

- [ ] **Step 5: Format, lint, commit**

```bash
pipenv run ruff format regis/utils/predicates.py tests/test_predicates.py
pipenv run ruff check regis/utils/predicates.py tests/test_predicates.py
git add regis/utils/predicates.py tests/test_predicates.py
git commit -m "feat(rules): shared pure predicate helpers (truthy/falsy/url/empty/matches)"
```

---

## Task 2 : Opérateurs JSON Logic

Enregistrer les prédicats comme opérateurs, à côté de `intersects`/`env_contains`.

**Files:**

- Modify: `regis/rules/evaluator.py` (imports en tête + `_add_custom_operations`, ~ligne 285)
- Test: `tests/test_rules_evaluator.py` (ajouts)

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à la fin de `tests/test_rules_evaluator.py` :

```python
def test_helper_operators_registered():
    """The new helper operators evaluate through json_logic."""
    import regis.rules.evaluator  # noqa: F401  (registers operators on import)
    from json_logic import jsonLogic

    assert jsonLogic({"is_true": [{"var": "v"}]}, {"v": "yes"}) is True
    assert jsonLogic({"is_true": [{"var": "v"}]}, {"v": "nope"}) is False
    assert jsonLogic({"is_false": [{"var": "v"}]}, {"v": "off"}) is True
    assert jsonLogic({"is_url": [{"var": "v"}]}, {"v": "https://x.io"}) is True
    assert jsonLogic({"is_url": [{"var": "v"}]}, {"v": "x.io"}) is False
    assert jsonLogic({"is_empty": [{"var": "v"}]}, {"v": ""}) is True
    assert jsonLogic({"is_set": [{"var": "v"}]}, {"v": "x"}) is True
    assert jsonLogic({"matches": [{"var": "v"}, "^job-[0-9]+$"]}, {"v": "job-7"}) is True
```

- [ ] **Step 2: Lancer pour vérifier l'échec**

Run: `pipenv run pytest --no-cov tests/test_rules_evaluator.py::test_helper_operators_registered -q`
Expected: FAIL — `Unrecognized operation is_true` (ou KeyError équivalent).

- [ ] **Step 3: Écrire l'implémentation**

Dans `regis/rules/evaluator.py`, ajouter l'import en tête (sous `from regis.playbook.context import ...`) :

```python
from regis.utils.predicates import is_empty, is_falsy, is_truthy, is_url, matches
```

Puis, à la fin de `_add_custom_operations()` (juste avant la fin de la fonction, après le bloc `env_contains`), ajouter :

```python
    # Meta/string helpers — meta values arrive as strings, so these make rule
    # conditions over `metadata.*` ergonomic. All are defensive (falsy on
    # unexpected input). See regis/utils/predicates.py.
    json_logic.add_operation("is_true", is_truthy)
    json_logic.add_operation("is_false", is_falsy)
    json_logic.add_operation("is_url", is_url)
    json_logic.add_operation("is_empty", is_empty)
    json_logic.add_operation("is_set", lambda a: not is_empty(a))
    json_logic.add_operation("matches", matches)
```

- [ ] **Step 4: Lancer pour vérifier le succès**

Run: `pipenv run pytest --no-cov tests/test_rules_evaluator.py -q`
Expected: PASS (le nouveau test + les existants).

- [ ] **Step 5: Format, lint, commit**

```bash
pipenv run ruff format regis/rules/evaluator.py tests/test_rules_evaluator.py
pipenv run ruff check regis/rules/evaluator.py tests/test_rules_evaluator.py
git add regis/rules/evaluator.py tests/test_rules_evaluator.py
git commit -m "feat(rules): register is_true/is_false/is_url/is_empty/is_set/matches operators"
```

---

## Task 3 : Namespace `metadata.*` optionnel (fix `incomplete`)

Une clé manquante sous `metadata.*` ne doit plus marquer la règle `incomplete` (le meta est fourni par l'utilisateur, son absence est un état testable). Les accès `results.*` manquants restent `incomplete`.

**Files:**

- Modify: `regis/playbook/context.py` (`MissingDataTracker.__getitem__` et `__contains__`)
- Test: `tests/test_rules_evaluator.py` (ajouts)

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à la fin de `tests/test_rules_evaluator.py` :

```python
def test_missing_metadata_does_not_mark_incomplete():
    """A rule referencing an absent metadata.* key resolves to a clean fail/pass."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["metadata"]},
        "results": {},
        "metadata": {},
    }
    rules_def = {
        "rules": [
            {
                "slug": "gate-must-be-set",
                "condition": {"is_set": [{"var": "metadata.gate.enabled"}]},
                "messages": {"pass": "set", "fail": "not set"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    rule = next(r for r in res["rules"] if r["slug"] == "gate-must-be-set")
    assert rule["status"] == "failed"  # absent -> failed, NOT incomplete
    assert rule["passed"] is False


def test_present_metadata_evaluates_normally():
    report = {
        "request": {"registry": "docker.io", "analyzers": ["metadata"]},
        "results": {},
        "metadata": {"ci": {"job": {"url": "https://ci.example/run/1"}}},
    }
    rules_def = {
        "rules": [
            {
                "slug": "job-url-valid",
                "condition": {"is_url": [{"var": "metadata.ci.job.url"}]},
                "messages": {"pass": "ok", "fail": "bad"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    rule = next(r for r in res["rules"] if r["slug"] == "job-url-valid")
    assert rule["status"] == "passed"


def test_missing_results_still_incomplete():
    """Non-metadata missing data must still yield incomplete (no regression)."""
    report = {
        "request": {"registry": "docker.io", "analyzers": ["cve"]},
        "results": {},
    }
    rules_def = {
        "rules": [
            {
                "slug": "needs-cve",
                "condition": {"==": [{"var": "results.cve.critical_count"}, 0]},
                "messages": {"pass": "ok", "fail": "bad"},
            }
        ]
    }
    res = evaluate_rules(report, rules_def)
    rule = next(r for r in res["rules"] if r["slug"] == "needs-cve")
    assert rule["status"] == "incomplete"
```

- [ ] **Step 2: Lancer pour vérifier l'échec**

Run: `pipenv run pytest --no-cov tests/test_rules_evaluator.py::test_missing_metadata_does_not_mark_incomplete tests/test_rules_evaluator.py::test_present_metadata_evaluates_normally tests/test_rules_evaluator.py::test_missing_results_still_incomplete -q`
Expected: `test_missing_metadata_does_not_mark_incomplete` FAIL (status == "incomplete"). Les deux autres peuvent déjà passer.

- [ ] **Step 3: Écrire l'implémentation**

Dans `regis/playbook/context.py`, ajouter un helper module-level (juste avant `class MissingDataTracker`) :

```python
def _is_optional_namespace(full_key: str) -> bool:
    """Keys under the user-supplied ``metadata`` namespace are optional.

    Their absence is a legitimate, testable state (via is_set/is_empty), not a
    "an analyzer did not run" condition, so it must not mark a rule incomplete.
    """
    return full_key == "metadata" or full_key.startswith("metadata.")
```

Dans `MissingDataTracker.__getitem__`, remplacer les deux affectations `self.root.missing_accessed = True` par une garde. Le corps devient :

```python
    def __getitem__(self, key: str) -> Any:
        full_key = f"{self.path}.{key}" if self.path else key
        self.accessed_keys.add(full_key)
        try:
            val = super().__getitem__(key)
        except KeyError:
            if not _is_optional_namespace(full_key):
                self.root.missing_accessed = True
            raise

        if val is None:
            if not _is_optional_namespace(full_key):
                self.root.missing_accessed = True
            return None

        if isinstance(val, dict):
            return MissingDataTracker(val, full_key, self.root)
        return val
```

Et dans `__contains__`, garder l'affectation de la même manière :

```python
    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            full_key = f"{self.path}.{key}" if self.path else key
            self.accessed_keys.add(full_key)
        if not super().__contains__(key):
            if not (isinstance(key, str) and _is_optional_namespace(
                f"{self.path}.{key}" if self.path else key
            )):
                self.root.missing_accessed = True
            return False
        return True
```

- [ ] **Step 4: Lancer pour vérifier le succès**

Run: `pipenv run pytest --no-cov tests/test_rules_evaluator.py tests/test_playbook_engine.py -q`
Expected: PASS (nouveaux tests + non-régression du moteur playbook).

- [ ] **Step 5: Format, lint, commit**

```bash
pipenv run ruff format regis/playbook/context.py tests/test_rules_evaluator.py
pipenv run ruff check regis/playbook/context.py tests/test_rules_evaluator.py
git add regis/playbook/context.py tests/test_rules_evaluator.py
git commit -m "fix(rules): exempt metadata.* namespace from incomplete-tracking"
```

---

## Task 4 : Schéma well-known imbriqué + `MetadataAnalyzer`

Le meta est stocké imbriqué (`{ci:{job:{url}}}`) ; le schéma doit l'être aussi pour que `enum`/`uri` s'appliquent vraiment. Le format `uri` est rendu déterministe via un `FormatChecker` local réutilisant `is_url`. La sortie `metadata_validation` est indexée par chemin pointé.

**Files:**

- Modify (rewrite): `regis/schemas/meta/well-known.schema.json`
- Modify (rewrite `analyze()` + helpers): `regis/analyzers/metadata.py`
- Test (rewrite): `tests/test_analyzer_metadata.py`

- [ ] **Step 1: Réécrire les tests (qui échouent)**

Remplacer **tout** le contenu de `tests/test_analyzer_metadata.py` par :

```python
"""Tests for MetadataAnalyzer (nested well-known schema + format checking)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from regis.analyzers.metadata import MetadataAnalyzer


class TestMetadataAnalyzerWellKnownOnly:
    """Tests without a playbook meta_schema_path. Meta is nested, as in production."""

    def test_empty_metadata_valid(self):
        analyzer = MetadataAnalyzer(metadata={})
        result = analyzer.analyze()
        assert result["analyzer"] == "metadata"
        assert result["valid"] is True
        # Every known leaf field is reported valid when absent (optional).
        for v in result["metadata_validation"].values():
            assert v == {"valid": True}
        # Known leaf paths are dotted.
        assert "ci.platform" in result["metadata_validation"]
        assert "ci.job.url" in result["metadata_validation"]

    def test_valid_well_known_field(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"platform": "github"}})
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["ci"]["platform"] == "github"
        assert result["metadata_validation"]["ci.platform"] == {"valid": True}

    def test_invalid_well_known_enum_value(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"platform": "bitbucket"}})
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["ci.platform"]["valid"] is False
        assert "error" in result["metadata_validation"]["ci.platform"]

    def test_valid_well_known_uri(self):
        analyzer = MetadataAnalyzer(
            metadata={"ci": {"job": {"url": "https://ci.example/run/9"}}}
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata_validation"]["ci.job.url"] == {"valid": True}

    def test_invalid_well_known_uri(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"job": {"url": "not a url"}}})
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["ci.job.url"]["valid"] is False

    def test_unknown_keys_passthrough_not_in_validation(self):
        analyzer = MetadataAnalyzer(
            metadata={"custom": {"key": "value"}, "ci": {"platform": "github"}}
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["custom"]["key"] == "value"
        assert "custom.key" not in result["metadata_validation"]
        assert "ci.platform" in result["metadata_validation"]

    def test_analyze_ignores_positional_args(self):
        analyzer = MetadataAnalyzer(metadata={"ci": {"job": {"id": "123"}}})
        client = MagicMock()
        result = analyzer.analyze(client, "repo/name", "latest", "linux/amd64")
        assert result["valid"] is True
        assert result["metadata"]["ci"]["job"]["id"] == "123"

    def test_validate_is_noop(self):
        analyzer = MetadataAnalyzer(metadata={})
        analyzer.validate({})  # should not raise


class TestMetadataAnalyzerWithPlaybookSchema:
    """Tests with a custom playbook meta_schema_path (merged via allOf)."""

    def _write_schema(self, tmp_path: Path, schema: dict) -> Path:
        p = tmp_path / "meta.schema.json"
        p.write_text(json.dumps(schema))
        return p

    def test_required_field_present(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-42"}, meta_schema_path=schema_path
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"]["PROJECT_ID"] == "PROJ-42"
        assert result["metadata_validation"]["PROJECT_ID"] == {"valid": True}

    def test_required_field_missing(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_path=schema_path)
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["PROJECT_ID"]["valid"] is False
        assert "error" in result["metadata_validation"]["PROJECT_ID"]

    def test_required_field_wrong_type(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": 42}, meta_schema_path=schema_path
        )
        result = analyzer.analyze()
        assert result["valid"] is False
        assert result["metadata_validation"]["PROJECT_ID"]["valid"] is False

    def test_optional_field_absent(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"OPTIONAL_FIELD": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(metadata={}, meta_schema_path=schema_path)
        result = analyzer.analyze()
        assert result["valid"] is True
        assert "OPTIONAL_FIELD" not in result["metadata"]
        assert result["metadata_validation"]["OPTIONAL_FIELD"] == {"valid": True}

    def test_nonexistent_schema_path_falls_back_to_well_known(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.json"
        analyzer = MetadataAnalyzer(
            metadata={"ci": {"platform": "github"}}, meta_schema_path=nonexistent
        )
        result = analyzer.analyze()
        assert result["valid"] is True

    def test_combined_well_known_and_playbook_fields(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["PROJECT_ID"],
            "properties": {"PROJECT_ID": {"type": "string"}},
        }
        schema_path = self._write_schema(tmp_path, schema)
        analyzer = MetadataAnalyzer(
            metadata={"PROJECT_ID": "PROJ-1", "ci": {"platform": "gitlab"}},
            meta_schema_path=schema_path,
        )
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata_validation"]["PROJECT_ID"] == {"valid": True}
        assert result["metadata_validation"]["ci.platform"] == {"valid": True}

    def test_none_metadata_defaults_to_empty(self):
        analyzer = MetadataAnalyzer(metadata=None)
        result = analyzer.analyze()
        assert result["valid"] is True
        assert result["metadata"] == {}
```

- [ ] **Step 2: Réécrire le schéma well-known**

Remplacer **tout** le contenu de `regis/schemas/meta/well-known.schema.json` par :

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://regis/schemas/meta/well-known.schema.json",
  "title": "Regis Well-Known Metadata",
  "description": "Standard metadata fields recognized by regis across all playbooks.",
  "type": "object",
  "properties": {
    "ci": {
      "type": "object",
      "description": "Continuous-integration context for the analysis run.",
      "properties": {
        "platform": {
          "type": "string",
          "enum": ["github", "gitlab"],
          "description": "CI platform running the analysis"
        },
        "job": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "description": "Unique identifier of the CI job"
            },
            "url": {
              "type": "string",
              "format": "uri",
              "description": "URL to the CI job run"
            }
          },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```

- [ ] **Step 3: Lancer pour vérifier l'échec**

Run: `pipenv run pytest --no-cov tests/test_analyzer_metadata.py -q`
Expected: FAIL — les cas `test_valid_well_known_field` / `test_invalid_well_known_enum_value` / `*_uri` échouent (l'`analyze()` actuel suppose des propriétés plates et n'active pas le format checker).

- [ ] **Step 4: Réécrire `MetadataAnalyzer`**

Dans `regis/analyzers/metadata.py`, remplacer les imports en tête et la méthode `analyze()` + les helpers internes. Garder `__init__`, `validate`, `_build_combined_schema`, `_load_well_known_schema` inchangés sauf indication. Imports en tête (après `import jsonschema`) :

```python
from regis.utils.predicates import is_url
```

Ajouter, au niveau module (après `logger = logging.getLogger(__name__)`) :

```python
# A local format checker so `format: uri` is enforced deterministically
# (jsonschema's default does nothing for "uri" without an optional dependency).
_FORMAT_CHECKER = jsonschema.FormatChecker()


@_FORMAT_CHECKER.checks("uri")
def _check_uri(value: object) -> bool:
    # Format checks run only on string instances; non-strings are caught by `type`.
    return is_url(value) if isinstance(value, str) else True


def _collect_leaf_paths(schema: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Recursively collect dotted leaf paths from a schema's ``properties``.

    A leaf is any property that is not an object-with-properties. Returns a mapping
    of ``dotted.path -> subschema`` (subschema currently unused but kept for clarity).
    """
    paths: dict[str, Any] = {}
    for name, sub in schema.get("properties", {}).items():
        path = f"{prefix}.{name}" if prefix else name
        if isinstance(sub, dict) and sub.get("type") == "object" and "properties" in sub:
            paths.update(_collect_leaf_paths(sub, path))
        else:
            paths[path] = sub
    return paths
```

Remplacer le corps de `analyze()` (de la ligne `combined_schema = self._build_combined_schema()` jusqu'au `return {...}` final) par :

```python
        combined_schema = self._build_combined_schema()

        # Known leaf fields (dotted) across the well-known + playbook schemas.
        leaf_paths: dict[str, Any] = {}
        for sub in combined_schema.get("allOf", []):
            leaf_paths.update(_collect_leaf_paths(sub))

        validator = jsonschema.Draft202012Validator(
            combined_schema, format_checker=_FORMAT_CHECKER
        )
        errors = list(validator.iter_errors(self._metadata))

        # metadata_validation: one entry per known leaf path, valid by default.
        metadata_validation: dict[str, Any] = {
            path: {"valid": True} for path in leaf_paths
        }
        for error in errors:
            if error.validator == "required":
                base = list(error.absolute_path)
                for missing in error.validator_value:
                    dotted = ".".join([*map(str, base), str(missing)])
                    metadata_validation[dotted] = {
                        "valid": False,
                        "error": error.message,
                    }
            else:
                dotted = ".".join(str(p) for p in error.absolute_path)
                if dotted:
                    metadata_validation[dotted] = {
                        "valid": False,
                        "error": error.message,
                    }

        return {
            "analyzer": self.name,
            "metadata": dict(self._metadata),
            "metadata_validation": metadata_validation,
            "valid": not errors,
        }
```

> Note de contrat : `metadata` reflète désormais le dict meta utilisateur **tel quel** (imbriqué), sans synthèse de `null` pour les champs absents (cette synthèse était incohérente avec la structure imbriquée). `metadata_validation` reste `{chemin: {"valid": bool, "error"?: str}}`, indexé par chemin pointé.

- [ ] **Step 5: Lancer pour vérifier le succès**

Run: `pipenv run pytest --no-cov tests/test_analyzer_metadata.py -q`
Expected: PASS (tous les cas, enum **et** uri réellement rejetés).

- [ ] **Step 6: Format, lint, commit**

```bash
pipenv run ruff format regis/analyzers/metadata.py tests/test_analyzer_metadata.py
pipenv run ruff check regis/analyzers/metadata.py tests/test_analyzer_metadata.py
git add regis/analyzers/metadata.py regis/schemas/meta/well-known.schema.json tests/test_analyzer_metadata.py
git commit -m "fix(metadata): nested well-known schema with real enum/uri enforcement"
```

---

## Task 5 : Normalisation report (rupture, `request.metadata` retiré)

Emplacement unique `metadata.*` ; `request.metadata` supprimé du schéma et du producteur ; `REPORT_SCHEMA_VERSION` 2 → 3 ; fixture contrat v3.

**Files:**

- Modify: `regis/schemas/report/report.schema.json` (retrait `request.properties.metadata`, description top-level `metadata`)
- Modify: `regis/commands/analyze.py` (2 sites)
- Modify: `regis/utils/report.py` (`REPORT_SCHEMA_VERSION = 3`)
- Create: `tests/fixtures/report.v3.json`
- Modify: `tests/test_report_schema_version.py`
- Modify: `tests/test_gh_env.py` (1 assert)

- [ ] **Step 1: Écrire/мettre à jour les tests qui échouent**

Dans `tests/test_report_schema_version.py` :

(a) Remplacer `test_constant_is_two` par :

```python
    def test_constant_is_three(self):
        from regis.utils.report import REPORT_SCHEMA_VERSION

        assert REPORT_SCHEMA_VERSION == 3
```

(b) Ajouter à la classe `TestReportSchemaVersion` :

```python
    def test_rejects_request_metadata(self):
        """request.metadata was removed; request has additionalProperties:false."""
        report = _minimal_report()
        report["request"]["metadata"] = {"ci": {"platform": "github"}}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=report, schema=_report_schema())

    def test_accepts_top_level_metadata(self):
        report = _minimal_report(metadata={"ci": {"platform": "github"}})
        jsonschema.validate(instance=report, schema=_report_schema())
```

(c) Dans `TestContractFixture`, repointer les deux méthodes sur `report.v3.json` et l'assertion de version :

```python
    def test_fixture_validates_against_real_validator(self):
        import json
        from pathlib import Path

        from regis.utils.report import validate_report

        fixture = Path(__file__).parent / "fixtures" / "report.v3.json"
        report = json.loads(fixture.read_text(encoding="utf-8"))

        assert report["schemaVersion"] == 3
        validate_report(report)  # must not raise

    def test_analyzer_blobs_match_their_schemas(self):
        import json
        from pathlib import Path

        import jsonschema

        fixtures = Path(__file__).parent / "fixtures" / "report.v3.json"
        report = json.loads(fixtures.read_text(encoding="utf-8"))

        schema_dir = importlib.resources.files("regis.schemas.analyzer")
        for slug in ("cve", "oci"):
            schema = json.loads(
                schema_dir.joinpath(f"{slug}.schema.json").read_text(encoding="utf-8")
            )
            jsonschema.validate(instance=report["results"][slug], schema=schema)
```

Dans `tests/test_gh_env.py`, ajouter après l'assert `report["metadata"]["ci"]["job_id"] == "999"` (≈ ligne 83) :

```python
            # Canonical location only: request.metadata was removed.
            assert "metadata" not in report["request"]
```

- [ ] **Step 2: Créer la fixture v3**

```bash
cp tests/fixtures/report.v2.json tests/fixtures/report.v3.json
```

Puis, dans `tests/fixtures/report.v3.json`, passer `"schemaVersion": 2` → `"schemaVersion": 3` et ajouter une clé top-level `"metadata"` (canonique) juste après la ligne `schemaVersion`. Vérifier qu'aucune clé `metadata` n'existe sous `request` (la copie de v2 n'en a pas). Le bloc d'en-tête doit ressembler à :

```json
{
  "schemaVersion": 3,
  "metadata": { "ci": { "platform": "github" } },
```

(le reste du fichier — `version`, `request`, `results`, blobs `cve`/`oci` — est conservé tel quel depuis v2).

- [ ] **Step 3: Lancer pour vérifier l'échec**

Run: `pipenv run pytest --no-cov tests/test_report_schema_version.py tests/test_gh_env.py -q`
Expected: FAIL — `test_constant_is_three` (constante = 2), `test_rejects_request_metadata` (schéma accepte encore), `test_gh_env` (écrit encore `request.metadata`).

- [ ] **Step 4: Implémenter les changements producteur + schéma**

Dans `regis/utils/report.py` ligne 17 :

```python
REPORT_SCHEMA_VERSION = 3
```

Dans `regis/schemas/report/report.schema.json` :

- Préciser la description du top-level `metadata` (≈ ligne 56-59) :

```json
    "metadata": {
      "type": "object",
      "description": "Arbitrary user-provided metadata (from --meta). Optional namespace exposed to rules as metadata.*.",
      "additionalProperties": true
    },
```

- Supprimer entièrement la propriété `metadata` du bloc `request.properties` (≈ lignes 123-127), de sorte que la dernière propriété de `request` reste `timestamp` et que `"additionalProperties": false` rejette désormais `request.metadata`.

Dans `regis/commands/analyze.py`, supprimer les deux écritures de `request.metadata` :

- Flux rerun (≈ ligne 371), supprimer la ligne :

```python
            existing_report.setdefault("request", {})["metadata"] = metadata_dict
```

- Flux normal (≈ ligne 593), supprimer la ligne :

```python
            analysis_report["request"]["metadata"] = metadata_dict
```

- [ ] **Step 5: Lancer pour vérifier le succès**

Run: `pipenv run pytest --no-cov tests/test_report_schema_version.py tests/test_gh_env.py tests/test_analyze_rerun.py -q`
Expected: PASS.

- [ ] **Step 6: Format, lint, commit**

```bash
pipenv run ruff format regis/commands/analyze.py regis/utils/report.py tests/test_report_schema_version.py tests/test_gh_env.py
pipenv run ruff check regis/commands/analyze.py regis/utils/report.py tests/test_report_schema_version.py tests/test_gh_env.py
git add regis/commands/analyze.py regis/utils/report.py regis/schemas/report/report.schema.json tests/fixtures/report.v3.json tests/test_report_schema_version.py tests/test_gh_env.py
git commit -m "feat(schema)!: single canonical metadata.* location, bump report schema 2->3"
```

---

## Task 6 : Documentation

Documenter le namespace `metadata.*`, le comportement optionnel, les champs well-known, les helpers ; note de migration.

**Files:**

- Modify: `docs/website/docs/concepts/rules.md`
- Create: `docs/website/docs/upgrade/report-metadata-namespace.md`

- [ ] **Step 1: Étendre la table des opérateurs**

Dans `docs/website/docs/concepts/rules.md`, dans la table « Regis adds several custom operators » (≈ ligne 233), ajouter ces lignes sous `env_contains` :

```markdown
| `is_true` | `true` if the value is a truthy string (`true`/`1`/`yes`/`on`, case-insensitive) or boolean `true`. |
| `is_false` | `true` if the value is a falsy string (`false`/`0`/`no`/`off`) or boolean `false`. |
| `is_url` | `true` if the value is a well-formed `http`/`https` URL. |
| `is_empty` | `true` if the value is null, empty, or whitespace-only. |
| `is_set` | `true` if the value is present and non-empty (complement of `is_empty`). |
| `matches` | `true` if the string value matches a regular expression: `{"matches": [{"var": "..."}, "^pattern$"]}`. |
```

- [ ] **Step 2: Ajouter la section « Référencer le meta dans les règles »**

Dans `docs/website/docs/concepts/rules.md`, juste avant `## Rule evaluation mechanics` (≈ ligne 222), insérer :

## Référencer le meta dans les règles

Les valeurs passées via `regis analyze --meta <clé>=<valeur>` sont exposées aux
règles sous le namespace **`metadata.*`** (chemin canonique). La notation pointée
de la clé devient une structure imbriquée :

```bash
regis analyze nginx:latest \
  --meta ci.platform=github \
  --meta ci.job.url=https://github.com/org/repo/actions/runs/42
```

s'adresse en règle par `{"var": "metadata.ci.platform"}` et
`{"var": "metadata.ci.job.url"}`.

### Namespace optionnel

Le meta est fourni par l'utilisateur : une clé `metadata.*` absente résout à
`null` **sans** marquer la règle `incomplete` (contrairement à un `results.*`
manquant, qui signifie « un analyzer n'a pas tourné »). On peut donc tester la
présence d'un meta de façon fiable :

```yaml
spec:
  rules:
    - slug: ci-job-url-required
      description: A CI job URL must be provided and well-formed.
      level: warning
      tags: [provenance]
      condition:
        and:
          - { "is_set": [{ "var": "metadata.ci.job.url" }] }
          - { "is_url": [{ "var": "metadata.ci.job.url" }] }
      messages:
        pass: "CI job URL is present and valid."
        fail: "Provide a valid --meta ci.job.url."
```

Comme toutes les valeurs `--meta` sont des chaînes, les helpers `is_true` /
`is_false` interprètent les drapeaux booléens :

```yaml
condition: { "is_true": [{ "var": "metadata.gate.enabled" }] }
```

### Champs well-known

Regis reconnaît ces champs standard (validés contre
`schemas/meta/well-known.schema.json`) ; tout autre champ est accepté tel quel :

| Champ                  | Type         | Notes                  |
| :--------------------- | :----------- | :--------------------- |
| `metadata.ci.platform` | enum         | `github` ou `gitlab`.  |
| `metadata.ci.job.id`   | string       | Identifiant du job CI. |
| `metadata.ci.job.url`  | string (uri) | URL du run CI.         |

- [ ] **Step 3: Créer la note de migration**

Créer `docs/website/docs/upgrade/report-metadata-namespace.md` :

```markdown
---
title: Report metadata namespace (schemaVersion 3)
---

# Report metadata namespace — `schemaVersion` 3

Starting with report `schemaVersion: 3`, user metadata (`--meta`) lives at a
**single canonical location**: the top-level `metadata` object. The duplicate
`request.metadata` field has been **removed**, and the report schema now rejects
it (`request` is `additionalProperties: false`).

## What changed

- `report.metadata.*` is the only place user metadata is written.
- Rules reference it as `{"var": "metadata.<key>"}` (e.g. `metadata.ci.job.url`).
- `request.metadata` is gone.

## Action required

- **Rule authors:** use `metadata.*` paths. Any rule that referenced
  `request.metadata.*` must switch to `metadata.*`.
- **Downstream consumers** (dashboards, plugins) reading `request.metadata` must
  read top-level `metadata` instead, and gate on `schemaVersion >= 3`.
- **Stored reports** produced before this change that contain `request.metadata`
  will fail validation if re-validated; regenerate them with `regis analyze`.

There is no automated migration: reports are generated output, not user config.
````

- [ ] **Step 4: Vérifier le build doc (lien/markdown)**

Run: `pipenv run pytest --no-cov tests/test_rules_evaluator.py tests/test_analyzer_metadata.py -q`
Expected: PASS (garde-fou : la doc n'introduit pas de régression ; pas de build Docusaurus requis localement).

> Le `_category_.json` de `upgrade/` liste-t-il explicitement les pages ? Vérifier `docs/website/docs/upgrade/_category_.json` : s'il fixe un ordre via `position`, aucun ajout par page n'est nécessaire (tri par défaut). Ne pas modifier sauf si un index manuel y référence chaque page.

- [ ] **Step 5: Commit**

```bash
git add docs/website/docs/concepts/rules.md docs/website/docs/upgrade/report-metadata-namespace.md
git commit -m "docs(rules): document metadata.* namespace, helpers, and schema-3 migration"
```

---

## Self-Review (effectuée)

**Couverture spec :**

- §1 Normalisation namespace → Task 5. ✅
- §2 Helpers JSON Logic → Tasks 1 + 2. ✅
- §3 Namespace `metadata.*` optionnel → Task 3. ✅
- §4 Schéma well-known corrigé + metadata.py → Task 4. ✅
- §5 Documentation → Task 6 (+ note upgrade). ✅
- §6 Tests TDD → intégrés à chaque task. ✅

**Cohérence des types/noms :** prédicats purs `is_truthy`/`is_falsy`/`is_url`/`is_empty`/`matches` (Task 1) ; opérateurs `is_true`/`is_false`/`is_url`/`is_empty`/`is_set`/`matches` (Task 2) ; `_is_optional_namespace` (Task 3) ; `_collect_leaf_paths`/`_FORMAT_CHECKER` (Task 4) ; `REPORT_SCHEMA_VERSION = 3` cohérent entre `report.py`, tests, fixture v3.

**Hors périmètre confirmé :** `is_semver`, `to_number`, migration outillée des reports existants.

**Coordination :** la rupture report (`feat(schema)!`, Task 5) est à séquencer avec la file « presentation generalization » ; le bump 2 → 3 doit être le bump report en vigueur au merge (vérifier qu'aucune autre PR en file ne vise aussi 2 → 3 pour éviter un double bump). La couverture globale doit rester ≥ 90 % (`pipenv run pytest`).
