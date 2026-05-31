"""Lazy downloader for analyzer tool binaries."""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from regis.tools import manifest as _manifest
from regis.tools.manifest import Tool

logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT_S = 120


class ToolFetchError(RuntimeError):
    """Raised when a tool cannot be made available locally."""


@dataclass(frozen=True)
class ToolStatus:
    name: str
    version: str
    cached: bool
    path: Path | None
    sha256_ok: bool | None  # None when not cached


def _detect_arch() -> str:
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "amd64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    raise ToolFetchError(f"unsupported architecture: {machine}")


def _default_cache_dir() -> Path:
    explicit = os.environ.get("REGIS_CACHE_DIR")
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "regis" / "tools"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ToolFetcher:
    def __init__(
        self,
        cache_dir: Path | None = None,
        mirror: str | None = None,
        arch: str | None = None,
        verify_cosign: bool = False,
        require_cosign: bool = False,
        offline: bool = False,
    ) -> None:
        self.cache_dir = (cache_dir or _default_cache_dir()).resolve()
        self.mirror = mirror or os.environ.get("REGIS_TOOLS_MIRROR")
        self.arch = arch or _detect_arch()
        self.verify_cosign = verify_cosign
        self.require_cosign = require_cosign
        self.offline = offline or os.environ.get("REGIS_OFFLINE") == "1"
        self._tools = _manifest.load_manifest()

    def _path_for(self, tool: Tool) -> Path:
        return (
            self.cache_dir / tool.name / tool.version / f"linux-{self.arch}" / tool.name
        )

    def ensure(self, name: str) -> Path:
        tool = self._tools[name]  # KeyError on unknown name (test expects this)
        target = self._path_for(tool)
        expected_sha = tool.sha_for(self.arch)
        if target.exists() and _sha256_file(target) == expected_sha:
            return target
        if self.offline:
            raise ToolFetchError(
                f"{name} not in cache and offline mode is enabled "
                f"(REGIS_OFFLINE=1). Expected at {target}."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        self._download_and_install(tool, target, expected_sha)
        return target

    def _resolve_url(self, tool: Tool) -> str:
        """Compute the download URL, honoring an optional mirror override."""
        if self.mirror:
            ext = {"none": "", "tar.gz": ".tar.gz", "zip": ".zip"}[tool.archive]
            return (
                f"{self.mirror.rstrip('/')}/{tool.name}/{tool.version}/"
                f"{tool.name}_{tool.version}_linux_{self.arch}{ext}"
            )
        return tool.url(arch=self.arch)

    def _download_and_install(
        self, tool: Tool, target: Path, expected_sha: str
    ) -> None:
        """Download ``tool`` to ``target`` after sha256 verification."""
        url = self._resolve_url(tool)
        logger.info("Fetching %s %s from %s", tool.name, tool.version, url)
        with tempfile.NamedTemporaryFile(
            dir=target.parent,
            prefix=f"{tool.name}.",
            suffix=".partial",
            delete=False,
        ) as tmpf:
            partial = Path(tmpf.name)
        try:
            with urllib.request.urlopen(  # nosec B310 — http(s) only, verified by sha256
                url, timeout=DOWNLOAD_TIMEOUT_S
            ) as resp:
                with partial.open("wb") as out:
                    shutil.copyfileobj(resp, out)

            extracted = self._maybe_extract(tool, partial)
            actual = _sha256_file(extracted)
            if actual != expected_sha:
                raise ToolFetchError(
                    f"{tool.name} sha256 mismatch: expected {expected_sha}, got {actual}"
                )
            extracted.replace(target)
            os.chmod(target, 0o755)  # nosec B103 — tool binaries must be executable
        finally:
            if partial.exists():
                partial.unlink()
            # extracted may equal partial; cleanup any sibling
            for stray in target.parent.glob(f"{tool.name}.*.partial*"):
                stray.unlink(missing_ok=True)
            for stray in target.parent.glob(f"{tool.name}.*.partial.extracted"):
                stray.unlink(missing_ok=True)

    def _maybe_extract(self, tool: Tool, archive_path: Path) -> Path:
        """Extract ``tool.member`` from the archive, or return the input as-is."""
        if tool.archive == "none":
            return archive_path
        if tool.member is None:
            raise ToolFetchError(f"{tool.name}: archive set but no member to extract")
        out = archive_path.with_suffix(".extracted")
        if tool.archive == "tar.gz":
            with tarfile.open(archive_path, "r:gz") as tar:
                m = tar.getmember(tool.member)
                src = tar.extractfile(m)
                if src is None:
                    raise ToolFetchError(
                        f"{tool.name}: member {tool.member!r} is not a regular file"
                    )
                with src, out.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        elif tool.archive == "zip":
            with zipfile.ZipFile(archive_path) as zf:
                with zf.open(tool.member) as src, out.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        else:
            raise ToolFetchError(f"unsupported archive type: {tool.archive}")
        archive_path.unlink()
        return out

    def status(self) -> list[ToolStatus]:
        out: list[ToolStatus] = []
        for name, tool in self._tools.items():
            path = self._path_for(tool)
            cached = path.exists()
            sha_ok: bool | None = None
            if cached:
                sha_ok = _sha256_file(path) == tool.sha_for(self.arch)
            out.append(
                ToolStatus(
                    name=name,
                    version=tool.version,
                    cached=cached,
                    path=path if cached else None,
                    sha256_ok=sha_ok,
                )
            )
        return out
