"""Versioning analyzer — detects tag naming patterns (semver, calver, etc.)."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from typing import Any

import semver

from regis_cli.analyzers.base import AnalyzerError, BaseAnalyzer
from regis_cli.registry.client import RegistryClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern classifiers — order matters (first match wins for each tag).
# ---------------------------------------------------------------------------

# CalVer patterns like 2024.01, 2024.01.15, 20240115
_CALVER_RE = re.compile(
    r"^v?(?:20\d{2})(?:[.\-](?:0[1-9]|1[0-2]))(?:[.\-](?:0[1-9]|[12]\d|3[01]))?$"
)

# Loose numeric versions like 1, 1.2, 1.2.3.4 (not strict semver)
_NUMERIC_RE = re.compile(r"^v?\d+(?:\.\d+)*$")

# Hash-like tags (hex strings ≥ 7 chars)
_HASH_RE = re.compile(r"^[0-9a-f]{7,}$")

# Known OS / distro variant tokens.  When all parts of a semver "prerelease"
# string consist of these tokens, the tag is classified as ``semver-variant``
# rather than ``semver-prerelease``.
_VARIANT_TOKENS: set[str] = {
    # Debian / Ubuntu code-names
    "alpine",
    "bookworm",
    "bullseye",
    "buster",
    "focal",
    "jammy",
    "jessie",
    "noble",
    "stretch",
    "trixie",
    "trusty",
    "xenial",
    # Generic qualifiers
    "slim",
    "fat",
    "full",
    "minimal",
    "lite",
    # Explicit OS names
    "linux",
    "windows",
    "windowsservercore",
    # Runtime variants
    "cli",
    "fpm",
    "zts",
    "apache",
    "nginx",
    "httpd",
    # SDK/Tooling
    "sdk",
    "jre",
    "jdk",
    "runtime",
    # Build types
    "debug",
    "dev",
    "development",
    "prod",
    "production",
    # Other common
    "management",
    "server",
    "desktop",
    # RedHat UBI
    "ubi",
    "ubi8",
    "ubi9",
    "redhat",
    "rhel",
    "micro",
    "init",
}

# Regex that matches alpine3.20, alpine3.21, etc. as a single variant token.
_VARIANT_TOKEN_RE = re.compile(
    r"^(" + "|".join(re.escape(t) for t in _VARIANT_TOKENS) + r")(\d[\w.]*)?$"
)

# Semver + variant pattern:  1.88.0-slim-bookworm, v2.0.0-alpine3.21
# Captures (optional v prefix)(semver digits)-(variant suffix)
_SEMVER_VARIANT_RE = re.compile(r"^v?(\d+\.\d+\.\d+)-(.+)$")


def _extract_variants(tag: str) -> list[str]:
    """Extract variant tokens from a tag string."""
    # Split by common separators (removed . to keep alpine3.18 intact)
    parts = re.split(r"[-_]", tag)
    # Filter parts that match known variant tokens
    found = []
    for part in parts:
        # Check against pure tokens
        if part in _VARIANT_TOKENS:
            found.append(part)
        # Check against combined tokens like alpine3.18
        elif _VARIANT_TOKEN_RE.match(part):
            found.append(part)
    return found


def _is_variant_suffix(suffix: str) -> bool:
    """Return True if *suffix* looks like an OS/distro variant, not a prerelease."""
    parts = suffix.split("-")
    return all(_VARIANT_TOKEN_RE.match(p) for p in parts)


def _classify_tag(tag: str) -> str:
    """Classify a single tag into a versioning pattern.

    Returns one of: ``semver``, ``semver-prerelease``, ``semver-variant``,
    ``calver``, ``numeric``, ``hash``, ``named``.
    """
    # Calendar versioning checked first — dates like 2024.12.25 are valid
    # semver too, but calver is the more specific classification.
    if _CALVER_RE.match(tag):
        return "calver"

    # Try strict semver.
    try:
        ver = semver.Version.parse(tag.lstrip("v"))
        if ver.prerelease:
            # Check whether the "prerelease" part is actually an OS variant.
            if _is_variant_suffix(ver.prerelease):
                return "semver-variant"
            return "semver-prerelease"
        return "semver"
    except ValueError:
        pass

    # Loose numeric (e.g. "1.2" or "8").
    if _NUMERIC_RE.match(tag):
        return "numeric"

    # Git commit hashes.
    if _HASH_RE.match(tag):
        return "hash"

    # Everything else is a named tag (latest, alpine, bookworm, …).
    return "named"


class VersioningAnalyzer(BaseAnalyzer):
    """Detect tag naming conventions and identify semver adoption."""

    name = "versioning"
    schema_file = "versioning.schema.json"

    def analyze(
        self,
        client: RegistryClient,
        repository: str,
        tag: str,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """Classify all tags and summarize versioning patterns using skopeo."""
        registry = client.registry
        target = f"docker://{registry}/{repository}"

        cmd = ["skopeo", "list-tags", target]

        if client.username and client.password:
            cmd.extend(["--creds", f"{client.username}:{client.password}"])

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(res.stdout)
            tags = data.get("Tags", [])
        except Exception as e:
            msg = f"Failed to list tags via skopeo for {target}: {e}"
            logger.error(msg)
            raise AnalyzerError(msg) from e

        # Classify every tag and extract variants.
        classifications: dict[str, list[str]] = {}
        variant_counts: dict[str, int] = {}
        variant_examples: dict[str, list[str]] = {}

        for t in tags:
            pattern = _classify_tag(t)
            classifications.setdefault(pattern, []).append(t)

            # Extract variants
            variants = _extract_variants(t)
            for v in variants:
                variant_counts[v] = variant_counts.get(v, 0) + 1
                variant_examples.setdefault(v, []).append(t)

        # Sort each bucket and compute stats.
        patterns: list[dict[str, Any]] = []
        for pattern_name in sorted(classifications):
            tag_list = sorted(classifications[pattern_name])
            patterns.append(
                {
                    "pattern": pattern_name,
                    "count": len(tag_list),
                    "percentage": (
                        round(len(tag_list) / len(tags) * 100, 1) if tags else 0
                    ),
                    "examples": tag_list[:10],
                }
            )

        # Determine the dominant pattern.
        dominant = (
            max(patterns, key=lambda p: p["count"])["pattern"]
            if patterns
            else "unknown"
        )

        # SemVer-specific summary (semver + prerelease + variant all count).
        semver_count = (
            len(classifications.get("semver", []))
            + len(classifications.get("semver-prerelease", []))
            + len(classifications.get("semver-variant", []))
        )
        semver_compliant = round(semver_count / len(tags) * 100, 1) if tags else 0

        # Determine release lines if the current tag is an alias
        current_pattern = _classify_tag(tag)
        release_lines = []
        if current_pattern not in ("semver", "semver-prerelease", "semver-variant"):
            inspect_target = f"docker://{registry}/{repository}:{tag}"

            inspect_cmd = ["skopeo", "inspect", inspect_target]
            if platform:
                try:
                    os_str, arch = platform.split("/", 1)
                    inspect_cmd.extend(
                        ["--override-os", os_str, "--override-arch", arch]
                    )
                except ValueError:
                    logger.debug(
                        "Invalid platform format %s, ignoring for inspect", platform
                    )
            else:
                # Default to linux/amd64 to avoid host architecture mismatch for multi-arch images
                inspect_cmd.extend(
                    ["--override-os", "linux", "--override-arch", "amd64"]
                )

            if client.username and client.password:
                inspect_cmd.extend(["--creds", f"{client.username}:{client.password}"])

            try:
                res_inspect = subprocess.run(
                    inspect_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                inspect_data = json.loads(res_inspect.stdout)
                repo_tags = inspect_data.get("RepoTags", [])

                # Filter to numeric release tags (semver-like)
                # We want 3, 3.14, 3.14.3 etc.
                numeric_tags = []
                for t in repo_tags:
                    p = _classify_tag(t)
                    if p in ("semver", "numeric"):
                        # Ensure it's not a variant or prerelease (handled by _classify_tag)
                        numeric_tags.append(t)

                if numeric_tags:
                    # Sort to find the most specific one
                    # (3 < 3.14 < 3.14.3)
                    numeric_tags.sort(
                        key=lambda x: [
                            int(c)
                            for c in x.lstrip("v").split(".")
                            if x.lstrip("v").replace(".", "").isdigit()
                        ]
                    )

                    most_specific = numeric_tags[-1]
                    # Identify hierarchy: if most specific is 3.14.3, we want [3, 3.14, 3.14.3]
                    # But only if those tags actually exist in numeric_tags
                    parts = most_specific.lstrip("v").split(".")
                    hierarchy = []
                    for i in range(1, len(parts) + 1):
                        prefix = ".".join(parts[:i])
                        # Handle "v" prefix if present
                        if f"v{prefix}" in numeric_tags:
                            hierarchy.append(f"v{prefix}")
                        elif prefix in numeric_tags:
                            hierarchy.append(prefix)

                    release_lines = hierarchy

                # Also fallback if no numeric hierarchy found
                if not release_lines:
                    semver_tags = [
                        t
                        for t in repo_tags
                        if _classify_tag(t) in ("semver", "calver", "semver-variant")
                    ]
                    if semver_tags:
                        semver_tags.sort(key=len, reverse=True)
                        release_lines = [semver_tags[0]]

            except Exception as e:
                logger.debug("Failed to inspect %s to find release lines: %s", tag, e)

        report = {
            "analyzer": self.name,
            "repository": repository,
            "total_tags": len(tags),
            "dominant_pattern": dominant,
            "semver_compliant_percentage": semver_compliant,
            "patterns": patterns,
            "variants": [
                {
                    "name": v,
                    "count": count,
                    "percentage": round(count / len(tags) * 100, 1) if tags else 0,
                    "examples": sorted(variant_examples[v])[:10],
                }
                for v, count in sorted(
                    variant_counts.items(), key=lambda x: x[1], reverse=True
                )
            ],
            "release_lines": release_lines,
        }

        return report
