#!/usr/bin/env python3
"""Generate the What's New page for the Docusaurus documentation site.

Reads CHANGELOG.md and produces docs/website/docs/whats-new.md.

Two layers of content:
  1. Base: CHANGELOG.md parsed into clean, user-friendly Markdown (always runs).
  2. Highlights: PR summaries from PRs labeled `whats-new`, fetched via the
     GitHub CLI (requires GH_TOKEN env var; silently skipped if unavailable).

Usage:
    python scripts/generate_whats_new.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
OUTPUT_PATH = REPO_ROOT / "docs" / "website" / "docs" / "whats-new.md"
GITHUB_REPO = "trivoallan/regis-cli"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"

# Map CHANGELOG section names to display icons.
# Sections mapped to None are excluded from the output.
SECTION_ICONS: dict[str, str | None] = {
    "Features": "✨",
    "Bug Fixes": "🐛",
    "Documentation": "📚",
    "Dependencies": None,  # Dependabot noise — skip
}


@dataclass
class VersionBlock:
    version: str  # e.g. "0.22.0"
    date: str  # ISO date "YYYY-MM-DD"
    compare_url: str
    sections: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class PRHighlight:
    number: int
    title: str
    summary: str  # cleaned body of the PR's ## Summary section


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _strip_commit_hash_link(text: str) -> str:
    """Remove trailing ([abcdef1](…/commit/…)) from a changelog entry line."""
    return re.sub(
        r"\s*\(\[`?[0-9a-f]{7,40}`?\]\("
        r"https://github\.com/[^)]+/commit/[0-9a-f]+\)\)\s*$",
        "",
        text,
    )


def _capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def parse_changelog(path: Path) -> list[VersionBlock]:
    """Parse CHANGELOG.md into VersionBlock objects.

    Only handles Release Please-managed versions (X.Y.Z with date).
    Older hand-written entries (v0.5.0 and below) are ignored.
    """
    content = path.read_text(encoding="utf-8")

    # Match: ## [X.Y.Z](compare_url) (YYYY-MM-DD)
    version_re = re.compile(
        r"^## \[(\d+\.\d+\.\d+)\]\((https://[^)]+)\)\s+\((\d{4}-\d{2}-\d{2})\)",
        re.MULTILINE,
    )
    section_re = re.compile(r"^### (.+)$", re.MULTILINE)

    matches = list(version_re.finditer(content))
    blocks: list[VersionBlock] = []

    for i, m in enumerate(matches):
        version, compare_url, date = m.group(1), m.group(2), m.group(3)

        block_start = m.end()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block_text = content[block_start:block_end]

        sec_matches = list(section_re.finditer(block_text))
        sections: dict[str, list[str]] = {}

        for j, sec_m in enumerate(sec_matches):
            sec_name = sec_m.group(1).strip()
            icon = SECTION_ICONS.get(sec_name, "🔧")
            if icon is None:
                continue  # explicitly excluded section

            sec_start = sec_m.end()
            sec_end = (
                sec_matches[j + 1].start()
                if j + 1 < len(sec_matches)
                else len(block_text)
            )
            sec_text = block_text[sec_start:sec_end]

            entries = [
                _capitalize_first(_strip_commit_hash_link(line[2:]))
                for line in sec_text.splitlines()
                if line.strip().startswith("- ")
            ]
            if entries:
                sections[sec_name] = entries

        if sections:
            blocks.append(
                VersionBlock(
                    version=version,
                    date=date,
                    compare_url=compare_url,
                    sections=sections,
                )
            )

    return blocks


# ---------------------------------------------------------------------------
# GitHub highlights
# ---------------------------------------------------------------------------


def _extract_summary_section(body: str) -> str:
    """Extract text under '## Summary' from a PR body."""
    if not body:
        return ""
    m = re.search(
        r"^##\s+Summary\s*\n(.*?)(?=^##|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(1).strip() if m else ""


def _parse_merged_at(iso: str) -> datetime:
    """Parse a GitHub ISO 8601 timestamp to a UTC-aware datetime."""
    # e.g. "2026-03-30T17:28:25Z"
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fetch_highlights(
    version_blocks: list[VersionBlock],
) -> dict[str, list[PRHighlight]]:
    """Return per-version PR highlights for PRs labeled `whats-new`.

    Requires the `gh` CLI and GH_TOKEN env var. Returns an empty dict on any
    failure so the caller can proceed without highlights.
    """
    if not os.environ.get("GH_TOKEN"):
        return {}

    try:
        result = subprocess.run(  # nosec B603 B607
            [
                "gh",
                "pr",
                "list",
                "--repo",
                GITHUB_REPO,
                "--label",
                "whats-new",
                "--state",
                "merged",
                "--limit",
                "200",
                "--json",
                "number,title,body,mergedAt",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"  gh pr list failed: {result.stderr.strip()}", file=sys.stderr)
            return {}
        prs: list[dict] = json.loads(result.stdout)
    except Exception as exc:
        print(f"  Could not fetch highlights: {exc}", file=sys.stderr)
        return {}

    highlights: dict[str, list[PRHighlight]] = {}

    # version_blocks are ordered newest-first (same as CHANGELOG).
    # Build date windows: (prev_version_date, current_version_date].
    for i, block in enumerate(version_blocks):
        year, month, day = (int(p) for p in block.date.split("-"))
        current_dt = datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)
        prev_block = version_blocks[i + 1] if i + 1 < len(version_blocks) else None
        if prev_block:
            py, pm, pd = (int(p) for p in prev_block.date.split("-"))
            prev_dt = datetime(py, pm, pd, tzinfo=timezone.utc)
        else:
            prev_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)

        version_prs = [
            PRHighlight(number=pr["number"], title=pr["title"], summary=summary)
            for pr in prs
            if (
                pr.get("mergedAt")
                and prev_dt < _parse_merged_at(pr["mergedAt"]) <= current_dt
                and (summary := _extract_summary_section(pr.get("body", "")))
            )
        ]
        if version_prs:
            highlights[block.version] = version_prs

    return highlights


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _format_date(iso_date: str) -> str:
    """Format 'YYYY-MM-DD' as 'Month D, YYYY'."""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y")


def _render_highlights_block(prs: list[PRHighlight]) -> str:
    parts = [":::info[Highlights]", ""]
    for pr in prs:
        parts.append(
            f"**{pr.title}** ([#{pr.number}]({GITHUB_REPO_URL}/pull/{pr.number}))"
        )
        parts.append("")
        parts.append(pr.summary)
        parts.append("")
    parts.append(":::")
    return "\n".join(parts)


def render_page(
    version_blocks: list[VersionBlock],
    highlights: dict[str, list[PRHighlight]],
) -> str:
    """Render the full What's New MDX page."""
    out: list[str] = [
        "---",
        "sidebar_position: 1.5",
        "title: What's New",
        "description: New features and improvements in each release of regis-cli.",
        "---",
        "",
        "<!-- This file is auto-generated by scripts/generate_whats_new.py — do not edit manually -->",
        "",
        "A summary of new features and improvements in each release of **regis-cli**.",
        f"For the complete list of changes, see the [full changelog]({GITHUB_REPO_URL}/blob/main/CHANGELOG.md).",
        "",
    ]

    for block in version_blocks:
        out += [
            "---",
            "",
            f"## [v{block.version}]({block.compare_url}) — {_format_date(block.date)}",
            "",
        ]

        version_highlights = highlights.get(block.version, [])
        if version_highlights:
            out += [_render_highlights_block(version_highlights), ""]

        for sec_name, entries in block.sections.items():
            icon = SECTION_ICONS.get(sec_name, "🔧")
            out += [f"### {icon} {sec_name}", ""]
            for entry in entries:
                out.append(f"- {entry}")
            out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if not CHANGELOG_PATH.exists():
        print(f"ERROR: {CHANGELOG_PATH} not found", file=sys.stderr)
        sys.exit(1)

    print("Parsing CHANGELOG.md…", file=sys.stderr)
    version_blocks = parse_changelog(CHANGELOG_PATH)
    print(f"  {len(version_blocks)} versioned entries found.", file=sys.stderr)

    print("Fetching PR highlights…", file=sys.stderr)
    highlights = fetch_highlights(version_blocks)
    if highlights:
        total = sum(len(v) for v in highlights.values())
        print(
            f"  {total} highlighted PR(s) across {len(highlights)} version(s).",
            file=sys.stderr,
        )
    else:
        print(
            "  No highlights (GH_TOKEN not set or no `whats-new` labeled PRs found).",
            file=sys.stderr,
        )

    print(f"Writing {OUTPUT_PATH.relative_to(REPO_ROOT)}…", file=sys.stderr)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_page(version_blocks, highlights), encoding="utf-8")
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
