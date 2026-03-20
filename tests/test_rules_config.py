from regis_cli.rules.evaluator import evaluate_rules


def test_parameterized_rules():
    # Mock report
    report = {
        "request": {
            "analyzers": ["trivy"],
            "url": "nginx:latest",
            "registry": "docker.io",
            "repository": "library/nginx",
            "tag": "latest",
            "timestamp": "2024-03-20T10:00:00Z",
        },
        "results": {
            "trivy": {
                "analyzer": "trivy",
                "critical_count": 2,
                "high_count": 5,
                "medium_count": 10,
            }
        },
    }

    # Playbook with parameterized rules
    playbook = {
        "rules": [
            {
                "provider": "trivy",
                "rule": "cve-count",
                "options": {"level": "critical", "max_count": 0},
            },
            {
                "provider": "trivy",
                "rule": "cve-count",
                "options": {"level": "high", "max_count": 10},
            },
        ]
    }

    results = evaluate_rules(report, playbook)
    rules = {r["slug"]: r for r in results["rules"]}

    # Verify instantiation and slugs
    assert "cve-count.critical" in rules
    assert "cve-count.high" in rules

    # Verify results
    assert rules["cve-count.critical"]["passed"] is False  # 2 > 0
    assert "critical CVEs" in rules["cve-count.critical"]["message"]

    assert rules["cve-count.high"]["passed"] is True  # 5 <= 10
    assert "within limits" in rules["cve-count.high"]["message"]


def test_parameterized_rule_custom_slug():
    report = {
        "request": {"analyzers": ["trivy"]},
        "results": {"trivy": {"critical_count": 0}},
    }
    playbook = {
        "rules": [
            {
                "slug": "custom-trivy-rule",
                "provider": "trivy",
                "rule": "cve-count",
                "options": {"level": "critical", "max_count": 0},
            }
        ]
    }
    results = evaluate_rules(report, playbook)
    rules = {r["slug"]: r for r in results["rules"]}
    assert "custom-trivy-rule" in rules
    assert rules["custom-trivy-rule"]["passed"] is True


def test_hadolint_dockle_parameterized():
    report = {
        "request": {"analyzers": ["hadolint", "dockle"]},
        "results": {
            "hadolint": {"issues_by_level": {"error": 1, "warning": 3}},
            "dockle": {"issues_by_level": {"FATAL": 0, "WARN": 10}},
        },
    }
    playbook = {
        "rules": [
            {
                "provider": "hadolint",
                "rule": "severity-count",
                "options": {"level": "error", "max_count": 0},
            },
            {
                "provider": "dockle",
                "rule": "severity-count",
                "options": {"level": "WARN", "max_count": 5},
            },
        ]
    }
    results = evaluate_rules(report, playbook)
    rules = {r["slug"]: r for r in results["rules"]}

    assert rules["severity-count.error"]["passed"] is False
    assert rules["severity-count.WARN"]["passed"] is False
