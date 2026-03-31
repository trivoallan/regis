"""GitHub CLI commands for regis."""

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

_COMMENT_MARKER = "<!-- regis -->"


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
    playbook = report_data.get("playbook", {})
    summary = playbook.get("rules_summary", {})
    score = summary.get("score", "N/A")
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    tier = playbook.get("tier") or "N/A"

    trivy = report_data.get("analyzers", {}).get("trivy", {})
    vuln_summary = trivy.get("vulnerabilities", {}).get("summary", {})

    lines = [
        _COMMENT_MARKER,
        "",
        "## regis Analysis Results",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| **Score** | {score}/100 |",
        f"| **Tier** | {tier} |",
        f"| **Rules** | {passed}/{total} passed |",
    ]

    if vuln_summary:
        critical = vuln_summary.get("CRITICAL", 0)
        high = vuln_summary.get("HIGH", 0)
        lines.append(f"| **Vulnerabilities** | {critical} critical, {high} high |")

    lines += [
        "",
        f"[View Full Report]({report_url})",
    ]

    return "\n".join(lines)


def _apply_labels(
    owner: str,
    repo: str,
    pr_number: str,
    token: str,
    report_data: dict,
    headers: dict,
) -> None:
    """Apply playbook labels and badge labels to a GitHub PR.

    Args:
        owner: Repository owner.
        repo: Repository name.
        pr_number: Pull request number as a string.
        token: GitHub authentication token (unused directly; passed via headers).
        report_data: Parsed report.json contents.
        headers: Pre-built GitHub API request headers.
    """
    playbook = report_data.get("playbook", {})
    labels: list[str] = list(playbook.get("labels", []))
    badge_labels: list[dict] = playbook.get("badge_labels", [])
    for badge in badge_labels:
        name = badge.get("name")
        if name:
            labels.append(name)

    if not labels:
        return

    labels_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/labels"
    )
    try:
        resp = requests.post(
            labels_url, headers=headers, json={"labels": labels}, timeout=30
        )
        resp.raise_for_status()
        click.echo(f"Applied {len(labels)} label(s) to PR.", err=True)
    except Exception as exc:
        click.echo(f"Warning: failed to apply labels to PR: {exc}", err=True)


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

    # Look for an existing regis comment
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

    _apply_labels(owner, repo, pr_number, token, report_data, headers)
