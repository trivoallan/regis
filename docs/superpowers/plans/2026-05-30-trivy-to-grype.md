# Replace Trivy with Grype + Syft + TruffleHog — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single `trivy` binary with three capability-named analyzers — `cve` (grype), `secrets` (trufflehog), `sbom` (syft) — deleting `TrivyAnalyzer` and renaming the report providers accordingly.

**Architecture:** One thin subprocess wrapper per tool under `regis/utils/` (mirroring `regis/utils/regctl.py`), each consumed by a `BaseAnalyzer` subclass. Analyzers stay independent and run in the existing `ThreadPoolExecutor` — no cross-analyzer chaining. Report field names stay stable; only the provider prefix changes (`results.trivy.*` → `results.cve.*` / `results.secrets.*`).

**Tech Stack:** Python 3.14, Click, pytest (≥ 90 % coverage gate), JSON Schema (draft 2020-12), JSON Logic, Docker multi-stage build, Trunk (lint/format), Docusaurus + Tremor (dashboard, pnpm). Pinned tool versions (confirmed in Task 1 spike): grype `v0.112.0`, syft `v1.44.0`, trufflehog `v3.95.3`.

**Spike corrections (Task 1 findings — these override the originally-drafted code below where they conflict):**

1. **Registry auth env vars:** grype has **no** `GRYPE_REGISTRY_AUTH_*` variable. Both grype **and** syft honor `SYFT_REGISTRY_AUTH_USERNAME` / `SYFT_REGISTRY_AUTH_PASSWORD`. The grype wrapper (Task 2) uses the `SYFT_REGISTRY_AUTH_*` names.
2. **syft version** lives at `metadata.tools.components[]` (a dict with a `components` array), not a flat array — the `_syft_version` helper in Task 5 already handles both shapes.
3. **grype `fix.state`** emits `""` (empty string) for the unknown case alongside `fixed`/`not-fixed`/`wont-fix`. `fixed_count` only counts `state == "fixed"`, so no code change is needed, but tests should not assume `"unknown"`.
4. **trufflehog exit code** is `0` even when secrets are found (non-zero `183` only with `--fail`). The wrapper uses `check=False` and counts NDJSON lines, so this is already correct. A failed remote pull also yields exit 0 + empty stdout — documented as a known limitation in a wrapper comment.
5. **trufflehog has no basic user/pass env pair.** Credentials, when present, are forwarded via a temporary `DOCKER_CONFIG` (same pattern as `regis/utils/regctl.py::_temp_docker_config`); see Task 6.

**Spec:** `docs/superpowers/specs/2026-05-30-trivy-to-grype-design.md`

**Conventions for every task:**

- Fast test loop: `pipenv run pytest <path> --no-cov`. Full gate before PR: `pipenv run pytest` (fails under 90 % coverage).
- Commit messages: Conventional Commits with mandatory scope. Trunk's pre-commit hook auto-fixes; re-stage and re-commit the produced changes if the first `git commit` is blocked.
- Patch targets in tests: patch at the source module (`regis.utils.<tool>.{subprocess,shutil}`, `regis.analyzers.<name>.*`), never `regis.cli.*`.
- The branch is already a feature worktree; commit directly to it.

---

## File Structure

| File                                                                    | Responsibility                                            | Action |
| ----------------------------------------------------------------------- | --------------------------------------------------------- | ------ |
| `regis/utils/grype.py`                                                  | Run grype, inject creds, return parsed JSON               | Create |
| `regis/utils/syft.py`                                                   | Run syft, inject creds, return parsed CycloneDX           | Create |
| `regis/utils/trufflehog.py`                                             | Run trufflehog, parse NDJSON, tolerate findings exit code | Create |
| `regis/analyzers/cve.py`                                                | `CveAnalyzer` — map grype JSON → report                   | Create |
| `regis/analyzers/secrets.py`                                            | `SecretsAnalyzer` — map trufflehog findings → report      | Create |
| `regis/analyzers/sbom.py`                                               | `SbomAnalyzer` — swap backend trivy → syft                | Modify |
| `regis/analyzers/trivy.py`                                              | —                                                         | Delete |
| `regis/schemas/analyzer/cve.schema.json`                                | Output contract for `cve`                                 | Create |
| `regis/schemas/analyzer/secrets.schema.json`                            | Output contract for `secrets`                             | Create |
| `regis/schemas/analyzer/sbom.schema.json`                               | Add `scanner_version`                                     | Modify |
| `regis/schemas/analyzer/trivy.schema.json`                              | —                                                         | Delete |
| `pyproject.toml`                                                        | Entry points: drop `trivy`, add `cve`, `secrets`          | Modify |
| `regis/playbooks/default/playbook.yaml`                                 | `provider: trivy` → `cve`                                 | Modify |
| `regis/commands/doctor.py`                                              | Required-tools list                                       | Modify |
| `Dockerfile`                                                            | Fetch + copy grype/syft/trufflehog, drop trivy            | Modify |
| `.github/workflows/cd-docs.yml`                                         | Install grype/syft/trufflehog                             | Modify |
| `.github/workflows/ci-image-size.yml`                                   | Comments / ceiling                                        | Modify |
| `apps/dashboard/src/components/CveSection.tsx`                          | ex-`TrivySection.tsx`                                     | Rename |
| `apps/dashboard/src/components/SecretsSection.tsx`                      | Secrets rendering                                         | Create |
| `apps/dashboard/src/components/AnalyzerSection.tsx`                     | Switch cases                                              | Modify |
| `apps/dashboard/src/components/Dashboard/AnalyzerCoverageCard.tsx`      | Label map                                                 | Modify |
| `apps/dashboard/src/components/Dashboard/VulnerabilityChart.tsx`        | "Detected by Grype"                                       | Modify |
| `apps/dashboard/src/components/SummaryView.tsx`                         | `results.cve`                                             | Modify |
| `apps/dashboard/docs/analyzers/cve.mdx`                                 | ex-`trivy.mdx`                                            | Rename |
| `apps/dashboard/docs/analyzers/secrets.mdx`                             | Secrets analyzer page                                     | Create |
| `tests/test_grype.py`, `tests/test_syft.py`, `tests/test_trufflehog.py` | Wrapper tests                                             | Create |
| `tests/test_analyzer_cve.py`, `tests/test_analyzer_secrets.py`          | Analyzer tests                                            | Create |
| `tests/test_sbom.py`                                                    | Update for syft backend                                   | Modify |
| `tests/test_trivy.py`, `tests/test_analyzer_trivy.py`                   | —                                                         | Delete |
| `tests/commands/test_doctor.py`                                         | New tool list                                             | Modify |
| `tests/fixtures/{grype,syft,trufflehog}/`                               | Captured real outputs                                     | Create |
| `CLAUDE.md`                                                             | Required-binaries line                                    | Modify |

---

## Task 1: Spike — install tools, capture fixtures, confirm open questions

This resolves spec §10 open questions empirically so later tasks use real shapes. No production code. Mirrors the regctl spike.

**Files:**

- Create: `tests/fixtures/grype/`, `tests/fixtures/syft/`, `tests/fixtures/trufflehog/`
- Create: `docs/superpowers/plans/2026-05-30-grype-probe-notes.md`

- [ ] **Step 1: Install the three tools locally**

```bash
# macOS (Homebrew)
brew install grype syft trufflehog
grype version
syft version
trufflehog --version
```

Record the exact version sub-command for each (`version` vs `--version`) and whether output goes to stdout or stderr.

- [ ] **Step 2: Capture fixtures against a stable public image**

```bash
mkdir -p tests/fixtures/grype tests/fixtures/syft tests/fixtures/trufflehog
REF=alpine:3.20

grype "$REF" -o json                 > tests/fixtures/grype/alpine_json.json
syft "$REF" -o cyclonedx-json        > tests/fixtures/syft/alpine_cyclonedx.json
trufflehog docker --image "$REF" --json --no-update 2> tests/fixtures/trufflehog/stderr.txt \
    > tests/fixtures/trufflehog/alpine_ndjson.txt; echo "exit=$?" >> tests/fixtures/trufflehog/stderr.txt
```

