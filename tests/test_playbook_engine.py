"""Tests for the playbook evaluation engine."""

from __future__ import annotations

from typing import Any

import pytest
import yaml

from regis_cli.playbook.engine import _flatten, evaluate, load_playbook


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
            "name": "Custom",
            "sections": [
                {
                    "name": "Main",
                    "levels": [{"name": "bronze", "order": 1}],
                    "scorecards": [
                        {
                            "name": "test-scorecard",
                            "title": "A test scorecard",
                            "level": "bronze",
                            "condition": {"==": [1, 1]},
                        },
                    ],
                }
            ],
        }
        p = tmp_path / "custom.yaml"
        p.write_text(yaml.dump(custom))
        loaded = load_playbook(p)
        assert loaded["name"] == "Custom"
        assert len(loaded["sections"][0]["scorecards"]) == 1

    def test_load_json(self, tmp_path):
        import json

        custom = {
            "name": "JSON Card",
            "sections": [
                {
                    "name": "Main",
                    "levels": [{"name": "bronze", "order": 1}],
                    "scorecards": [
                        {
                            "name": "always-pass",
                            "title": "Always passes",
                            "level": "bronze",
                            "condition": {"==": [1, 1]},
                        },
                    ],
                }
            ],
        }
        p = tmp_path / "custom.json"
        p.write_text(json.dumps(custom))
        loaded = load_playbook(p)
        assert loaded["name"] == "JSON Card"


