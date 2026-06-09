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