- [ ] **Step 3: Record findings in the probe note**

Document in `2026-05-30-grype-probe-notes.md`:

1. Version sub-command + stream for each tool.
2. grype: confirm `descriptor.version`, `matches[].vulnerability.severity` value set (Critical/High/Medium/Low/Negligible/Unknown), `matches[].vulnerability.fix.state` value set (expect `fixed`/`not-fixed`/`wont-fix`/`unknown`), `matches[].artifact.{name,version,type}`.
3. syft: confirm `bomFormat`, `specVersion`, `components[]`, `dependencies[]`, and where the syft version lives (`metadata.tools` — array vs `metadata.tools.components[]`).
4. trufflehog: confirm `--json` emits NDJSON (one object per line), the finding fields (`DetectorName`, `Verified`, `Redacted`, `Raw`, `SourceMetadata`), and the **exit code when secrets are found** (expect non-zero, e.g. 183) and when none are found (expect 0).
5. Credential env vars: confirm grype reads `GRYPE_REGISTRY_AUTH_USERNAME`/`GRYPE_REGISTRY_AUTH_PASSWORD` (or Docker config), syft reads `SYFT_REGISTRY_AUTH_USERNAME`/`SYFT_REGISTRY_AUTH_PASSWORD`, and how trufflehog authenticates to a private registry.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures docs/superpowers/plans/2026-05-30-grype-probe-notes.md
git commit -m "test(cve): capture grype/syft/trufflehog probe fixtures"
```

> If any captured shape contradicts the code below (field names, exit codes, env vars), adjust the affected task's code to match the fixture — the fixture is ground truth.

---

## Task 2: grype subprocess wrapper

**Files:**

- Create: `regis/utils/grype.py`
- Test: `tests/test_grype.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the grype subprocess wrapper."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.utils.grype import run_grype

_SAMPLE = '{"descriptor": {"name": "grype", "version": "0.80.2"}, "matches": []}'