class TestEvaluate:
    """Test playbook evaluation."""

    PLAYBOOK = {
        "name": "Test Playbook",
        "sections": [
            {
                "name": "Test",
                "levels": [
                    {"name": "bronze", "order": 1},
                    {"name": "silver", "order": 2},
                    {"name": "gold", "order": 3},
                ],
                "scorecards": [
                    {
                        "name": "has-tags",
                        "title": "Has tags",
                        "level": "bronze",
                        "condition": {">": [{"var": "results.tags.total_tags"}, 0]},
                    },
                    {
                        "name": "has-provenance",
                        "title": "Has provenance",
                        "level": "silver",
                        "condition": {
                            "==": [{"var": "results.provenance.has_provenance"}, True]
                        },
                    },
                    {
                        "name": "good-score",
                        "title": "Good playbook",
                        "level": "gold",
                        "condition": {">=": [{"var": "results.playbookdev.score"}, 7]},
                    },
                ],
            }
        ],
    }

    def test_all_pass(self):
        report = {
            "results": {
                "tags": {"total_tags": 100},
                "provenance": {"has_provenance": True},
                "playbookdev": {"score": 8},
            },
        }
        result = evaluate(self.PLAYBOOK, report)
        assert result["score"] == 100
        assert result["passed_scorecards"] == 3
        section = result["pages"][0]["sections"][0]
        assert all(r["passed"] for r in section["scorecards"])

    def test_partial_pass(self):
        report = {
            "results": {
                "tags": {"total_tags": 50},
                "provenance": {"has_provenance": False},
                "playbookdev": {"score": 2},
            },
        }
        result = evaluate(self.PLAYBOOK, report)
        assert result["passed_scorecards"] == 1

    def test_two_pass(self):
        report = {
            "results": {
                "tags": {"total_tags": 50},
                "provenance": {"has_provenance": True},
                "playbookdev": {"score": 3},
            },
        }
        result = evaluate(self.PLAYBOOK, report)
        assert result["passed_scorecards"] == 2

    def test_tags_propagation(self):
        """Test that tags are correctly copied from scorecard defs to results."""
        playbook = {
            "name": "Tags Test",
            "sections": [
                {
                    "name": "Main",
                    "scorecards": [
                        {
                            "name": "scorecard-with-tags",
                            "tags": ["tag1", "tag2"],
                            "condition": {"==": [1, 1]},
                        },
                        {
                            "name": "scorecard-without-tags",
                            "condition": {"==": [1, 1]},
                        },
                    ],
                }
            ],
        }
        result = evaluate(playbook, {})
        scorecards = result["pages"][0]["sections"][0]["scorecards"]
        assert scorecards[0]["tags"] == ["tag1", "tag2"]
        assert scorecards[1]["tags"] == []

    def test_incomplete_status(self):
        """Test that missing data results in an 'incomplete' status."""
        playbook = {
            "name": "Missing Data Test",
            "sections": [
                {
                    "name": "Main",
                    "scorecards": [
                        {
                            "name": "missing-var",
                            "condition": {">": [{"var": "non_existent"}, 0]},
                        }
                    ],
                }
            ],
        }
        result = evaluate(playbook, {"some_other_data": 42})
        scorecards = result["pages"][0]["sections"][0]["scorecards"]
        assert scorecards[0]["status"] == "incomplete"
        assert "MISSING" in scorecards[0]["details"]

    def test_no_pass(self):
        report = {
            "results": {
                "tags": {"total_tags": 0},
                "provenance": {"has_provenance": False},
                "playbookdev": {"score": 0},
                "trivy": {"vulnerability_count": 100},
            },
        }
        result = evaluate(self.PLAYBOOK, report)
        assert result["passed_scorecards"] == 0

    def test_empty_scorecards(self):
        result = evaluate(
            {"name": "empty", "sections": [{"name": "Main", "scorecards": []}]}, {}
        )
        assert result["score"] == 0

    def test_score_percentage(self):
        report = {
            "results": {
                "tags": {"total_tags": 10},
                "provenance": {"has_provenance": True},
                "playbookdev": {"score": 3},
            },
        }
        result = evaluate(self.PLAYBOOK, report)
        assert result["score"] == 67  # 2/3 = 66.67 → rounds to 67

    def test_missing_data_fails_gracefully(self):
        """Scorecards referencing missing data should fail, not crash."""
        report = {"results": {}}
        result = evaluate(self.PLAYBOOK, report)
        assert isinstance(result["score"], int)

    def test_missing_sections_raises(self):
        """Playbooks without sections must raise ValueError."""
        playbook = {
            "name": "Legacy",
            "scorecards": [{"name": "r", "condition": {"==": [1, 1]}}],
        }
        with pytest.raises(ValueError, match="missing both 'pages' and 'sections'"):
            evaluate(playbook, {})

    def test_multi_section(self):
        """Multiple sections aggregate correctly."""
        playbook = {
            "name": "Multi",
            "sections": [
                {
                    "name": "A",
                    "scorecards": [
                        {"name": "a1", "title": "A1", "condition": {"==": [1, 1]}},
                    ],
                },
                {
                    "name": "B",
                    "scorecards": [
                        {"name": "b1", "title": "B1", "condition": {"==": [1, 0]}},
                    ],
                },
            ],
        }
        result = evaluate(playbook, {})
        assert result["total_scorecards"] == 2
        assert result["passed_scorecards"] == 1
        assert result["score"] == 50
        assert len(result["pages"][0]["sections"]) == 2

    def test_render_order(self):
        """render_order reflects the YAML key definition order."""
        playbook = {
            "name": "Order Test",
            "sections": [
                {
                    "name": "Scorecards First",
                    "scorecards": [
                        {"name": "r1", "title": "R1", "condition": {"==": [1, 1]}},
                    ],
                    "display": {
                        "widgets": [{"label": "W", "value": "x"}],
                        "analyzers": ["trivy"],
                    },
                    "levels": [{"name": "bronze", "order": 1}],
                },
            ],
        }
        result = evaluate(playbook, {})
        order = result["pages"][0]["sections"][0]["render_order"]
        assert order == ["scorecards", "widgets", "analyzers", "levels"]

    def test_section_widgets(self):
        """Test that section widgets are resolved correctly (merging section vs display)."""
        playbook = {
            "name": "Widgets Test",
            "sections": [
                {
                    "name": "Widgets",
                    "widgets": [
                        {"label": "W1", "value": "results.w1"},
                        {
                            "template": "analyzers/custom.html",
                            "options": {"foo": "bar"},
                        },
                    ],
                    "display": {"widgets": [{"label": "W2", "value": "results.w2"}]},
                }
            ],
        }
        report = {"results": {"w1": "A", "w2": "B"}}
        result = evaluate(playbook, report)

        section = result["pages"][0]["sections"][0]
        assert "widgets" in section["render_order"]
        widgets = section["widgets"]
        assert len(widgets) == 3
        # Direct section widgets
        assert widgets[0]["label"] == "W1"
        assert widgets[0]["resolved_value"] == "A"
        assert widgets[1]["template"] == "analyzers/custom.html"
        assert widgets[1]["options"] == {"foo": "bar"}
        # Display widgets merged at end
        assert widgets[2]["label"] == "W2"
        assert widgets[2]["resolved_value"] == "B"


