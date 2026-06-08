"""Shared verdict model for human-facing `regis analyze` output.

A single normalization point (`build_verdict`) feeds three thin renderers
(terminal, markdown, HTML) so a given tier renders identically everywhere.
Pure: no I/O, no click, no Jinja.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- Mapping tables (single source of truth) ---

TIER_FALLBACK_ICON = "🏷️"  # tier defined without a declared icon
TIER_NONE_LABEL = "⚪ Unrated"  # no tier condition matched

# Badge `class` is a fixed engine enum (not user-defined).
CLASS_EMOJI = {"error": "🟥", "warning": "🟧", "success": "🟩"}
# Rule `level` is a fixed engine enum.
LEVEL_EMOJI = {"critical": "🟥", "warning": "🟧", "info": "🟦"}
# click text colours (click has no orange; warning text falls back to yellow,
# the orange square emoji carries the medal-disambiguation).
LEVEL_STYLE = {"critical": "red", "warning": "yellow", "info": "blue"}

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class RuleLine:
    slug: str
    level: str
    message: str


@dataclass(frozen=True)
class VerdictBadge:
    label: str
    klass: str


@dataclass(frozen=True)
class Verdict:
    evaluated: bool
    tier: str | None
    tier_icon: str | None
    score: int
    total: int
    passed: int
    failed: int
    incomplete: int
    worst_level: str | None
    badges: list[VerdictBadge] = field(default_factory=list)
    failures: list[RuleLine] = field(default_factory=list)
    incompletes: list[RuleLine] = field(default_factory=list)


def tier_label(tier: str | None, icon: str | None) -> str:
    """Render the tier headline label, e.g. '🥇 Gold' / '🏷️ Custom' / '⚪ Unrated'."""
    if not tier:
        return TIER_NONE_LABEL
    return f"{icon or TIER_FALLBACK_ICON} {tier}"


def badge_emoji(klass: str) -> str:
    """Emoji for a badge `class`; empty string for unknown/neutral classes."""
    return CLASS_EMOJI.get(klass, "")


def level_emoji(level: str | None) -> str:
    """Emoji for a rule `level`; empty string when unknown/None."""
    return LEVEL_EMOJI.get(str(level).lower(), "") if level else ""


def _source(final_report: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the playbook result to render: playbooks[0], else top-level hoisted."""
    playbooks = final_report.get("playbooks") or []
    if playbooks:
        return playbooks[0]
    if "tier" in final_report or "rules" in final_report:
        return final_report
    return None


def build_verdict(final_report: dict[str, Any]) -> Verdict:
    """Normalize a final report into a render-ready Verdict."""
    src = _source(final_report)
    if src is None:
        return Verdict(
            evaluated=False,
            tier=None,
            tier_icon=None,
            score=0,
            total=0,
            passed=0,
            failed=0,
            incomplete=0,
            worst_level=None,
        )

    rules = list(src.get("rules") or [])
    passed = [r for r in rules if r.get("passed")]
    failed = [
        r for r in rules if not r.get("passed") and r.get("status") != "incomplete"
    ]
    incomplete = [r for r in rules if r.get("status") == "incomplete"]

    worst_level = None
    if failed:
        worst_level = min(
            (str(r.get("level") or "info").lower() for r in failed),
            key=lambda lv: _SEVERITY_ORDER.get(lv, 99),
        )

    badges = [
        VerdictBadge(label=b.get("name", ""), klass=b.get("class", ""))
        for b in (src.get("badge_labels") or [])
    ]

    def _line(r: dict[str, Any]) -> RuleLine:
        return RuleLine(
            slug=r.get("slug", "unknown"),
            level=str(r.get("level") or "info").lower(),
            message=r.get("message", ""),
        )

    summary = src.get("rules_summary") or {}
    return Verdict(
        evaluated=True,
        tier=src.get("tier"),
        tier_icon=src.get("tier_icon"),
        score=int(summary.get("score", 0)),
        total=summary.get("total", len(rules)),
        passed=len(passed),
        failed=len(failed),
        incomplete=len(incomplete),
        worst_level=worst_level,
        badges=badges,
        failures=[_line(r) for r in failed],
        incompletes=[_line(r) for r in incomplete],
    )