class TestRunGrype:
    @patch("regis.utils.grype.shutil.which")
    def test_not_found(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(AnalyzerError, match="grype executable not found"):
            run_grype("alpine:3.20")

    @patch("regis.utils.grype.shutil.which")
    @patch("regis.utils.grype.subprocess.run")
    def test_success_and_args(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/grype"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)

        result = run_grype("alpine:3.20")
        assert result["descriptor"]["version"] == "0.80.2"

        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/local/bin/grype"
        assert args[1] == "alpine:3.20"
        assert "json" in args  # -o json

    @patch("regis.utils.grype.shutil.which")
    @patch("regis.utils.grype.subprocess.run")
    def test_creds_and_platform(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/grype"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)

        run_grype("alpine:3.20", username="u", password="p", platform="linux/arm64")

        args = mock_run.call_args[0][0]
        env = mock_run.call_args[1]["env"]
        assert "--platform" in args and "linux/arm64" in args
        # grype has no GRYPE_REGISTRY_AUTH_*; it honors the syft auth env vars.
        assert env["SYFT_REGISTRY_AUTH_USERNAME"] == "u"
        assert env["SYFT_REGISTRY_AUTH_PASSWORD"] == "p"

    @patch("regis.utils.grype.shutil.which")
    @patch("regis.utils.grype.subprocess.run")
    def test_called_process_error(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/grype"
        mock_run.side_effect = subprocess.CalledProcessError(1, ["grype"], stderr="boom")
        with pytest.raises(AnalyzerError, match="grype failed: boom"):
            run_grype("alpine:3.20")

    @patch("regis.utils.grype.shutil.which")
    @patch("regis.utils.grype.subprocess.run")
    def test_invalid_json(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/grype"
        mock_run.return_value = MagicMock(stdout="not-json")
        with pytest.raises(AnalyzerError, match="grype produced invalid"):
            run_grype("alpine:3.20")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_grype.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: regis.utils.grype`.

- [ ] **Step 3: Write the wrapper**

```python
"""Subprocess wrapper for the grype vulnerability scanner.

Centralizes grype invocation, registry-credential injection, and JSON parsing.
Mirrors regis/utils/regctl.py.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess  # nosec B404
from typing import Any

from regis.analyzers.base import AnalyzerError

logger = logging.getLogger(__name__)

#: Default timeout for grype calls (seconds). Image cataloging can be slow.
DEFAULT_TIMEOUT = 300


def run_grype(
    image: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Run ``grype <image> -o json`` and return parsed JSON.

    Args:
        image: Full image reference (e.g. ``registry/repo:tag``).
        username: Optional registry username.
        password: Optional registry password.
        platform: Optional platform string (e.g. ``linux/arm64``).
        timeout: Subprocess timeout in seconds.

    Returns:
        The parsed grype JSON document.

    Raises:
        AnalyzerError: if grype is missing, fails, or emits invalid JSON.
    """
    grype_path = shutil.which("grype")
    if not grype_path:
        raise AnalyzerError("grype executable not found in PATH")

    env = os.environ.copy()
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")
    if user and pwd:
        # grype vendors syft's image loader and honors the SYFT_* auth env vars;
        # there is no GRYPE_REGISTRY_AUTH_* equivalent (confirmed in the spike).
        env["SYFT_REGISTRY_AUTH_USERNAME"] = user
        env["SYFT_REGISTRY_AUTH_PASSWORD"] = pwd

    cmd = [grype_path, image, "-o", "json"]
    if platform:
        cmd.extend(["--platform", platform])

    logger.debug("Running grype on %s", image)
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            env=env,
        )
        return json.loads(result.stdout)  # type: ignore[no-any-return]
    except subprocess.CalledProcessError as exc:
        raise AnalyzerError(f"grype failed: {exc.stderr}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalyzerError(f"grype timed out after {timeout}s") from exc
    except json.JSONDecodeError as exc:
        raise AnalyzerError(f"grype produced invalid JSON: {exc}") from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/test_grype.py --no-cov`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add regis/utils/grype.py tests/test_grype.py
git commit -m "feat(cve): add grype subprocess wrapper"
```

---

## Task 3: cve.schema.json + CveAnalyzer

**Files:**

- Create: `regis/schemas/analyzer/cve.schema.json`
- Create: `regis/analyzers/cve.py`
- Modify: `pyproject.toml` (add `cve` entry point)
- Test: `tests/test_analyzer_cve.py`

- [ ] **Step 1: Write the schema**

`regis/schemas/analyzer/cve.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://trivoallan.github.io/regis/schemas/analyzer/cve.schema.json",
  "title": "cve.output",
  "description": "Vulnerability scan results from Grype.",
  "type": "object",
  "required": [
    "analyzer",
    "repository",
    "tag",
    "scanner_version",
    "vulnerability_count",
    "critical_count",
    "high_count",
    "medium_count",
    "low_count",
    "negligible_count",
    "unknown_count",
    "fixed_count",
    "targets"
  ],
  "properties": {
    "analyzer": { "type": "string", "const": "cve" },
    "repository": { "type": "string" },
    "tag": { "type": "string" },
    "scanner_version": {
      "type": "string",
      "description": "Version of the grype CLI used."
    },
    "vulnerability_count": { "type": "integer", "minimum": 0 },
    "critical_count": { "type": "integer", "minimum": 0 },
    "high_count": { "type": "integer", "minimum": 0 },
    "medium_count": { "type": "integer", "minimum": 0 },
    "low_count": { "type": "integer", "minimum": 0 },
    "negligible_count": { "type": "integer", "minimum": 0 },
    "unknown_count": { "type": "integer", "minimum": 0 },
    "fixed_count": { "type": "integer", "minimum": 0 },
    "targets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["Target", "Vulnerabilities"],
        "properties": {
          "Target": {
            "type": "string",
            "description": "Artifact type (apk, deb, python, …)."
          },
          "Vulnerabilities": {
            "type": ["array", "null"],
            "items": {
              "type": "object",
              "required": [
                "VulnerabilityID",
                "PkgName",
                "InstalledVersion",
                "Severity"
              ],
              "properties": {
                "VulnerabilityID": { "type": "string" },
                "PkgName": { "type": "string" },
                "InstalledVersion": { "type": "string" },
                "FixedVersion": { "type": "string" },
                "Severity": { "type": "string" },
                "Title": { "type": "string" },
                "Description": { "type": "string" }
              }
            }
          }
        }
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Write the failing test**

`tests/test_analyzer_cve.py`:

```python
"""Tests for the CVE analyzer (grype backend)."""

from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.cve import CveAnalyzer

# Minimal grype JSON: two matches across two artifact types, mixed severities.
_GRYPE = {
    "descriptor": {"name": "grype", "version": "0.80.2"},
    "matches": [
        {
            "vulnerability": {
                "id": "CVE-2024-0001",
                "severity": "Critical",
                "description": "bad thing",
                "fix": {"versions": ["1.2.3"], "state": "fixed"},
            },
            "artifact": {"name": "libfoo", "version": "1.2.2", "type": "apk"},
        },
        {
            "vulnerability": {
                "id": "CVE-2024-0002",
                "severity": "Negligible",
                "description": "",
                "fix": {"versions": [], "state": "not-fixed"},
            },
            "artifact": {"name": "pybar", "version": "0.9", "type": "python"},
        },
    ],
}


@pytest.fixture
def analyzer():
    return CveAnalyzer()


class TestCveAnalyzer:
    def test_default_rules_slugs(self, analyzer):
        slugs = {r["slug"] for r in analyzer.default_rules()}
        assert {"fix-available", "cve-count"} <= slugs

    @patch("regis.analyzers.cve.run_grype")
    def test_analyze_counts_and_targets(self, mock_run, analyzer):
        mock_run.return_value = _GRYPE
        client = MagicMock()
        client.registry = "docker.io"
        client.username = None
        client.password = None

        report = analyzer.analyze(client, "library/alpine", "3.20")

        assert report["analyzer"] == "cve"
        assert report["scanner_version"] == "0.80.2"
        assert report["vulnerability_count"] == 2
        assert report["critical_count"] == 1
        assert report["negligible_count"] == 1
        assert report["fixed_count"] == 1
        # Grouped by artifact.type
        targets = {t["Target"]: t for t in report["targets"]}
        assert set(targets) == {"apk", "python"}
        apk_vuln = targets["apk"]["Vulnerabilities"][0]
        assert apk_vuln["VulnerabilityID"] == "CVE-2024-0001"
        assert apk_vuln["PkgName"] == "libfoo"
        assert apk_vuln["FixedVersion"] == "1.2.3"
        # Report must validate against the schema.
        analyzer.validate(report)

    @patch("regis.analyzers.cve.run_grype")
    def test_analyze_forwards_error(self, mock_run, analyzer):
        mock_run.side_effect = AnalyzerError("boom")
        client = MagicMock()
        client.registry = "example.com"
        with pytest.raises(AnalyzerError, match="boom"):
            analyzer.analyze(client, "repo", "tag")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pipenv run pytest tests/test_analyzer_cve.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: regis.analyzers.cve`.

- [ ] **Step 4: Write the analyzer**

`regis/analyzers/cve.py`:

```python
"""CVE analyzer — scans images for vulnerabilities using grype."""

from __future__ import annotations

import logging
from typing import Any

from regis.analyzers.base import AnalyzerError, BaseAnalyzer
from regis.registry.client import RegistryClient
from regis.utils.grype import run_grype

logger = logging.getLogger(__name__)

#: Maps grype severity strings to the report's count field.
_SEVERITY_FIELD = {
    "Critical": "critical_count",
    "High": "high_count",
    "Medium": "medium_count",
    "Low": "low_count",
    "Negligible": "negligible_count",
    "Unknown": "unknown_count",
}


class CveAnalyzer(BaseAnalyzer):
    """Scan an image for vulnerabilities using grype."""

    name = "cve"
    schema_file = "analyzer/cve.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "fix-available",
                "description": "All vulnerabilities should be fixed if a patch exists.",
                "level": "warning",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.cve.fixed_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "All vulnerabilities with available fixes have been patched.",  # nosec B105
                    "fail": "Image has ${results.cve.fixed_count} vulnerabilities with available fixes.",
                },
            },
            {
                "slug": "cve-count",
                "description": "Max allowed violations for a given severity level.",
                "level": "warning",
                "tags": ["security"],
                "params": {"level": "critical", "max_count": 0},
                "condition": {
                    "<=": [
                        {
                            "get": [
                                {"var": "results.cve"},
                                {"cat": [{"var": "rule.params.level"}, "_count"]},
                            ]
                        },
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "Number of ${rule.params.level} vulnerabilities is within limits.",  # nosec B105
                    "fail": "Image has ${results.cve.${rule.params.level}_count} ${rule.params.level} CVEs (max allowed: ${rule.params.max_count}).",
                },
            },
        ]

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Run grype analysis and return a report dict."""
        if client.registry in ("docker.io", "registry-1.docker.io"):
            full_image = f"{repository}:{tag}"
        else:
            full_image = f"{client.registry}/{repository}:{tag}"

        data = run_grype(
            full_image,
            username=client.username,
            password=client.password,
            platform=platform,
        )

        counts = {field: 0 for field in _SEVERITY_FIELD.values()}
        fixed_count = 0
        grouped: dict[str, list[dict[str, Any]]] = {}

        for match in data.get("matches", []):
            vuln = match.get("vulnerability", {})
            artifact = match.get("artifact", {})
            severity = vuln.get("severity", "Unknown")
            counts[_SEVERITY_FIELD.get(severity, "unknown_count")] += 1

            fix = vuln.get("fix", {})
            if fix.get("state") == "fixed":
                fixed_count += 1
            fixed_versions = fix.get("versions") or []

            atype = artifact.get("type", "unknown")
            grouped.setdefault(atype, []).append(
                {
                    "VulnerabilityID": vuln.get("id", ""),
                    "PkgName": artifact.get("name", ""),
                    "InstalledVersion": artifact.get("version", ""),
                    "FixedVersion": fixed_versions[0] if fixed_versions else "",
                    "Severity": severity,
                    "Title": vuln.get("id", ""),
                    "Description": vuln.get("description", ""),
                }
            )

        targets = [
            {"Target": atype, "Vulnerabilities": vulns}
            for atype, vulns in sorted(grouped.items())
        ]

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "scanner_version": str(data.get("descriptor", {}).get("version", "unknown")),
            "vulnerability_count": sum(counts.values()),
            **counts,
            "fixed_count": fixed_count,
            "targets": targets,
        }
```

- [ ] **Step 5: Register the entry point**

In `pyproject.toml`, under `[project.entry-points."regis.analyzers"]`, replace the `trivy = …` line with:

```toml
cve = "regis.analyzers.cve:CveAnalyzer"
```

Then reinstall so the entry point is discoverable:

```bash
pipenv run pip install -e . --no-deps
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pipenv run pytest tests/test_analyzer_cve.py --no-cov`
Expected: PASS (3 tests, including schema validation).

- [ ] **Step 7: Commit**

```bash
git add regis/analyzers/cve.py regis/schemas/analyzer/cve.schema.json tests/test_analyzer_cve.py pyproject.toml
git commit -m "feat(cve): add CveAnalyzer backed by grype"
```

---

## Task 4: syft subprocess wrapper

**Files:**

- Create: `regis/utils/syft.py`
- Test: `tests/test_syft.py`

- [ ] **Step 1: Write the failing test**

`tests/test_syft.py`:

```python
"""Tests for the syft subprocess wrapper."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.utils.syft import run_syft

_SAMPLE = '{"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}'


class TestRunSyft:
    @patch("regis.utils.syft.shutil.which")
    def test_not_found(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(AnalyzerError, match="syft executable not found"):
            run_syft("alpine:3.20")

    @patch("regis.utils.syft.shutil.which")
    @patch("regis.utils.syft.subprocess.run")
    def test_success_and_args(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)

        result = run_syft("alpine:3.20")
        assert result["bomFormat"] == "CycloneDX"

        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/local/bin/syft"
        assert "cyclonedx-json" in args

    @patch("regis.utils.syft.shutil.which")
    @patch("regis.utils.syft.subprocess.run")
    def test_creds_and_platform(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout=_SAMPLE)

        run_syft("alpine:3.20", username="u", password="p", platform="linux/arm64")

        args = mock_run.call_args[0][0]
        env = mock_run.call_args[1]["env"]
        assert "--platform" in args and "linux/arm64" in args
        assert env["SYFT_REGISTRY_AUTH_USERNAME"] == "u"
        assert env["SYFT_REGISTRY_AUTH_PASSWORD"] == "p"

    @patch("regis.utils.syft.shutil.which")
    @patch("regis.utils.syft.subprocess.run")
    def test_called_process_error(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/syft"
        mock_run.side_effect = subprocess.CalledProcessError(1, ["syft"], stderr="boom")
        with pytest.raises(AnalyzerError, match="syft failed: boom"):
            run_syft("alpine:3.20")

    @patch("regis.utils.syft.shutil.which")
    @patch("regis.utils.syft.subprocess.run")
    def test_invalid_json(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/syft"
        mock_run.return_value = MagicMock(stdout="not-json")
        with pytest.raises(AnalyzerError, match="syft produced invalid"):
            run_syft("alpine:3.20")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_syft.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: regis.utils.syft`.

- [ ] **Step 3: Write the wrapper**

`regis/utils/syft.py`:

```python
"""Subprocess wrapper for the syft SBOM generator.

Centralizes syft invocation, registry-credential injection, and CycloneDX-JSON
parsing. Mirrors regis/utils/grype.py.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess  # nosec B404
from typing import Any

from regis.analyzers.base import AnalyzerError

logger = logging.getLogger(__name__)

#: Default timeout for syft calls (seconds).
DEFAULT_TIMEOUT = 300


def run_syft(
    image: str,
    username: str | None = None,
    password: str | None = None,
    platform: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Run ``syft <image> -o cyclonedx-json`` and return parsed JSON.

    Raises:
        AnalyzerError: if syft is missing, fails, or emits invalid JSON.
    """
    syft_path = shutil.which("syft")
    if not syft_path:
        raise AnalyzerError("syft executable not found in PATH")

    env = os.environ.copy()
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")
    if user and pwd:
        env["SYFT_REGISTRY_AUTH_USERNAME"] = user
        env["SYFT_REGISTRY_AUTH_PASSWORD"] = pwd

    cmd = [syft_path, image, "-o", "cyclonedx-json"]
    if platform:
        cmd.extend(["--platform", platform])

    logger.debug("Running syft on %s", image)
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            env=env,
        )
        return json.loads(result.stdout)  # type: ignore[no-any-return]
    except subprocess.CalledProcessError as exc:
        raise AnalyzerError(f"syft failed: {exc.stderr}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalyzerError(f"syft timed out after {timeout}s") from exc
    except json.JSONDecodeError as exc:
        raise AnalyzerError(f"syft produced invalid JSON: {exc}") from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/test_syft.py --no-cov`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add regis/utils/syft.py tests/test_syft.py
git commit -m "feat(sbom): add syft subprocess wrapper"
```

---

## Task 5: Swap SbomAnalyzer backend trivy → syft

**Files:**

- Modify: `regis/analyzers/sbom.py`
- Modify: `regis/schemas/analyzer/sbom.schema.json`
- Modify: `tests/test_sbom.py`

- [ ] **Step 1: Add `scanner_version` to the schema**

In `regis/schemas/analyzer/sbom.schema.json`, add `"scanner_version"` to the `required` array and to `properties`:

```json
"scanner_version": {
  "type": "string",
  "description": "Version of the syft CLI used."
}
```

- [ ] **Step 2: Update the SbomAnalyzer test for the syft backend**

In `tests/test_sbom.py`:

- Replace the import `from regis.analyzers.sbom import COPYLEFT_LICENSES, SbomAnalyzer, _run_trivy_sbom` with `from regis.analyzers.sbom import COPYLEFT_LICENSES, SbomAnalyzer`.
- Replace every `@patch("regis.analyzers.sbom._run_trivy_sbom")` with `@patch("regis.analyzers.sbom.run_syft")` and rename the mock param accordingly.
- The CycloneDX fixtures (e.g. `CYCLONEDX_COPYLEFT_SAMPLE`) gain a syft-style tools block so `scanner_version` resolves; add to each fixture dict:

```python
    "metadata": {"tools": {"components": [{"name": "syft", "version": "1.14.1"}]}},
```

- Add an assertion in the success-path test:

```python
    assert report["scanner_version"] == "1.14.1"
```

- Delete the `TestRunTrivySbom` class (the old `_run_trivy_sbom` unit tests) — the wrapper is now covered by `tests/test_syft.py`.

- [ ] **Step 3: Run the test to verify it fails**

Run: `pipenv run pytest tests/test_sbom.py --no-cov`
Expected: FAIL — `ImportError` / `AttributeError` on `run_syft` patch target (not yet imported in sbom.py).

- [ ] **Step 4: Rewrite the SBOM backend**

In `regis/analyzers/sbom.py`:

Replace the imports block — drop `os`, `shutil`, `subprocess` and add the syft wrapper:

```python
from __future__ import annotations

import logging
from typing import Any

from regis.analyzers.base import AnalyzerError, BaseAnalyzer
from regis.registry.client import RegistryClient
from regis.utils.syft import run_syft
```

Delete the entire `_run_trivy_sbom` function.

Add a version helper above the class:

```python
def _syft_version(data: dict[str, Any]) -> str:
    """Best-effort extraction of the syft version from CycloneDX metadata.tools."""
    tools = data.get("metadata", {}).get("tools", {})
    # CycloneDX 1.5: metadata.tools.components[]; older: metadata.tools[] (array).
    candidates = tools.get("components", []) if isinstance(tools, dict) else tools
    for tool in candidates:
        if tool.get("name") == "syft" and tool.get("version"):
            return str(tool["version"])
    return "unknown"
```

In `SbomAnalyzer.analyze`, replace the `data = _run_trivy_sbom(…)` call with:

```python
        data = run_syft(
            full_image,
            username=client.username,
            password=client.password,
            platform=platform,
        )
```

Add `"scanner_version": _syft_version(data),` to the returned dict (e.g. right after `"analyzer": self.name,`).

Update the class docstring: `"""Generate a Software Bill of Materials using Syft (CycloneDX)."""`

- [ ] **Step 5: Run the test to verify it passes**

Run: `pipenv run pytest tests/test_sbom.py --no-cov`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add regis/analyzers/sbom.py regis/schemas/analyzer/sbom.schema.json tests/test_sbom.py
git commit -m "feat(sbom): generate SBOM with syft instead of trivy"
```

---

## Task 6: trufflehog subprocess wrapper

**Files:**

- Create: `regis/utils/trufflehog.py`
- Test: `tests/test_trufflehog.py`

- [ ] **Step 1: Write the failing test**

`tests/test_trufflehog.py`:

```python
"""Tests for the trufflehog subprocess wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.utils.trufflehog import run_trufflehog

# NDJSON: one finding per line, plus a blank line that must be ignored.
_NDJSON = (
    '{"DetectorName": "AWS", "Verified": true, "Redacted": "AKIA...", '
    '"SourceMetadata": {"Data": {"Docker": {"layer": "sha256:abc"}}}}\n'
    "\n"
    '{"DetectorName": "Generic", "Verified": false, "Redacted": "xyz...", '
    '"SourceMetadata": {"Data": {"Docker": {"layer": "sha256:def"}}}}\n'
)


class TestRunTrufflehog:
    @patch("regis.utils.trufflehog.shutil.which")
    def test_not_found(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(AnalyzerError, match="trufflehog executable not found"):
            run_trufflehog("alpine:3.20")

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_parses_ndjson_ignoring_blank_lines(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trufflehog"
        mock_run.return_value = MagicMock(stdout=_NDJSON, returncode=0)

        findings = run_trufflehog("alpine:3.20")
        assert len(findings) == 2
        assert findings[0]["DetectorName"] == "AWS"

        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/local/bin/trufflehog"
        assert "docker" in args and "--json" in args
        assert "--image" in args

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_nonzero_exit_with_findings_is_not_an_error(self, mock_run, mock_which):
        # trufflehog exits non-zero (e.g. 183) when secrets are found.
        mock_which.return_value = "/usr/local/bin/trufflehog"
        mock_run.return_value = MagicMock(stdout=_NDJSON, returncode=183)
        findings = run_trufflehog("alpine:3.20")
        assert len(findings) == 2

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_invalid_json_line_raises(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trufflehog"
        mock_run.return_value = MagicMock(stdout="not-json\n", returncode=0)
        with pytest.raises(AnalyzerError, match="trufflehog produced invalid"):
            run_trufflehog("alpine:3.20")

    @patch("regis.utils.trufflehog.shutil.which")
    @patch("regis.utils.trufflehog.subprocess.run")
    def test_credentials_written_to_temp_docker_config(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/trufflehog"
        captured = {}

        def _capture(*args, **kwargs):
            # Read the temp config the wrapper created before it is cleaned up.
            cfg_dir = kwargs["env"]["DOCKER_CONFIG"]
            with open(f"{cfg_dir}/config.json", encoding="utf-8") as fh:
                captured["config"] = fh.read()
            return MagicMock(stdout="", returncode=0)

        mock_run.side_effect = _capture
        run_trufflehog("ghcr.io/acme/app:1.0", username="u", password="p")

        assert "ghcr.io" in captured["config"]
        # base64("u:p") == "dTpw"
        assert "dTpw" in captured["config"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pipenv run pytest tests/test_trufflehog.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: regis.utils.trufflehog`.

- [ ] **Step 3: Write the wrapper**

`regis/utils/trufflehog.py`:

```python
"""Subprocess wrapper for the trufflehog secret scanner.

Runs ``trufflehog docker --image <ref> --json`` and parses the NDJSON output.
The exit code is not used to detect failure (trufflehog exits 0 even with
findings unless ``--fail`` is passed); an unparseable line is the failure
signal instead. Credentials, when present, are forwarded via a temporary
``DOCKER_CONFIG`` (trufflehog has no basic-auth env pair) — same pattern as
regis/utils/regctl.py.

Known limitation: a failed remote-registry pull also yields exit 0 + empty
stdout, which is indistinguishable from "no secrets found".
"""

from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import subprocess  # nosec B404
import tempfile
from typing import Any

from regis.analyzers.base import AnalyzerError

logger = logging.getLogger(__name__)

#: Default timeout for trufflehog calls (seconds).
DEFAULT_TIMEOUT = 300


def _registry_host(image: str) -> str:
    """Derive the docker-config auths key (registry host) from an image ref."""
    first = image.split("/", 1)[0]
    if "." in first or ":" in first or first == "localhost":
        return first
    return "https://index.docker.io/v1/"  # Docker Hub default auths key


def _write_docker_config(host: str, user: str, pwd: str) -> str:
    """Write a temp Docker config.json with credentials; return its dir.

    Cleans up the temp directory if the write fails. The caller is responsible
    for removing the directory after the subprocess finishes.
    """
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    config = {"auths": {host: {"auth": auth}}}
    tmpdir = tempfile.mkdtemp(prefix="regis-trufflehog-")
    try:
        with open(os.path.join(tmpdir, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(config, handle)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return tmpdir


def run_trufflehog(
    image: str,
    username: str | None = None,
    password: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """Run trufflehog against a container image and return parsed findings.

    Args:
        image: Full image reference.
        username: Optional registry username (forwarded via env).
        password: Optional registry password (forwarded via env).
        timeout: Subprocess timeout in seconds.

    Returns:
        A list of finding dicts (one per NDJSON line).

    Raises:
        AnalyzerError: if trufflehog is missing, times out, or emits a line
            that is not valid JSON.
    """
    th_path = shutil.which("trufflehog")
    if not th_path:
        raise AnalyzerError("trufflehog executable not found in PATH")

    env = os.environ.copy()
    user = username or env.get("REGIS_USERNAME")
    pwd = password or env.get("REGIS_PASSWORD")
    docker_config_dir: str | None = None
    if user and pwd:
        docker_config_dir = _write_docker_config(_registry_host(image), user, pwd)
        env["DOCKER_CONFIG"] = docker_config_dir

    cmd = [th_path, "docker", "--image", image, "--json", "--no-update"]

    logger.debug("Running trufflehog on %s", image)
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=False,  # trufflehog exits 0 even with findings (no --fail)
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise AnalyzerError(f"trufflehog timed out after {timeout}s") from exc
    finally:
        if docker_config_dir:
            shutil.rmtree(docker_config_dir, ignore_errors=True)

    findings: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            findings.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AnalyzerError(f"trufflehog produced invalid JSON: {exc}") from exc
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pipenv run pytest tests/test_trufflehog.py --no-cov`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add regis/utils/trufflehog.py tests/test_trufflehog.py
git commit -m "feat(secrets): add trufflehog subprocess wrapper"
```

---

## Task 7: secrets.schema.json + SecretsAnalyzer

**Files:**

- Create: `regis/schemas/analyzer/secrets.schema.json`
- Create: `regis/analyzers/secrets.py`
- Modify: `pyproject.toml` (add `secrets` entry point)
- Test: `tests/test_analyzer_secrets.py`

- [ ] **Step 1: Write the schema**

`regis/schemas/analyzer/secrets.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://trivoallan.github.io/regis/schemas/analyzer/secrets.schema.json",
  "title": "secrets.output",
  "description": "Secret detection results from TruffleHog.",
  "type": "object",
  "required": [
    "analyzer",
    "repository",
    "tag",
    "scanner_version",
    "secrets_count",
    "verified_count",
    "findings"
  ],
  "properties": {
    "analyzer": { "type": "string", "const": "secrets" },
    "repository": { "type": "string" },
    "tag": { "type": "string" },
    "scanner_version": { "type": "string" },
    "secrets_count": { "type": "integer", "minimum": 0 },
    "verified_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Secrets TruffleHog verified as live credentials."
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["DetectorName", "Verified"],
        "properties": {
          "DetectorName": { "type": "string" },
          "Verified": { "type": "boolean" },
          "Redacted": { "type": "string" },
          "layer": { "type": "string" }
        }
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Write the failing test**

`tests/test_analyzer_secrets.py`:

```python
"""Tests for the secrets analyzer (trufflehog backend)."""

from unittest.mock import MagicMock, patch

import pytest

from regis.analyzers.base import AnalyzerError
from regis.analyzers.secrets import SecretsAnalyzer

_FINDINGS = [
    {
        "DetectorName": "AWS",
        "Verified": True,
        "Redacted": "AKIA...",
        "SourceMetadata": {"Data": {"Docker": {"layer": "sha256:abc"}}},
    },
    {
        "DetectorName": "Generic",
        "Verified": False,
        "Redacted": "xyz...",
        "SourceMetadata": {"Data": {"Docker": {"layer": "sha256:def"}}},
    },
]


@pytest.fixture
def analyzer():
    return SecretsAnalyzer()


class TestSecretsAnalyzer:
    def test_default_rules_slug(self, analyzer):
        slugs = {r["slug"] for r in analyzer.default_rules()}
        assert "secret-scan" in slugs

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.82.7")
    @patch("regis.analyzers.secrets.run_trufflehog")
    def test_analyze_counts(self, mock_run, _mock_ver, analyzer):
        mock_run.return_value = _FINDINGS
        client = MagicMock()
        client.registry = "docker.io"
        client.username = None
        client.password = None

        report = analyzer.analyze(client, "library/alpine", "3.20")

        assert report["analyzer"] == "secrets"
        assert report["scanner_version"] == "3.82.7"
        assert report["secrets_count"] == 2
        assert report["verified_count"] == 1
        assert report["findings"][0]["layer"] == "sha256:abc"
        analyzer.validate(report)

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.82.7")
    @patch("regis.analyzers.secrets.run_trufflehog")
    def test_analyze_no_secrets(self, mock_run, _mock_ver, analyzer):
        mock_run.return_value = []
        client = MagicMock()
        client.registry = "example.com"
        client.username = None
        client.password = None
        report = analyzer.analyze(client, "repo", "tag")
        assert report["secrets_count"] == 0
        assert report["verified_count"] == 0
        assert report["findings"] == []
        analyzer.validate(report)

    @patch("regis.analyzers.secrets._scanner_version", return_value="3.82.7")
    @patch("regis.analyzers.secrets.run_trufflehog")
    def test_analyze_forwards_error(self, mock_run, _mock_ver, analyzer):
        mock_run.side_effect = AnalyzerError("boom")
        client = MagicMock()
        client.registry = "example.com"
        with pytest.raises(AnalyzerError, match="boom"):
            analyzer.analyze(client, "repo", "tag")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pipenv run pytest tests/test_analyzer_secrets.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: regis.analyzers.secrets`.

- [ ] **Step 4: Write the analyzer**

`regis/analyzers/secrets.py`:

```python
"""Secrets analyzer — detects embedded credentials using trufflehog."""

from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404
from typing import Any

from regis.analyzers.base import BaseAnalyzer
from regis.registry.client import RegistryClient
from regis.utils.trufflehog import run_trufflehog

logger = logging.getLogger(__name__)


def _scanner_version() -> str:
    """Best-effort trufflehog version via ``trufflehog --version`` (stderr)."""
    path = shutil.which("trufflehog")
    if not path:
        return "unknown"
    try:
        result = subprocess.run(  # nosec B603
            [path, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    out = (result.stderr or result.stdout).strip()
    return out.splitlines()[0] if out else "unknown"


def _layer(finding: dict[str, Any]) -> str:
    """Extract the Docker layer digest from a trufflehog finding, if present."""
    docker = finding.get("SourceMetadata", {}).get("Data", {}).get("Docker", {})
    return str(docker.get("layer", ""))


class SecretsAnalyzer(BaseAnalyzer):
    """Scan an image for embedded secrets using trufflehog."""

    name = "secrets"
    schema_file = "analyzer/secrets.schema.json"

    @classmethod
    def default_rules(cls) -> list[dict[str, Any]]:
        return [
            {
                "slug": "secret-scan",
                "description": "No secrets or credentials should be embedded in the image.",
                "level": "critical",
                "tags": ["security"],
                "params": {"max_count": 0},
                "condition": {
                    "<=": [
                        {"var": "results.secrets.secrets_count"},
                        {"var": "rule.params.max_count"},
                    ]
                },
                "messages": {
                    "pass": "No secrets detected in the image.",  # nosec B105
                    "fail": "TruffleHog detected ${results.secrets.secrets_count} secrets in the image.",
                },
            },
        ]

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Run trufflehog analysis and return a report dict."""
        if client.registry in ("docker.io", "registry-1.docker.io"):
            full_image = f"{repository}:{tag}"
        else:
            full_image = f"{client.registry}/{repository}:{tag}"

        raw = run_trufflehog(
            full_image,
            username=client.username,
            password=client.password,
        )

        findings = [
            {
                "DetectorName": f.get("DetectorName", ""),
                "Verified": bool(f.get("Verified", False)),
                "Redacted": f.get("Redacted", ""),
                "layer": _layer(f),
            }
            for f in raw
        ]
        verified_count = sum(1 for f in findings if f["Verified"])

        return {
            "analyzer": self.name,
            "repository": repository,
            "tag": tag,
            "scanner_version": _scanner_version(),
            "secrets_count": len(findings),
            "verified_count": verified_count,
            "findings": findings,
        }
```

- [ ] **Step 5: Register the entry point**

In `pyproject.toml`, under `[project.entry-points."regis.analyzers"]`, add:

```toml
secrets = "regis.analyzers.secrets:SecretsAnalyzer"
```

Reinstall:

```bash
pipenv run pip install -e . --no-deps
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pipenv run pytest tests/test_analyzer_secrets.py --no-cov`
Expected: PASS (4 tests).

- [ ] **Step 7: Commit**

```bash
git add regis/analyzers/secrets.py regis/schemas/analyzer/secrets.schema.json tests/test_analyzer_secrets.py pyproject.toml
git commit -m "feat(secrets): add SecretsAnalyzer backed by trufflehog"
```

---

## Task 8: Delete the trivy analyzer, schema, and tests

**Files:**

- Delete: `regis/analyzers/trivy.py`, `regis/schemas/analyzer/trivy.schema.json`
- Delete: `tests/test_trivy.py`, `tests/test_analyzer_trivy.py`

- [ ] **Step 1: Confirm the `trivy` entry point is already gone**

Run: `grep -n "trivy" pyproject.toml`
Expected: no match (replaced by `cve` in Task 3). If a match remains, remove that line.

- [ ] **Step 2: Delete the files**

```bash
git rm regis/analyzers/trivy.py regis/schemas/analyzer/trivy.schema.json tests/test_trivy.py tests/test_analyzer_trivy.py
```

- [ ] **Step 3: Check for stray references**

Run: `grep -rn "TrivyAnalyzer\|analyzers.trivy\|analyzer/trivy.schema\|_run_trivy" regis tests`
Expected: no matches. Fix any that remain (they would be in code not yet migrated — there should be none after Tasks 3 & 5).

- [ ] **Step 4: Run the affected suites**

Run: `pipenv run pytest tests/test_analyzer_cve.py tests/test_analyzer_secrets.py tests/test_sbom.py --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(cve)!: remove trivy analyzer in favor of cve/secrets/sbom

BREAKING CHANGE: the 'trivy' analyzer is replaced by 'cve' (grype) and
'secrets' (trufflehog); SBOM generation now uses syft. Playbooks using
'provider: trivy' must switch to 'provider: cve' / 'provider: secrets',
and 'results.trivy.*' becomes 'results.cve.*' / 'results.secrets.*'."
```

---

## Task 9: Migrate the default playbook

**Files:**

- Modify: `regis/playbooks/default/playbook.yaml`
- Test: `tests/test_rules_config.py`, `tests/test_playbook_engine.py` (regression)

- [ ] **Step 1: Update the playbook providers**

In `regis/playbooks/default/playbook.yaml`, change the three trivy rules:

```yaml
- provider: cve
  rule: cve-count
  slug: cve-critical
  level: critical
  options:
    level: critical
    max_count: 0

- provider: cve
  rule: cve-count
  slug: cve-high
  level: warning
  options:
    level: high
    max_count: 10

- provider: cve
  rule: fix-available
  slug: cve-fixable
  level: warning
```

(The `sbom` rules are unchanged.)

- [ ] **Step 2: Find and update playbook/rules test fixtures**

Run: `grep -rn "results.trivy\|provider: trivy\|provider=\"trivy\"\|\"trivy\"" tests`
For each match in `tests/test_rules_config.py` and `tests/test_playbook_engine.py`, change `results.trivy.<field>` → `results.cve.<field>` (vulnerability fields) or `results.secrets.secrets_count` (secrets), and `provider: trivy` → `provider: cve`.

- [ ] **Step 3: Run the playbook suites**

Run: `pipenv run pytest tests/test_rules_config.py tests/test_playbook_engine.py --no-cov`
Expected: PASS.

- [ ] **Step 4: Validate the playbook offline**

Run: `pipenv run regis playbook validate regis/playbooks/default`
Expected: validation success (no schema errors).

- [ ] **Step 5: Commit**

```bash
git add regis/playbooks/default/playbook.yaml tests/test_rules_config.py tests/test_playbook_engine.py
git commit -m "feat(playbook)!: switch default playbook from trivy to cve provider

BREAKING CHANGE: default playbook rules now use 'provider: cve'."
```

---

## Task 10: Update `regis doctor`

**Files:**

- Modify: `regis/commands/doctor.py`
- Modify: `tests/commands/test_doctor.py`

- [ ] **Step 1: Update the doctor test**

In `tests/commands/test_doctor.py`, change the tool-presence assertion loop:

```python
    for tool in ("grype", "syft", "trufflehog", "regctl", "hadolint", "dockle"):
        assert tool in result.output
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pipenv run pytest tests/commands/test_doctor.py --no-cov`
Expected: FAIL — `grype`/`syft`/`trufflehog` not in output.

- [ ] **Step 3: Update the required-tools list**

In `regis/commands/doctor.py`, replace the `_REQUIRED_TOOLS` list:

```python
_REQUIRED_TOOLS: list[tuple[str, str]] = [
    ("grype", "version"),
    ("syft", "version"),
    ("trufflehog", "--version"),
    ("regctl", "version"),
    ("hadolint", "--version"),
    ("dockle", "--version"),
]
```

(Use the exact version sub-commands confirmed in Task 1.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `pipenv run pytest tests/commands/test_doctor.py --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add regis/commands/doctor.py tests/commands/test_doctor.py
git commit -m "feat(cli): check grype/syft/trufflehog in regis doctor"
```

---

## Task 11: Dockerfile + CI tool installation

**Files:**

- Modify: `Dockerfile`
- Modify: `.github/workflows/cd-docs.yml`
- Modify: `.github/workflows/ci-image-size.yml`

- [ ] **Step 1: Replace the trivy fetch block in the Dockerfile**

In the `tools-fetcher` stage, add the pinned versions to the `ENV` line:

```dockerfile
ENV HADOLINT_VERSION=2.12.0 \
    DOCKLE_VERSION=0.4.15 \
    REGCTL_VERSION=0.11.5 \
    GRYPE_VERSION=0.112.0 \
    SYFT_VERSION=1.44.0 \
    TRUFFLEHOG_VERSION=3.95.3
```

Replace the trivy install block (the `curl … trivy … install.sh` lines) with three fetches that mirror the dockle/regctl pattern:

```dockerfile
# grype (static binary)
RUN case "$TARGETARCH" in \
      amd64) arch="amd64" ;; \
      arm64) arch="arm64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/anchore/grype/releases/download/v${GRYPE_VERSION}/grype_${GRYPE_VERSION}_linux_${arch}.tar.gz" \
      -o /tmp/grype.tar.gz && \
    tar -xzf /tmp/grype.tar.gz -C /tools grype && \
    chmod +x /tools/grype && rm /tmp/grype.tar.gz

# syft (static binary)
RUN case "$TARGETARCH" in \
      amd64) arch="amd64" ;; \
      arm64) arch="arm64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/anchore/syft/releases/download/v${SYFT_VERSION}/syft_${SYFT_VERSION}_linux_${arch}.tar.gz" \
      -o /tmp/syft.tar.gz && \
    tar -xzf /tmp/syft.tar.gz -C /tools syft && \
    chmod +x /tools/syft && rm /tmp/syft.tar.gz

# trufflehog (static binary)
RUN case "$TARGETARCH" in \
      amd64) arch="amd64" ;; \
      arm64) arch="arm64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION}_linux_${arch}.tar.gz" \
      -o /tmp/trufflehog.tar.gz && \
    tar -xzf /tmp/trufflehog.tar.gz -C /tools trufflehog && \
    chmod +x /tools/trufflehog && rm /tmp/trufflehog.tar.gz
