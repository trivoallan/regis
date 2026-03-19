"""GitLab CLI commands for regis-cli."""

from __future__ import annotations

import json
import logging

import click
import gitlab

# We will need standard types like Path


logger = logging.getLogger(__name__)


@click.group()
def gitlab_cmd() -> None:
    """GitLab CI integration commands."""
    pass


@gitlab_cmd.command(name="create-request")
@click.argument("image_url")
@click.argument("playbook_url")
@click.argument("requester_id")
@click.argument("requester_login")
def create_request(
    image_url: str, playbook_url: str, requester_id: str, requester_login: str
) -> None:
    """Create a JSON request for analysis.

    This replaces the base64-encoded python snippet that outputs analysis-request.json.
    """
    try:
        req_id = int(requester_id)
    except ValueError as exc:
        raise click.ClickException(
            f"Invalid requester_id '{requester_id}', must be an integer."
        ) from exc

    request_data = {
        "image_url": image_url,
        "playbook_url": playbook_url,
        "requester_id": req_id,
        "requester_login": requester_login,
    }

    click.echo(json.dumps(request_data, indent=2))


@gitlab_cmd.command(name="update-mr")
@click.option(
    "--report",
    "report_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to report.json",
)
@click.option(
    "--report-url", "report_url", required=True, help="URL to the generated HTML report"
)
@click.option(
    "--mr-url",
    "mr_url",
    required=True,
    help="GitLab API URL for the MR (e.g. https://gitlab.com/api/v4/projects/1/merge_requests/2)",
)
@click.option("--token", "token", required=True, help="GitLab PRIVATE-TOKEN")
def update_mr(report_path: str, report_url: str, mr_url: str, token: str) -> None:
    """Update a Merge Request with analysis results.

    This command reads the report.json, posts a comment with a link to the HTML report,
    updates the MR description to include the link and any checklists, and applies labels.
    """
    try:
        from urllib.parse import urlparse

        parsed_url = urlparse(mr_url)
        # e.g. mr_url = "https://gitlab.example.com/api/v4/projects/123/merge_requests/456"
        host = f"{parsed_url.scheme}://{parsed_url.netloc}"

        path_parts = parsed_url.path.strip("/").split("/")
        # Find 'projects' index and extract project ID and MR IID
        try:
            proj_idx = path_parts.index("projects")
            project_id = int(path_parts[proj_idx + 1])
            mr_iid = int(path_parts[proj_idx + 3])
        except (ValueError, IndexError) as exc:
            raise click.ClickException(
                f"Invalid MR URL format: {mr_url}. Expected format containing /projects/<id>/merge_requests/<iid>"
            ) from exc

    except Exception as exc:
        if isinstance(exc, click.ClickException):
            raise
        raise click.ClickException(f"Failed to parse MR URL: {exc}") from exc

    # Read the JSON report
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as exc:
        raise click.ClickException(
            f"Failed to read report file {report_path}: {exc}"
        ) from exc

    # Initialize GitLab client
    gl = gitlab.Gitlab(host, private_token=token)

    try:
        project = gl.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
    except gitlab.GitlabGetError as exc:
        raise click.ClickException(f"Failed to fetch MR from GitLab: {exc}") from exc

    # 1. Post a comment with the report link
    comment_body = (
        "🚀 **regis-cli Analysis Complete!**\n\n"
        f"The full HTML security report is ready: [View Analysis Report]({report_url})"
    )
    try:
        mr.notes.create({"body": comment_body})
        click.echo("Posted MR comment with report link.", err=True)
    except gitlab.GitlabCreateError as exc:
        click.echo(f"Warning: Failed to post MR comment: {exc}", err=True)

    # 2. Extract labels and checklists from the playbook in the report
    playbook_data = report_data.get("playbook", {})
    labels = playbook_data.get("labels", [])
    badge_labels = playbook_data.get("badge_labels", [])
    checklists = playbook_data.get("mr_description_checklists", [])

    # 3. Handle badge labels with colors
    final_labels = list(labels)
    class_colors = {
        "success": "388e3c",
        "warning": "fbc02d",
        "error": "d32f2f",
        "information": "1976d2",
    }

    for badge in badge_labels:
        name = badge["name"]
        cls = badge["class"]
        color = class_colors.get(cls, "607d8b")  # default grey

        try:
            # Check if label exists, otherwise create it
            try:
                project.labels.get(name)
            except gitlab.GitlabGetError:
                project.labels.create({"name": name, "color": f"#{color}"})
                click.echo(
                    f"Created GitLab label '{name}' with color {color}", err=True
                )

            if name not in final_labels:
                final_labels.append(name)
        except Exception as exc:
            click.echo(
                f"Warning: Failed to manage GitLab label '{name}': {exc}", err=True
            )

    # 4. Build new MR description
    current_desc = mr.description or ""
    report_link_md = f"📝 **[View Analysis Report]({report_url})**"

    # Prepend report link to description if changing it wasn't already done
    if "View Analysis Report" not in current_desc:
        new_desc = f"{report_link_md}\n\n{current_desc}"
    else:
        new_desc = current_desc

    # Setup checklist strings
    checklist_lines = []
    if checklists:
        for clist in checklists:
            title = clist.get("title")
            if title:
                checklist_lines.append(f"\n\n---\n\n## {title}\n")
            items = clist.get("items", [])
            for item in items:
                if isinstance(item, dict):
                    checked = "x" if item.get("checked") else " "
                    label = item["label"]
                    checklist_lines.append(f"- [{checked}] {label}")
                else:
                    checklist_lines.append(f"- [ ] {item}")

    # Append checklist to description
    if checklist_lines:
        checklist_md = "\n".join(checklist_lines)
        if checklist_md not in new_desc:
            new_desc = f"{new_desc}{checklist_md}"

    from typing import Any

    update_kwargs: dict[str, Any] = {}
    if new_desc != current_desc:
        update_kwargs["description"] = new_desc

    if final_labels:
        # Get existing labels to append new ones
        ext_labels = list(mr.labels)
        for label in final_labels:
            if label not in ext_labels:
                ext_labels.append(label)
        update_kwargs["labels"] = ext_labels

    if update_kwargs:
        try:
            for k, v in update_kwargs.items():
                setattr(mr, k, v)
            mr.save()
            msg = []
            if "description" in update_kwargs:
                msg.append("description")
            if "labels" in update_kwargs:
                msg.append(f"labels ({','.join(labels)})")
            click.echo(f"Updated MR: {' and '.join(msg)}.", err=True)
        except gitlab.GitlabUpdateError as exc:
            click.echo(f"Warning: Failed to update MR: {exc}", err=True)
    else:
        click.echo("No description or label updates required.", err=True)
