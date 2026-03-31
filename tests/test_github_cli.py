"""Tests for the github CLI subcommands in regis-cli."""

import json
from unittest import mock

import pytest
from click.testing import CliRunner

from regis_cli.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def report_data():
    return {
        "tier": "Gold",
        "rules_summary": {
            "score": 85,
            "total": ["rule-a", "rule-b", "rule-c", "rule-d"],
            "passed": ["rule-a", "rule-b", "rule-c"],
        },
        "results": {
            "trivy": {
                "analyzer": "trivy",
                "critical_count": 2,
                "high_count": 5,
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
    with mock.patch("regis_cli.github_cli.requests") as mock_requests:
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
        assert "<!-- regis-cli -->" in post_body
        assert "85" in post_body  # score

        # PATCH must NOT be called
        mock_requests.patch.assert_not_called()


def test_updates_existing_comment(runner, report_file):
    """When a comment with the marker is found, PATCH is called to update it."""
    existing_comment_id = 999
    with mock.patch("regis_cli.github_cli.requests") as mock_requests:
        # GET returns one comment containing the marker
        mock_requests.get.return_value.json.return_value = [
            {"id": existing_comment_id, "body": "<!-- regis-cli -->\nOld content"},
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
        assert "<!-- regis-cli -->" in patch_body

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
    with mock.patch("regis_cli.github_cli.requests") as mock_requests:
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


def test_token_read_from_env(runner, report_file, monkeypatch):
    """The --token option should fall back to GITHUB_TOKEN env var."""
    monkeypatch.setenv("GITHUB_TOKEN", "env_token")

    with mock.patch("regis_cli.github_cli.requests") as mock_requests:
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

        get_headers = mock_requests.get.call_args[1]["headers"]
        assert get_headers["Authorization"] == "Bearer env_token"