```

- [ ] **Step 2: Replace the trivy COPY in the final stage**

Replace `COPY --from=tools-fetcher /tools/trivy /usr/local/bin/trivy` with:

```dockerfile
COPY --from=tools-fetcher /tools/grype /usr/local/bin/grype
COPY --from=tools-fetcher /tools/syft /usr/local/bin/syft
COPY --from=tools-fetcher /tools/trufflehog /usr/local/bin/trufflehog
```

- [ ] **Step 3: Update the CI docs workflow**

In `.github/workflows/cd-docs.yml`, replace the trivy install line (the `curl … trivy … install.sh` step) with the three official install scripts:

```yaml
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sudo sh -s -- -b /usr/local/bin
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sudo sh -s -- -b /usr/local/bin
```

- [ ] **Step 4: Update the image-size workflow comment**

In `.github/workflows/ci-image-size.yml`, update the comment block that cites "trivy (~160 MB)" to reflect grype+syft+trufflehog (~120 MB combined). Leave the numeric ceiling as-is for now; it is re-evaluated against a real build in Task 14.

- [ ] **Step 5: Lint the Dockerfile**

Run: `trunk check Dockerfile`
Expected: no new hadolint issues (the `# hadolint ignore=DL4006` was only needed for the piped trivy installer; the new blocks don't pipe to sh).

