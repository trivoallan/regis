# trunk-ignore-all(bandit/B101)
"""Tests for the gitlab CLI subcommands in regis-cli."""

import json
from unittest import mock

import pytest
from click.testing import CliRunner

from regis_cli.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_create_request_success(runner):
    """Test the create-request command generates expected output."""
    result = runner.invoke(
        main,
        [
            "gitlab",
            "create-request",
            "ghcr.io/myname/myimage:latest",
            "https://example.com/playbook.yml",
            "123",
            "testuser",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["image_url"] == "ghcr.io/myname/myimage:latest"
    assert data["playbook_url"] == "https://example.com/playbook.yml"
    assert data["requester_id"] == 123
    assert data["requester_login"] == "testuser"


def test_create_request_invalid_id(runner):
    """Test create-request command with invalid requester ID."""
    result = runner.invoke(
        main,
        [
            "gitlab",
            "create-request",
            "image:latest",
            "url",
            "not_an_int",
            "user",
        ],
    )
    assert result.exit_code != 0
    assert "Invalid requester_id 'not_an_int'" in result.output


def test_update_mr_success(runner, tmp_path):
    """Test update-mr success using mock gitlab."""
    # Create fake report.json
    report_file = tmp_path / "report.json"
    report_data = {
        "playbook": {
            "labels": ["security"],
            "mr_description_checklists": [
                {
                    "title": "Security Check",
                    "items": [
                        "Review report",
                        {"label": "Approve", "checked": True},
                        {"label": "Dismiss", "checked": False},
                    ],
                }
            ],
        }
    }
    report_file.write_text(json.dumps(report_data))

    # Mock python-gitlab execution
    with mock.patch("regis_cli.gitlab_cli.gitlab.Gitlab") as mock_gl:
        mock_instance = mock_gl.return_value
        mock_project = mock_instance.projects.get.return_value
        mock_mr = mock_project.mergerequests.get.return_value

        # Setup existing MR properties
        mock_mr.description = "Original Description"
        mock_mr.labels = []

        result = runner.invoke(
            main,
            [
                "gitlab",
                "update-mr",
                "--report",
                str(report_file),
                "--report-url",
                "https://example.com/report.html",
                "--mr-url",
                "https://gitlab.com/api/v4/projects/1/merge_requests/2",
                "--token",
                "test-token",
            ],
        )

        assert result.exit_code == 0
        assert "Posted MR comment with report link." in result.output
        assert "Updated MR: description and labels (security)." in result.output

        # Verify Comment Creation
        mock_mr.notes.create.assert_called_once()
        create_args = mock_mr.notes.create.call_args[0][0]
        assert "https://example.com/report.html" in create_args["body"]

        # Verify Description Changes
        assert "https://example.com/report.html" in mock_mr.description
        assert "Original Description" in mock_mr.description
        assert "Security Check" in mock_mr.description
        assert "- [ ] Review report" in mock_mr.description
        assert "- [x] Approve" in mock_mr.description
        assert "- [ ] Dismiss" in mock_mr.description

        # Verify Label Changes
        assert mock_mr.labels == ["security"]

        # Save must be called to update MR on gitlab
        mock_mr.save.assert_called_once()


def test_update_mr_invalid_url(runner, tmp_path):
    """Test update-mr with invalid mr-url format."""
    report_file = tmp_path / "report.json"
    report_file.write_text("{}")

    result = runner.invoke(
        main,
        [
            "gitlab",
            "update-mr",
            "--report",
            str(report_file),
            "--report-url",
            "http://url",
            "--mr-url",
            "https://gitlab.com/invalid/format",
            "--token",
            "token",
        ],
    )
    assert result.exit_code != 0
    assert "Invalid MR URL format" in result.output
