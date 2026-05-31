"""Lazy downloader for analyzer tool binaries."""

from __future__ import annotations

import hashlib
import logging
import os
import platform
from dataclasses import dataclass
from pathlib import Path

from regis.tools import manifest as _manifest
from regis.tools.manifest import Tool

logger = logging.getLogger(__name__)


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
            self.cache_dir
            / tool.name
            / tool.version
            / f"linux-{self.arch}"
            / tool.name
        )

    def ensure(self, name: str) -> Path:
        tool = self._tools[name]  # KeyError on unknown name (test expects this)
        target = self._path_for(tool)
        if target.exists() and _sha256_file(target) == tool.sha_for(self.arch):
            return target
        if self.offline:
            raise ToolFetchError(
                f"{name} not in cache and offline mode is enabled "
                f"(REGIS_OFFLINE=1). Expected at {target}."
            )
        # download path implemented in Task 5
        raise NotImplementedError("download path implemented in next task")

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
