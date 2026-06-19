"""Tests for the playbook evaluation engine."""

from __future__ import annotations

from typing import Any

import yaml

from regis.core.domain.playbook.engine import _flatten, evaluate, load_playbook


class TestFlatten:
    """Test the ``_flatten`` helper."""

    def test_simple(self):
        data = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        flat = _flatten(data)
        assert flat == {"a": 1, "b.c": 2, "b.d.e": 3}

    def test_empty(self):
        assert _flatten({}) == {}


class TestLoadPlaybook:
    """Test playbook loading."""

    def test_load_from_file(self, tmp_path):
        custom = {
            "apiVersion": "regis.io/v1alpha1",
            "kind": "Playbook",
            "metadata": {
                "name": "custom",
                "title": "Custom",
                "labels": {"app.kubernetes.io/version": "1.0.0"},
            },
            "spec": {
                "rules": [
                    {
                        "slug": "test-rule",
                        "provider": "core",
                        "rule": "always-true",
                        "level": "warning",
                    },
                ],
            },
        }
        p = tmp_path / "custom.yaml"
        p.write_text(yaml.dump(custom))
        loaded = load_playbook(p)
        assert loaded["name"] == "Custom"
        assert len(loaded["rules"]) == 1

    def test_load_json(self, tmp_path):
        import json

        custom = {
            "apiVersion": "regis.io/v1alpha1",
            "kind": "Playbook",
            "metadata": {
                "name": "json-card",
                "title": "JSON Card",
                "labels": {"app.kubernetes.io/version": "1.0.0"},
            },
            "spec": {
                "rules": [
                    {
                        "slug": "always-pass",
                        "provider": "core",
                        "rule": "always-true",
                        "level": "warning",
                    },
                ],
            },
        }
        p = tmp_path / "custom.json"
        p.write_text(json.dumps(custom))
        loaded = load_playbook(p)
        assert loaded["name"] == "JSON Card"


