import pytest
from json_logic import jsonLogic

from regis_cli.playbook.engine import NamedList, _resolve_path


def test_namedlist_access():
    data = [
        {"slug": "overview", "name": "System Overview", "score": 90},
        {"name": "Security-Checks", "score": 100},
        {"value": "no-name-or-slug"},
    ]
    named_list = NamedList(data)

    # 1. Normal integer access
    assert named_list[0]["score"] == 90
    assert named_list[2]["value"] == "no-name-or-slug"

    # 2. String index access (should fall back to integer if valid number)
    assert named_list["0"]["score"] == 90

    # 3. Slug access
    assert named_list["overview"]["score"] == 90

    # 4. Normalized name access
    # "Security-Checks" -> "security_checks"
    assert named_list["security_checks"]["score"] == 100

    # 5. Invalid access falls back to list exception
    with pytest.raises(TypeError):
        _ = named_list["non_existent"]


def test_resolve_path_with_namedlist():
    context = {
        "playbooks": NamedList(
            [
                {
                    "pages": NamedList(
                        [
                            {
                                "slug": "compliance",
                                "sections": NamedList(
                                    [{"name": "Mandatory Requirements", "score": 85}]
                                ),
                            }
                        ]
                    )
                }
            ]
        )
    }

    # Test int based resolution
    assert _resolve_path("playbooks.0.pages.0.sections.0.score", context) == 85

    # Test name based resolution
    # "Mandatory Requirements" -> "mandatory_requirements"
    path = "playbooks.0.pages.compliance.sections.mandatory_requirements.score"
    assert _resolve_path(path, context) == 85


def test_jsonlogic_with_namedlist():
    context = {
        "playbooks": NamedList(
            [
                {
                    "pages": NamedList(
                        [
                            {
                                "slug": "security",
                                "sections": NamedList(
                                    [{"name": "Vulnerabilities", "critical": 0}]
                                ),
                            }
                        ]
                    )
                }
            ]
        )
    }

    # jsonLogic uses direct dict/list indexing under the hood
    condition = {
        "==": [
            {"var": "playbooks.0.pages.security.sections.vulnerabilities.critical"},
            0,
        ]
    }
    assert jsonLogic(condition, context) is True
