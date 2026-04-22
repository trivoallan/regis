#!/usr/bin/env python3
"""Verify S01 snapshot retention policy acceptance criteria."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures = []


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{': ' + detail if detail else ''}")
    if not ok:
        failures.append(name)


# 1. release-snapshot.yml has is_minor guard on snapshot-pending job
wf = (ROOT / ".github/workflows/release-snapshot.yml").read_text()
has_is_minor_output = bool(re.search(r"is_minor\s*:", wf))
has_snapshot_if = bool(re.search(r"if:.*is_minor.*==.*'true'", wf))
check(
    "release-snapshot.yml has is_minor guard on snapshot-pending",
    has_is_minor_output and has_snapshot_if,
    f"output={has_is_minor_output} if-guard={has_snapshot_if}",
)

# 2. versions.json has exactly 3 entries and no v0.24.0
versions_path = ROOT / "docs/website/versions.json"
versions = json.loads(versions_path.read_text())
no_024 = "v0.24.0" not in versions
check(
    "versions.json has exactly 3 entries",
    len(versions) == 3,
    f"entries={versions}",
)
check(
    "versions.json does not contain v0.24.0",
    no_024,
    f"entries={versions}",
)

# 3. No versioned_docs/version-v0.24.0 directory
versioned_docs = ROOT / "docs/website/versioned_docs"
v024_docs = versioned_docs / "version-v0.24.0"
check(
    "versioned_docs/version-v0.24.0 does not exist",
    not v024_docs.exists(),
)

# 4. No versioned_sidebars/version-v0.24.0-sidebars.json
versioned_sidebars = ROOT / "docs/website/versioned_sidebars"
v024_sidebar = versioned_sidebars / "version-v0.24.0-sidebars.json"
check(
    "versioned_sidebars/version-v0.24.0-sidebars.json does not exist",
    not v024_sidebar.exists(),
)

if failures:
    print(f"\n{len(failures)} check(s) FAILED: {failures}")
    sys.exit(1)
else:
    print("\nAll checks PASSED.")
    sys.exit(0)