class TestGitLabChecklist:
    """Test GitLab MR description checklist item evaluation."""

    BASE_PLAYBOOK = {
        "name": "Checklist Test",
        "sections": [
            {
                "name": "Main",
                "scorecards": [{"name": "always-pass", "condition": {"==": [1, 1]}}],
            }
        ],
    }

    def _make_playbook(self, checklist: list[Any]) -> dict[str, Any]:
        import copy

        pb: dict[str, Any] = copy.deepcopy(self.BASE_PLAYBOOK)
        pb["integrations"] = {"gitlab": {"checklist": checklist}}
        return pb

    def test_unconditional_item_always_included(self):
        """Items with no condition are always added to the checklist."""
        pb = self._make_playbook([{"label": "Manual review done"}])
        result = evaluate(pb, {})
        assert result["mr_description_checklists"] == [
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
                    "show_if": {"==": [{"var": "results.trivy.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"trivy": {"critical_count": 0}}}
        result = evaluate(pb, report)
        assert result["mr_description_checklists"] == [
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
                    "show_if": {"==": [{"var": "results.trivy.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"trivy": {"critical_count": 5}}}
        result = evaluate(pb, report)
        assert "mr_description_checklists" not in result

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
        assert "mr_description_checklists" not in result

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
        assert result["mr_description_checklists"] == [
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
                    "check_if": {"==": [{"var": "results.trivy.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"trivy": {"critical_count": 0}}}
        result = evaluate(pb, report)
        assert result["mr_description_checklists"] == [
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
                    "check_if": {"==": [{"var": "results.trivy.critical_count"}, 0]},
                }
            ]
        )
        report = {"results": {"trivy": {"critical_count": 3}}}
        result = evaluate(pb, report)
        assert result["mr_description_checklists"] == [
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
        assert result["mr_description_checklists"] == [
            {
                "title": "📝 Review Checklist",
                "items": [{"label": "Some item", "checked": False}],
            }
        ]

    def test_no_checklist_key_absent(self):
        """When checklist is not defined, mr_description_checklists is absent."""
        result = evaluate(self.BASE_PLAYBOOK, {})
        assert "mr_description_checklists" not in result

    def test_empty_checklist_key_absent(self):
        """When checklist is an empty list, mr_description_checklists is absent."""
        pb = self._make_playbook([])
        result = evaluate(pb, {})
        assert "mr_description_checklists" not in result

    def test_multiple_checklists(self):
        import copy

        pb = copy.deepcopy(self.BASE_PLAYBOOK)
        pb["integrations"] = {
            "gitlab": {
                "checklists": [
                    {
                        "title": "Security Checklist",
                        "items": [
                            {
                                "label": "No critical CVEs",
                                "check_if": {
                                    "==": [{"var": "results.trivy.critical_count"}, 0]
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
        }
        report = {"results": {"trivy": {"critical_count": 0}}}
        result = evaluate(pb, report)
        assert result["mr_description_checklists"] == [
            {
                "title": "Security Checklist",
                "items": [{"label": "No critical CVEs", "checked": True}],
            },
            {
                "title": "Compliance Checklist",
                "items": [{"label": "Manual compliance check", "checked": False}],
            },
        ]


class TestGitLabTemplates:
    """Test GitLab MR templates evaluation."""

    BASE_PLAYBOOK = {
        "name": "Templates Test",
        "sections": [
            {
                "name": "Main",
                "scorecards": [{"name": "always-pass", "condition": {"==": [1, 1]}}],
            }
        ],
    }

    def _make_playbook(self, templates: list[Any]) -> dict[str, Any]:
        import copy

        pb: dict[str, Any] = copy.deepcopy(self.BASE_PLAYBOOK)
        pb["integrations"] = {"gitlab": {"templates": templates}}
        return pb

    def test_unconditional_template_included(self):
        """Templates with no condition are always added."""
        pb = self._make_playbook([{"url": "https://example.com/template"}])
        result = evaluate(pb, {})
        assert result["mr_templates"] == [{"url": "https://example.com/template"}]

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
        assert result["mr_templates"] == [{"url": "local/path/to/template"}]

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
        assert "mr_templates" not in result

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
        assert "mr_templates" not in result

    def test_empty_templates_absent(self):
        """When templates is an empty list, mr_templates is absent."""
        pb = self._make_playbook([])
        result = evaluate(pb, {})
        assert "mr_templates" not in result
