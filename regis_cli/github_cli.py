"""GitHub CLI commands for regis-cli."""

from __future__ import annotations

import json
import logging
import re

import click
import requests

logger = logging.getLogger(__name__)

_PR_URL_RE = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)

_COMMENT_MARKER = "<!-- regis-cli -->"


@click.group()
def github_cmd() -> None:
    """GitHub CI integration commands."""
    pass


def _build_comment_body(report_data: dict, report_url: str) -> str:
    """Build the Markdown comment body from report data.

    Args:
        report_data: Parsed report.json contents.
        report_url: URL to the generated HTML report.

    Returns:
        Markdown string to post as a PR comment.
    """
    rules_summary = report_data.get("rules_summary", {})
    score = rules_summary.get("score", "N/A")
    total_rules = len(rules_summary.get("total", []))
    passed_rules = len(rules_summary.get("passed", []))
    tier = report_data.get("tier") or "N/A"

    trivy = report_data.get("results", {}).get("trivy", {})
    critical_count: int | None = trivy.get("critical_count")
    high_count: int | None = trivy.get("high_count")

    lines = [
        _COMMENT_MARKER,
        "",
        "## regis-cli Analysis Results",
        "",
        f"**Score:** {score}/100 &nbsp; **Tier:** {tier}",
        f"**Rules:** {passed_rules}/{total_rules} passed",
    ]

    if critical_count is not None and high_count is not None:
        lines.append(
            f"**Vulnerabilities:** {critical_count} critical, {high_count} high"
        )

    lines += [
        "",
        f"[View Full Report]({report_url})",
    ]

    return "\n".join(lines)


@github_cmd.command(name="update-pr")
@click.option(
    "--report",
    "report_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to report.json",
)
@click.option(
    "--report-url",
    "report_url",
    required=True,
    help="URL to the generated HTML report",
)
@click.option(
    "--pr-url",
    "pr_url",
    required=True,
    help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/42)",
)
@click.option(
    "--token",
    "token",
    default=None,
    envvar="GITHUB_TOKEN",
    help="GitHub token (also reads GITHUB_TOKEN env var)",
)
def update_pr(
    report_path: str, report_url: str, pr_url: str, token: str | None
) -> None:
    """Post or update a PR comment with analysis results."""
    # Parse the PR URL
    match = _PR_URL_RE.fullmatch(pr_url.strip())
    if not match:
        raise click.ClickException(
            f"Invalid GitHub PR URL: '{pr_url}'. "
            "Expected format: https://github.com/<owner>/<repo>/pull/<number>"
        )

    owner = match.group("owner")
    repo = match.group("repo")
    pr_number = match.group("number")

    if not token:
        raise click.ClickException(
            "GitHub token is required. Use --token or set GITHUB_TOKEN."
        )

    # Load the report
    try:
        with open(report_path, encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as exc:
        raise click.ClickException(
            f"Failed to read report file {report_path}: {exc}"
        ) from exc

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    comments_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    )

    # Fetch existing comments
    try:
        response = requests.get(comments_url, headers=headers, timeout=30)
        response.raise_for_status()
        comments = response.json()
    except Exception as exc:
        raise click.ClickException(f"Failed to fetch PR comments: {exc}") from exc

    comment_body = _build_comment_body(report_data, report_url)

    # Look for an existing regis-cli comment
    existing_id: int | None = None
    for comment in comments:
        if _COMMENT_MARKER in comment.get("body", ""):
            existing_id = comment["id"]
            break

    try:
        if existing_id is not None:
            patch_url = (
                f"https://api.github.com/repos/{owner}/{repo}"
                f"/issues/comments/{existing_id}"
            )
            resp = requests.patch(
                patch_url, headers=headers, json={"body": comment_body}, timeout=30
            )
            resp.raise_for_status()
            click.echo(f"Updated existing PR comment (id={existing_id}).", err=True)
        else:
            resp = requests.post(
                comments_url, headers=headers, json={"body": comment_body}, timeout=30
            )
            resp.raise_for_status()
            click.echo("Posted new PR comment.", err=True)
    except Exception as exc:
        raise click.ClickException(f"Failed to post/update PR comment: {exc}") from exc