- [ ] **Step 6: Commit**

```bash
git add Dockerfile .github/workflows/cd-docs.yml .github/workflows/ci-image-size.yml
git commit -m "ci(docker): install grype/syft/trufflehog, drop trivy"
```

---

## Task 12: Migrate the dashboard

**Files:**

- Rename: `apps/dashboard/src/components/TrivySection.tsx` → `CveSection.tsx`
- Create: `apps/dashboard/src/components/SecretsSection.tsx`
- Modify: `apps/dashboard/src/components/AnalyzerSection.tsx`
- Modify: `apps/dashboard/src/components/Dashboard/AnalyzerCoverageCard.tsx`
- Modify: `apps/dashboard/src/components/Dashboard/VulnerabilityChart.tsx`
- Modify: `apps/dashboard/src/components/SummaryView.tsx`
- Rename: `apps/dashboard/docs/analyzers/trivy.mdx` → `cve.mdx`
- Create: `apps/dashboard/docs/analyzers/secrets.mdx`

- [ ] **Step 1: Rename the Trivy section component**

```bash
git mv apps/dashboard/src/components/TrivySection.tsx apps/dashboard/src/components/CveSection.tsx
```

In `CveSection.tsx`, rename the exported function `TrivySection` → `CveSection` and the interfaces `TrivyData`/`TrivyTarget`/`TrivyVulnerability` → `CveData`/`CveTarget`/`CveVulnerability` (find/replace within the file). Keep field names (`critical_count`, etc.). If a `negligible_count` display is desired, add it alongside the existing severity rows; not required for the build to pass.

