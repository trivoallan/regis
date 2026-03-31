"""Tests for the github CLI subcommands in regis."""

import json
from unittest import mock

import pytest
from click.testing import CliRunner

from regis.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def report_data():
    return {
        "playbook": {
            "playbook_name": "default",
            "score": 85,
            "tier": "Gold",
            "rules_summary": {"score": 85, "total": 10, "passed": 7},
            "badges": [],
            "labels": [],
            "badge_labels": [],
            "mr_description_checklists": [],
        },
        "analyzers": {
            "trivy": {
                "vulnerabilities": {
                    "summary": {"CRITICAL": 2, "HIGH": 5, "MEDIUM": 12, "LOW": 8}
                }
            }
        },
    }


@pytest.fixture
def report_file(tmp_path, report_data):
    f = tmp_path / "report.json"
    f.write_text(json.dumps(report_data))
    return f


def test_creates_new_comment(runner, report_file):
    """When no existing comment is found, POST is called to create a new one."""
    with mock.patch("regis.github_cli.requests") as mock_requests:
        # GET returns empty list — no existing comment
        mock_requests.get.return_value.json.return_value = []
        mock_requests.get.return_value.raise_for_status.return_value = None
        mock_requests.post.return_value.raise_for_status.return_value = None

        result = runner.invoke(
            main,
            [
                "github",
                "update-pr",
                "--report",
                str(report_file),
                "--report-url",
                "https://example.com/report.html",
                "--pr-url",
                "https://github.com/owner/repo/pull/42",
                "--token",
                "ghp_fake",
            ],
        )

        assert result.exit_code == 0, result.output

        # POST must be called once to create the comment
        mock_requests.post.assert_called_once()
        post_url = mock_requests.post.call_args[0][0]
        assert "owner/repo" in post_url
        assert "42" in post_url

        post_body = mock_requests.post.call_args[1]["json"]["body"]
        assert "<!-- regis -->" in post_body
        assert "85/100" in post_body  # score
        assert "7/10" in post_body  # rules

        # PATCH must NOT be called
        mock_requests.patch.assert_not_called()


def test_updates_existing_comment(runner, report_file):
    """When a comment with the marker is found, PATCH is called to update it."""
    existing_comment_id = 999
    with mock.patch("regis.github_cli.requests") as mock_requests:
        # GET returns one comment containing the marker
        mock_requests.get.return_value.json.return_value = [
            {"id": existing_comment_id, "body": "<!-- regis -->\nOld content"},
        ]
        mock_requests.get.return_value.raise_for_status.return_value = None
        mock_requests.patch.return_value.raise_for_status.return_value = None

        result = runner.invoke(
            main,
            [
                "github",
                "update-pr",
                "--report",
                str(report_file),
                "--report-url",
                "https://example.com/report.html",
                "--pr-url",
                "https://github.com/owner/repo/pull/42",
                "--token",
                "ghp_fake",
            ],
        )

        assert result.exit_code == 0, result.output

        # PATCH must be called with the correct comment ID
        mock_requests.patch.assert_called_once()
        patch_url = mock_requests.patch.call_args[0][0]
        assert str(existing_comment_id) in patch_url

        patch_body = mock_requests.patch.call_args[1]["json"]["body"]
        assert "<!-- regis -->" in patch_body

        # POST must NOT be called
        mock_requests.post.assert_not_called()


def test_rejects_invalid_pr_url(runner, report_file):
    """Non-GitHub PR URLs should cause a non-zero exit code."""
    result = runner.invoke(
        main,
        [
            "github",
            "update-pr",
            "--report",
            str(report_file),
            "--report-url",
            "https://example.com/report.html",
            "--pr-url",
            "https://gitlab.com/owner/repo/merge_requests/1",
            "--token",
            "ghp_fake",
        ],
    )

    assert result.exit_code != 0


def test_comment_body_contains_tier_and_vuln_counts(runner, report_file):
    """The comment body should include tier and vulnerability counts."""
    with mock.patch("regis.github_cli.requests") as mock_requests:
        mock_requests.get.return_value.json.return_value = []
        mock_requests.get.return_value.raise_for_status.return_value = None
        mock_requests.post.return_value.raise_for_status.return_value = None

        result = runner.invoke(
            main,
            [
                "github",
                "update-pr",
                "--report",
                str(report_file),
                "--report-url",
                "https://example.com/report.html",
                "--pr-url",
                "https://github.com/owner/repo/pull/42",
                "--token",
                "ghp_fake",
            ],
        )

        assert result.exit_code == 0, result.output

        post_body = mock_requests.post.call_args[1]["json"]["body"]
        assert "Gold" in post_body  # tier
        assert "2" in post_body  # critical count
        assert "5" in post_body  # high count
        assert "https://example.com/report.html" in post_body  # report link


def test_applies_labels_to_pr(runner, tmp_path):
    """Labels from playbook.labels and playbook.badge_labels are POSTed to the labels endpoint."""
    data = {
        "playbook": {
            "rules_summary": {"score": 90, "total": 5, "passed": 5},
            "tier": "Gold",
            "labels": ["regis:security-review"],
            "badge_labels": [{"name": "regis::trivy::critical", "class": "error"}],
        },
        "analyzers": {},
    }
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(data))

    with mock.patch("regis.github_cli.requests") as mock_requests:
        mock_requests.get.return_value.json.return_value = []
        mock_requests.get.return_value.raise_for_status.return_value = None
        mock_requests.post.return_value.status_code = 201
        mock_requests.post.return_value.raise_for_status.return_value = None

        result = runner.invoke(
            main,
            [
                "github",
                "update-pr",
                "--report",
                str(report_file),
                "--report-url",
                "https://example.com/report.html",
                "--pr-url",
                "https://github.com/owner/repo/pull/42",
                "--token",
                "ghp_fake",
            ],
        )

        assert result.exit_code == 0, result.output

        # POST must be called twice: once for comment, once for labels
        assert mock_requests.post.call_count == 2

        # First call: create comment
        comment_url = mock_requests.post.call_args_list[0][0][0]
        assert "comments" in comment_url

        # Second call: apply labels
        labels_url = mock_requests.post.call_args_list[1][0][0]
        assert "/labels" in labels_url
        assert "owner/repo" in labels_url
        assert "42" in labels_url

        labels_body = mock_requests.post.call_args_list[1][1]["json"]["labels"]
        assert "regis:security-review" in labels_body
        assert "regis::trivy::critical" in labels_body


def test_token_read_from_env(runner, report_file, monkeypatch):
    """The --token option should fall back to GITHUB_TOKEN env var."""
    monkeypatch.setenv("GITHUB_TOKEN", "env_token")

    with mock.patch("regis.github_cli.requests") as mock_requests:
        mock_requests.get.return_value.json.return_value = []
        mock_requests.get.return_value.raise_for_status.return_value = None
        mock_requests.post.return_value.raise_for_status.return_value = None

        result = runner.invoke(
            main,
            [
                "github",
                "update-pr",
                "--report",
                str(report_file),
                "--report-url",
                "https://example.com/report.html",
                "--pr-url",
                "https://github.com/owner/repo/pull/42",
                # --token intentionally omitted
            ],
        )

        assert result.exit_code == 0, result.output

        # Verify the token was used in the request
        get_call = mock_requests.get.call_args
        headers = get_call.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer env_token"
