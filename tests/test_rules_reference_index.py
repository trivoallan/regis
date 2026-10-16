"""The hand-written rules index must link every generated rule page, and only those."""

from __future__ import annotations

import re
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parent.parent / "docs" / "reference" / "rules"
LINK = re.compile(r"\]\(\./([^)#\s]+\.md)\)")


def test_rules_index_links_every_rule_page() -> None:
    index = (RULES_DIR / "README.md").read_text(encoding="utf-8")
    linked = set(LINK.findall(index))
    pages = {p.relative_to(RULES_DIR).as_posix() for p in RULES_DIR.glob("*/*.md")}

    assert pages, "no generated rule page found: run `make reference`"
    assert linked - pages == set(), "docs/reference/rules/README.md links missing pages"
    assert pages - linked == set(), (
        "rule pages missing from docs/reference/rules/README.md"
    )