- [ ] **Step 2: Update the dispatcher**

In `apps/dashboard/src/components/AnalyzerSection.tsx`:

- Replace `import { TrivySection } from "./TrivySection";` with `import { CveSection } from "./CveSection";` and add `import { SecretsSection } from "./SecretsSection";`
- Replace `case "trivy": return <TrivySection data={data as never} />;` with:

```tsx
    case "cve":
      return <CveSection data={data as never} />;
    case "secrets":
      return <SecretsSection data={data as never} />;
```

- [ ] **Step 3: Create the Secrets section**

`apps/dashboard/src/components/SecretsSection.tsx`:

```tsx
/**
 * SecretsSection — renders trufflehog secret-detection results.
 */

import React from "react";
import { Card, Flex, Text, Metric, Badge } from "@tremor/react";

interface SecretFinding {
  DetectorName: string;
  Verified: boolean;
  Redacted?: string;
  layer?: string;
}

interface SecretsData {
  secrets_count: number;
  verified_count: number;
  findings?: SecretFinding[];
}

export function SecretsSection({
  data,
}: {
  data: SecretsData;
}): React.JSX.Element {
  const findings = data.findings ?? [];
  const color =
    data.verified_count > 0
      ? "rose"
      : data.secrets_count > 0
        ? "amber"
        : "emerald";
  return (
    <Card>
      <Flex justifyContent="between" alignItems="start">
        <Text className="font-medium">Secrets</Text>
        <Badge color={color} size="xs">
          {data.verified_count} verified
        </Badge>
      </Flex>
      <Metric className="mt-2">{data.secrets_count}</Metric>
      <Text className="mt-1 text-tremor-content">Detected by TruffleHog</Text>
      <ul className="mt-4 space-y-1">
        {findings.map((f, i) => (
          <li key={i} className="text-tremor-default">
            <span className="font-medium">{f.DetectorName}</span>
            {f.Verified ? " (verified)" : ""} — {f.Redacted ?? ""}
          </li>
        ))}
      </ul>
    </Card>
  );
}
```

