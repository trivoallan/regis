"""Unit tests for the pure view-model builder _build_context."""

from regis.report.html import _build_context


def _report(results=None, rules=None, tier="Gold", score=92):
    rules = rules if rules is not None else []
    return {
        "schemaVersion": 4,
        "request": {"registry": "r", "repository": "library/nginx", "tag": "1.27"},
        "results": results if results is not None else {},
        "tier": tier,
        "rules": rules,
        "rules_summary": {
            "score": score,
            "total": [r["slug"] for r in rules],
            "passed": [r["slug"] for r in rules if r["passed"]],
        },
    }


_FAILING_CVE_RULE = {
    "slug": "no-critical-cve",
    "level": "critical",
    "passed": False,
    "status": "failed",
    "message": "1 critical CVE",
    "analyzers": ["cve"],
}


class TestToc:
    def test_one_entry_per_analyzer(self):
        ctx = _build_context(
            _report(results={"cve": {"analyzer": "cve"}, "oci": {"analyzer": "oci"}}),
            "all",
        )
        slugs = [e["slug"] for e in ctx["toc"]]
        assert slugs == ["cve", "oci"]

    def test_status_reflects_failing_analyzers(self):
        ctx = _build_context(
            _report(
                results={"cve": {"analyzer": "cve"}, "oci": {"analyzer": "oci"}},
                rules=[_FAILING_CVE_RULE],
            ),
            "all",
        )
        status = {e["slug"]: e["status"] for e in ctx["toc"]}
        assert status == {"cve": "fail", "oci": "pass"}

    def test_respects_slug_filter(self):
        ctx = _build_context(
            _report(results={"cve": {}, "oci": {}}),
            "cve",
        )
        assert [e["slug"] for e in ctx["toc"]] == ["cve"]


class TestFailingAnalyzers:
    def test_collects_analyzers_of_failed_rules(self):
        ctx = _build_context(
            _report(
                results={"cve": {}, "oci": {}},
                rules=[
                    _FAILING_CVE_RULE,
                    {
                        "slug": "ok-rule",
                        "level": "info",
                        "passed": True,
                        "status": "passed",
                        "message": "",
                        "analyzers": ["oci"],
                    },
                ],
            ),
            "all",
        )
        assert ctx["failing_analyzers"] == {"cve"}

    def test_empty_when_all_pass(self):
        ctx = _build_context(_report(results={"cve": {}}), "all")
        assert ctx["failing_analyzers"] == set()

    def test_excludes_incomplete_rules(self):
        ctx = _build_context(
            _report(
                results={"cve": {}},
                rules=[
                    {
                        "slug": "maybe-cve",
                        "level": "critical",
                        "passed": False,
                        "status": "incomplete",
                        "message": "",
                        "analyzers": ["cve"],
                    }
                ],
            ),
            "all",
        )
        assert ctx["failing_analyzers"] == set()

    def test_sourced_from_playbooks_when_present(self):
        report = {
            "schemaVersion": 4,
            "request": {"registry": "r", "repository": "x", "tag": "t"},
            "results": {"cve": {}},
            "playbooks": [
                {
                    "tier": "Gold",
                    "rules_summary": {"score": 50, "total": ["a"], "passed": []},
                    "rules": [
                        {
                            "slug": "a",
                            "level": "critical",
                            "passed": False,
                            "status": "failed",
                            "message": "boom",
                            "analyzers": ["cve"],
                        }
                    ],
                }
            ],
        }
        ctx = _build_context(report, "all")
        assert ctx["failing_analyzers"] == {"cve"}
        assert {e["slug"]: e["status"] for e in ctx["toc"]} == {"cve": "fail"}
