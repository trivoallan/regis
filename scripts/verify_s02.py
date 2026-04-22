#!/usr/bin/env python3
"""Verify S02 snapshot publication date acceptance criteria."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures = []


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{': ' + detail if detail else ''}")
    if not ok:
        failures.append(name)


# 1. snapshot_dates.json has dates for v0.27.0 and v0.26.2
dates_path = ROOT / "regis/data/snapshot_dates.json"
dates = json.loads(dates_path.read_text())
check(
    "regis/data/snapshot_dates.json: v0.27.0 date == 2026-04-09",
    dates.get("v0.27.0", {}).get("date") == "2026-04-09",
    str(dates.get("v0.27.0")),
)
check(
    "regis/data/snapshot_dates.json: v0.26.2 date == 2026-04-03",
    dates.get("v0.26.2", {}).get("date") == "2026-04-03",
    str(dates.get("v0.26.2")),
)

# 2. docs mirror has the same dates
web_dates_path = ROOT / "docs/website/snapshot-dates.json"
web_dates = json.loads(web_dates_path.read_text())
check(
    "docs/website/snapshot-dates.json: v0.27.0 date == 2026-04-09",
    web_dates.get("v0.27.0", {}).get("date") == "2026-04-09",
    str(web_dates.get("v0.27.0")),
)
check(
    "docs/website/snapshot-dates.json: v0.26.2 date == 2026-04-03",
    web_dates.get("v0.26.2", {}).get("date") == "2026-04-03",
    str(web_dates.get("v0.26.2")),
)

# 3. analyze.py has --markdown flag
analyze_src = (ROOT / "regis/commands/analyze.py").read_text()
check(
    "regis/commands/analyze.py: --markdown flag present",
    "--markdown" in analyze_src,
)
check(
    'regis/commands/analyze.py: formats.append("md") present',
    'formats.append("md")' in analyze_src,
)

# 4. report.py has elif fmt == "md" branch
report_src = (ROOT / "regis/utils/report.py").read_text()
check(
    'regis/utils/report.py: elif fmt == "md" branch present',
    'elif fmt == "md":' in report_src,
)

if failures:
    print(f"\n{len(failures)} check(s) FAILED: {failures}")
    sys.exit(1)
else:
    print("\nAll checks PASSED.")
    sys.exit(0)