- [ ] **Step 4: Update the coverage-card label map**

In `apps/dashboard/src/components/Dashboard/AnalyzerCoverageCard.tsx`, in `ANALYZER_LABELS` replace `trivy: "Trivy",` with:

```ts
  cve: "Vulnerabilities",
  secrets: "Secrets",
```

- [ ] **Step 5: Update the vulnerability chart label**

In `apps/dashboard/src/components/Dashboard/VulnerabilityChart.tsx`, change the caption `Detected by Trivy` → `Detected by Grype`.

- [ ] **Step 6: Update SummaryView**

In `apps/dashboard/src/components/SummaryView.tsx`, replace:

```tsx
const trivyData = report.results?.trivy as Record<string, number> | undefined;
const vulnerabilityData = trivyData;
```

with `cveData` reading `report.results?.cve`:

```tsx
const cveData = report.results?.cve as Record<string, number> | undefined;
const vulnerabilityData = cveData
  ? [
      { severity: "Critical", count: cveData.critical_count ?? 0 },
      { severity: "High", count: cveData.high_count ?? 0 },
      { severity: "Medium", count: cveData.medium_count ?? 0 },
      { severity: "Low", count: cveData.low_count ?? 0 },
      { severity: "Unknown", count: cveData.unknown_count ?? 0 },
    ]
  : [];
```

