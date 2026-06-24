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


def test_every_result_is_kind_fail():
    # houba keys on result.kind to classify a verdict as a governance breach
    # (policy.*) rather than a vulnerability (vuln.*); regis only emits breaches.
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule("a", "critical", "failed"),
                    _rule("b", "warning", "passed"),
                    _rule("c", "info", "failed"),
                ]
            )
        )
    )
    results = s["runs"][0]["results"]
    assert results  # sanity: breaches present
    assert all(r["kind"] == "fail" for r in results)


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
    # No playbook ran -> not evaluated -> empty run (the "Regis never ran"
    # signal). The pass receipt fires only when rules were actually evaluated.
    s = json.loads(render_sarif(_report([])))
    assert s["version"] == "2.1.0"
    assert s["runs"][0]["results"] == []
    assert s["runs"][0]["tool"]["driver"]["name"] == "Regis"


def test_clean_run_emits_pass_receipt_keyed_to_digest():
    # A clean run (rules evaluated, zero breaches) must NOT be an empty SARIF
    # run -- that is indistinguishable from "Regis never ran". One kind="pass"
    # result, carrying the digest, proves governance happened for this image.
    s = json.loads(
        render_sarif(
            _report(
                [
                    _rule("a", "warning", "passed"),
                    _rule("b", "info", "incomplete"),
                ],
                digest="sha256-CLEAN",
            )
        )
    )
    results = s["runs"][0]["results"]
    assert len(results) == 1
    receipt = results[0]
    assert receipt["kind"] == "pass"
    assert receipt["level"] == "none"
    assert receipt["properties"]["digest"] == "sha256-CLEAN"
    # self-consistent: the receipt's ruleIndex resolves to its descriptor
    rules = s["runs"][0]["tool"]["driver"]["rules"]
    assert rules[receipt["ruleIndex"]]["id"] == receipt["ruleId"]