class TestPresentationChecklists:
    """Test presentation checklist item evaluation."""

    BASE_PLAYBOOK = {
        "schemaVersion": 1,
        "version": "1.0.0",
        "name": "Checklist Test",
    }

    def _make_playbook(self, checklist: list[Any]) -> dict[str, Any]:
        import copy

        pb: dict[str, Any] = copy.deepcopy(self.BASE_PLAYBOOK)
        pb["presentation"] = {"checklist": checklist}
        return pb

    def test_unconditional_item_always_included(self):
        """Items with no condition are always added to the checklist."""
        pb = self._make_playbook([{"label": "Manual review done"}])
        result = evaluate(pb, {})
        assert result["checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [{"label": "Manual review done", "checked": False}],
            }
        ]

    def test_truthy_condition_includes_item(self):
        """Items whose condition evaluates to True are included."""
        pb = self._make_playbook(
            [
                {
                    "label": "No critical CVEs",
                    "show_if": {"==": [{"var": "results.cve.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"cve": {"critical_count": 0}}}
        result = evaluate(pb, report)
        assert result["checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [{"label": "No critical CVEs", "checked": False}],
            }
        ]

    def test_falsy_condition_excludes_item(self):
        """Items whose condition evaluates to False are excluded."""
        pb = self._make_playbook(
            [
                {
                    "label": "No critical CVEs",
                    "show_if": {"==": [{"var": "results.cve.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"cve": {"critical_count": 5}}}
        result = evaluate(pb, report)
        assert "checklists" not in result

    def test_missing_data_excludes_item(self):
        """Items whose condition references missing data are excluded."""
        pb = self._make_playbook(
            [
                {
                    "label": "Item needs missing data",
                    "show_if": {"==": [{"var": "non_existent_key"}, 0]},
                }
            ]
        )
        result = evaluate(pb, {})
        assert "checklists" not in result

    def test_mixed_items(self):
        """Mixed conditional and unconditional items produce correct subset."""
        pb = self._make_playbook(
            [
                {"label": "Always here"},
                {
                    "label": "Included: truthy",
                    "show_if": {"==": [{"var": "results.ok"}, True]},
                },
                {
                    "label": "Excluded: falsy",
                    "show_if": {"==": [{"var": "results.ok"}, False]},
                },
            ]
        )
        report = {"results": {"ok": True}}
        result = evaluate(pb, report)
        assert result["checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [
                    {"label": "Always here", "checked": False},
                    {"label": "Included: truthy", "checked": False},
                ],
            }
        ]

    def test_check_if_pre_checks_item(self):
        """An item with a truthy check_if renders as checked."""
        pb = self._make_playbook(
            [
                {
                    "label": "No critical CVEs",
                    "check_if": {"==": [{"var": "results.cve.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"cve": {"critical_count": 0}}}
        result = evaluate(pb, report)
        assert result["checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [{"label": "No critical CVEs", "checked": True}],
            }
        ]

    def test_check_if_falsy_stays_unchecked(self):
        """An item with a falsy check_if renders as unchecked."""
        pb = self._make_playbook(
            [
                {
                    "label": "No critical CVEs",
                    "check_if": {"==": [{"var": "results.cve.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"cve": {"critical_count": 3}}}
        result = evaluate(pb, report)
        assert result["checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [{"label": "No critical CVEs", "checked": False}],
            }
        ]

    def test_missing_check_if_stays_unchecked(self):
        """When check_if references missing data, item renders unchecked."""
        pb = self._make_playbook(
            [
                {
                    "label": "Some item",
                    "check_if": {"==": [{"var": "non_existent"}, 0]},
                }
            ]
        )
        result = evaluate(pb, {})
        assert result["checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [{"label": "Some item", "checked": False}],
            }
        ]

    def test_no_checklist_key_absent(self):
        """When checklist is not defined, checklists is absent."""
        result = evaluate(self.BASE_PLAYBOOK, {})
        assert "checklists" not in result

    def test_empty_checklist_key_absent(self):
        """When checklist is an empty list, checklists is absent."""
        pb = self._make_playbook([])
        result = evaluate(pb, {})
        assert "checklists" not in result

    def test_multiple_checklists(self):
        import copy

        pb = copy.deepcopy(self.BASE_PLAYBOOK)
        pb["presentation"] = {
            "checklists": [
                {
                    "title": "Security Checklist",
                    "items": [
                        {
                            "label": "No critical CVEs",
                            "check_if": {
                                "==": [{"var": "results.cve.critical_count"}, 0]
                            },
                        }
                    ],
                },
                {
                    "title": "Compliance Checklist",
                    "items": [{"label": "Manual compliance check"}],
                },
            ]
        }
        report = {"results": {"cve": {"critical_count": 0}}}
        result = evaluate(pb, report)
        assert result["checklists"] == [
            {
                "title": "Security Checklist",
                "items": [{"label": "No critical CVEs", "checked": True}],
            },
            {
                "title": "Compliance Checklist",
                "items": [{"label": "Manual compliance check", "checked": False}],
            },
        ]


class TestPresentationTemplates:
    """Test presentation templates evaluation."""

    BASE_PLAYBOOK = {
        "schemaVersion": 1,
        "version": "1.0.0",
        "name": "Templates Test",
    }

    def _make_playbook(self, templates: list[Any]) -> dict[str, Any]:
        import copy

        pb: dict[str, Any] = copy.deepcopy(self.BASE_PLAYBOOK)
        pb["presentation"] = {"templates": templates}
        return pb

    def test_unconditional_template_included(self):
        """Templates with no condition are always added."""
        pb = self._make_playbook([{"url": "https://example.com/template"}])
        result = evaluate(pb, {})
        assert result["templates"] == [{"url": "https://example.com/template"}]

    def test_truthy_condition_includes_template(self):
        """Templates whose condition evaluates to True are included."""
        pb = self._make_playbook(
            [
                {
                    "url": "local/path/to/template",
                    "condition": {"==": [{"var": "results.ok"}, True]},
                }
            ]
        )
        report = {"results": {"ok": True}}
        result = evaluate(pb, report)
        assert result["templates"] == [{"url": "local/path/to/template"}]

    def test_falsy_condition_excludes_template(self):
        """Templates whose condition evaluates to False are excluded."""
        pb = self._make_playbook(
            [
                {
                    "url": "local/path/to/template",
                    "condition": {"==": [{"var": "results.ok"}, False]},
                }
            ]
        )
        report = {"results": {"ok": True}}
        result = evaluate(pb, report)
        assert "templates" not in result

    def test_missing_data_excludes_template(self):
        """Templates whose condition references missing data are excluded."""
        pb = self._make_playbook(
            [
                {
                    "url": "local/path/to/template",
                    "condition": {"==": [{"var": "non_existent_key"}, True]},
                }
            ]
        )
        result = evaluate(pb, {})
        assert "templates" not in result

    def test_empty_templates_absent(self):
        """When templates is an empty list, templates is absent."""
        pb = self._make_playbook([])
        result = evaluate(pb, {})
        assert "templates" not in result


def test_evaluate_propagates_playbook_metadata() -> None:
    from regis.core.domain.playbook.evaluator import evaluate

    playbook = {
        "apiVersion": "regis.io/v1alpha1",
        "kind": "Playbook",
        "version": "2.3.4",
        "name": "MetadataPlaybook",
    }
    report: dict = {"results": {}}
    result = evaluate(playbook, report)

    assert result["playbook_name"] == "MetadataPlaybook"
    assert result["playbook_version"] == "2.3.4"
    assert result["api_version"] == "regis.io/v1alpha1"
    assert "schema_version" not in result


def test_evaluate_propagates_api_version() -> None:
    from regis.core.domain.playbook.evaluator import evaluate

    playbook = {
        "apiVersion": "regis.io/v1alpha1",
        "kind": "Playbook",
        "name": "X",
        "version": "1.0.0",
        "rules": [],
    }
    result = evaluate(playbook, {"analyzers": {}})
    assert result["api_version"] == "regis.io/v1alpha1"
    assert result["playbook_version"] == "1.0.0"
    assert "schema_version" not in result
