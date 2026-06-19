"""Unit tests for the SARIF renderer (playbook verdicts -> SARIF 2.1.0)."""

import json

from regis.adapters.driven.report.sarif import DOCS_BASE, render_sarif


def _rule(slug, level, status, *, criterion=None, analyzers=None, message="msg"):
    return {
        "slug": slug,
        "description": f"{slug} desc",
        "level": level,
        "status": status,
        "passed": status == "passed",
        "message": message,
        "tags": ["security"],
        "analyzers": analyzers if analyzers is not None else [],
        **({"criterion": criterion} if criterion else {}),
    }


def _report(rules, *, digest="sha256-AAA"):
    return {
        "version": "0.37.0",
        "request": {
            "url": "python:3.9-slim",
            "registry": "registry-1.docker.io",
            "repository": "library/python",
            "tag": "3.9-slim",
            "digest": digest,
        },
        "rules": rules,
    }


def test_emits_one_result_per_breach():
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule("a", "critical", "failed"),
                    _rule("b", "warning", "passed"),
                    _rule("c", "info", "failed"),
                    _rule("d", "warning", "incomplete"),
                ]
            )
        )
    )
    assert [r["ruleId"] for r in s["runs"][0]["results"]] == ["a", "c"]


def test_maps_severity_to_level_and_security_severity():
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule("crit", "critical", "failed"),
                    _rule("warn", "warning", "failed"),
                    _rule("note", "info", "failed"),
                ]
            )
        )
    )
    res = {r["ruleId"]: r for r in s["runs"][0]["results"]}
    assert (res["crit"]["level"], res["crit"]["properties"]["security-severity"]) == (
        "error",
        "9.0",
    )
    assert (res["warn"]["level"], res["warn"]["properties"]["security-severity"]) == (
        "warning",
        "7.0",
    )
    assert (res["note"]["level"], res["note"]["properties"]["security-severity"]) == (
        "note",
        "2.0",
    )


def test_help_uri_points_to_criterion_doc():
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule(
                        "cve-critical",
                        "critical",
                        "failed",
                        criterion="cve-count",
                        analyzers=["cve"],
                    ),
                ]
            )
        )
    )
    desc = s["runs"][0]["tool"]["driver"]["rules"][0]
    assert desc["helpUri"] == f"{DOCS_BASE}/cve/cve-count"


def test_help_uri_falls_back_to_core_when_no_analyzer():
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule(
                        "registry-domain-whitelist",
                        "critical",
                        "failed",
                        criterion="registry-domain-whitelist",
                        analyzers=[],
                    ),
                ]
            )
        )
    )
    desc = s["runs"][0]["tool"]["driver"]["rules"][0]
    assert desc["helpUri"] == f"{DOCS_BASE}/core/registry-domain-whitelist"


def test_fingerprint_ignores_digest():
    f1 = json.loads(
        render_sarif(_report([_rule("a", "warning", "failed")], digest="sha256-AAA"))
    )
    f2 = json.loads(
        render_sarif(_report([_rule("a", "warning", "failed")], digest="sha256-ZZZ"))
    )
    assert (
        f1["runs"][0]["results"][0]["partialFingerprints"]
        == f2["runs"][0]["results"][0]["partialFingerprints"]
    )


def test_every_result_indexes_its_descriptor():
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule("a", "critical", "failed"),
                    _rule("b", "warning", "passed"),
                ]
            )
        )
    )
    rules = s["runs"][0]["tool"]["driver"]["rules"]
    assert {d["id"] for d in rules} == {"a", "b"}  # every evaluated rule -> descriptor
    for res in s["runs"][0]["results"]:
        assert rules[res["ruleIndex"]]["id"] == res["ruleId"]


def test_message_links_to_full_report():
    s = json.loads(
        render_sarif(
            _report([_rule("a", "warning", "failed")]),
            report_url="https://ci/report.html",
        )
    )
    assert "https://ci/report.html" in s["runs"][0]["results"][0]["message"]["markdown"]


def test_location_defaults_to_dockerfile_and_is_overridable():
    # GitHub Code Scanning rejects results without a location, so every result
    # carries one, anchored at the Dockerfile by default (the artifact the image
    # was built from) — overridable for repos that keep it elsewhere.
    default = json.loads(render_sarif(_report([_rule("a", "warning", "failed")])))
    loc = default["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "Dockerfile"

    custom = json.loads(
        render_sarif(
            _report([_rule("a", "warning", "failed")]), dockerfile="build/Dockerfile"
        )
    )
    uri = custom["runs"][0]["results"][0]["locations"][0]["physicalLocation"][
        "artifactLocation"
    ]["uri"]
    assert uri == "build/Dockerfile"


def test_no_rules_yields_valid_empty_sarif():
    s = json.loads(render_sarif(_report([])))
    assert s["version"] == "2.1.0"
    assert s["runs"][0]["results"] == []
    assert s["runs"][0]["tool"]["driver"]["name"] == "Regis"