- [ ] **Step 7: Rename the analyzer doc page and add the secrets page**

```bash
git mv apps/dashboard/docs/analyzers/trivy.mdx apps/dashboard/docs/analyzers/cve.mdx
```

In `cve.mdx`, change the front-matter `title: Trivy` → `title: Vulnerabilities` and `<AnalyzerPage name="trivy" />` → `<AnalyzerPage name="cve" />`.

Create `apps/dashboard/docs/analyzers/secrets.mdx`:

```mdx
---
title: Secrets
hide_title: true
---

import { AnalyzerPage } from "@site/src/components/AnalyzerPage";

<AnalyzerPage name="secrets" />
```

- [ ] **Step 8: Build the dashboard as a guard**

Run: `pnpm --filter @regis/dashboard build`
Expected: build succeeds (no missing-import or type errors).

- [ ] **Step 9: Commit**

```bash
git add apps/dashboard
git commit -m "feat(viewer): render cve/secrets analyzers, drop Trivy section"
```

---

## Task 13: Docs, CLAUDE.md, and What's New

**Files:**

- Modify: `CLAUDE.md`
- Modify: `docs/memory-bank/techContext.md`, `docs/memory-bank/externalIntegrations.md`, `docs/memory-bank/systemPatterns.md`
- Modify: `docs/website` analyzer/reference pages mentioning trivy

- [ ] **Step 1: Update CLAUDE.md required binaries**

In `CLAUDE.md`, change the required-binaries line:

> Required external binaries (must be on `PATH`): `grype`, `syft`, `trufflehog`, `regctl`, `hadolint`, `dockle`.

- [ ] **Step 2: Sweep the memory-bank and docs site for trivy references**

Run: `grep -rn -i "trivy" docs CLAUDE.md`
For each prose reference, update it to the new model (grype for CVEs, syft for SBOM, trufflehog for secrets; provider names `cve`/`secrets`/`sbom`). Do **not** edit `CHANGELOG.md` (auto-generated) or `docs/memory-bank/RULES.md`. Do **not** touch any root `.gitlab-ci.yml`.

- [ ] **Step 3: Write the migration note for the PR summary**

Draft (to paste into the PR `## Summary`, harvested into What's New):

```markdown
## Summary

Regis now scans with **grype** (CVEs), **syft** (SBOM), and **trufflehog**
(secrets) instead of trivy. Analyzers are named by capability: `cve`,
`secrets`, `sbom`.

**Breaking — playbook migration:**

- `provider: trivy` → `provider: cve` (CVE rules) or `provider: secrets`
- `results.trivy.<sev>_count` → `results.cve.<sev>_count`
- `results.trivy.secrets_count` → `results.secrets.secrets_count`

New `cve` reports add a `negligible_count` bucket; `secrets` reports add
`verified_count` (live-verified credentials).
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs
git commit -m "docs(analyzer): document grype/syft/trufflehog migration"
```

---

## Task 14: Full suite, coverage gate, and image-size re-check

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite with coverage**

Run: `pipenv run pytest`
Expected: PASS, coverage ≥ 90 %. If a new module is under-covered, add focused tests (e.g. `_syft_version` array-shaped `metadata.tools`, `_scanner_version` missing-binary path, `_layer` with no Docker metadata).

- [ ] **Step 2: Lint everything**

Run: `trunk check`
Expected: no issues. Auto-fix with `trunk check --fix` and re-stage if needed.

- [ ] **Step 3: Smoke-test the CLI entry points**

Run:

```bash
pipenv run regis rules list --filter-provider cve
pipenv run regis rules list --filter-provider secrets
```

Expected: lists the `cve-count`/`fix-available` and `secret-scan` rules respectively (confirms entry points are discoverable).

- [ ] **Step 4: (Optional, if Docker available) Build and measure the image**

Run:

```bash
docker build -t regis:grype .
docker save regis:grype | wc -c
```

Compare against the `ci-image-size.yml` ceiling (220 MB). If the new size is comfortably under, optionally tighten the ceiling in a follow-up commit; if it exceeds, raise the ceiling with a justifying comment.

- [ ] **Step 5: Final commit (if any test/coverage fixes were made)**

```bash
git add -A
git commit -m "test(cve): cover edge cases for grype/syft/trufflehog migration"
```

---

## Self-Review Notes

- **Spec coverage:** §3 architecture → Tasks 2–7; §4 schemas → Tasks 3/5/7; §5 migration (playbook, dashboard, versioning, CLAUDE.md) → Tasks 9/12/13 + the `!` breaking commits; §6 infra → Tasks 10/11; §7 error handling → wrappers in Tasks 2/4/6; §8 testing → every task + Task 14; §10 open questions → Task 1 spike.
- **Version bump:** the `!`/`BREAKING CHANGE:` commits in Tasks 8 & 9 drive Release Please to 0.33.0 (`bump-minor-pre-major: true` already set) — no manual version edit needed.
- **Type consistency:** `run_grype`/`run_syft` return `dict`, `run_trufflehog` returns `list[dict]`; analyzers consume exactly those. `_SEVERITY_FIELD` count keys match the `cve.schema.json` required fields. `scanner_version` is the field name in all three schemas.
- **No `regis playbook migrate`:** out of scope per spec; migration is the documented find/replace in Task 13 Step 3.
