"""Per-file coverage gate.

coverage.py only enforces a *global* ``fail_under`` threshold, so a poorly
tested file can hide behind well-covered ones. After pytest-cov writes its data,
this gate loads it and fails the session if any measured file is below the same
threshold (read from ``[tool.coverage.report].fail_under``). Wired in via
``tests/conftest.py``. Spec:
docs/superpowers/specs/2026-06-08-per-file-coverage-gate-design.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback
    import tomli as tomllib

import coverage
import pytest


def read_threshold(rootpath: Path) -> float:
    """Read the shared coverage threshold from ``[tool.coverage.report]``."""
    data = tomllib.loads((rootpath / "pyproject.toml").read_text(encoding="utf-8"))
    return float(data["tool"]["coverage"]["report"]["fail_under"])


def evaluate_coverage(
    stats: dict[str, tuple[int, int]], threshold: float
) -> list[tuple[str, float]]:
    """Return ``[(path, percent)]`` for files below ``threshold``, worst first.

    ``stats`` maps a display path to ``(n_statements, n_missing)``. Files with
    zero statements are skipped. The percentage is rounded to two decimals before
    comparison, mirroring coverage.py's reporting precision.
    """
    offenders: list[tuple[str, float]] = []
    for path, (n_statements, n_missing) in stats.items():
        if n_statements == 0:
            continue
        percent = 100.0 * (n_statements - n_missing) / n_statements
        if round(percent, 2) < threshold:
            offenders.append((path, percent))
    offenders.sort(key=lambda item: (item[1], item[0]))
    return offenders


def _collect_stats(rootpath: Path) -> dict[str, tuple[int, int]]:
    """Load on-disk coverage data into ``{display_path: (n_statements, n_missing)}``."""
    cov = coverage.Coverage()  # reads [tool.coverage] config (omit, etc.)
    cov.load()
    data = cov.get_data()
    stats: dict[str, tuple[int, int]] = {}
    for filename in data.measured_files():
        _, statements, _excluded, missing, _fmt = cov.analysis2(filename)
        try:
            display = str(Path(filename).relative_to(rootpath))
        except ValueError:
            display = filename
        stats[display] = (len(statements), len(missing))
    return stats


def enforce(session: pytest.Session) -> None:
    """Fail the pytest session if any measured file is below the threshold."""
    option = session.config.option
    if getattr(option, "no_cov", False) or not getattr(option, "cov_source", None):
        return  # coverage disabled (e.g. --no-cov): nothing to check
    rootpath = Path(session.config.rootpath)
    threshold = read_threshold(rootpath)
    offenders = evaluate_coverage(_collect_stats(rootpath), threshold)
    if not offenders:
        return
    lines = [f"Per-file coverage gate: {len(offenders)} file(s) below {threshold:.1f}%"]
    lines += [f"  {percent:5.1f}%  {path}" for path, percent in offenders]
    print("\n" + "\n".join(lines), file=sys.stderr)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
