"""Authentication resolution for the Docker Registry."""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def resolve_credentials(
    registry: str,
    cli_auths: list[str] | None = None,
) -> tuple[str | None, str | None]:
    """Resolve credentials for a given registry domain.

    Order of precedence:
    1. CLI-provided auth overrides (--auth flag)
    2. Domain-specific env vars (e.g., REGIS_AUTH_REGISTRY_EXAMPLE_COM_USERNAME)
    3. Global env vars (REGIS_USERNAME / REGIS_PASSWORD)
    4. Docker config.json (~/.docker/config.json)

    Args:
        registry: The registry hostname to authenticate against.
        cli_auths: A list of string overrides in the form 'registry=user:pass'.

    Returns:
        A tuple of (username, password) if found, otherwise (None, None).
    """
    # Normalize registry aliases (especially for Docker Hub)
    aliases = {registry}
    if registry in ("registry-1.docker.io", "docker.io", "index.docker.io"):
        aliases.update({"registry-1.docker.io", "docker.io", "index.docker.io"})

    # 1. Check CLI overrides
    if cli_auths:
        for auth_override in cli_auths:
            if "=" in auth_override:
                domain, creds = auth_override.split("=", 1)
                if (domain == registry or domain in aliases) and ":" in creds:
                    user, pwd = creds.split(":", 1)
                    logger.debug("Using CLI override credentials for %s", registry)
                    return user, pwd

    # 2. Check domain-specific environment variables
    for alias in sorted(aliases):
        env_domain = alias.upper().replace(".", "_").replace(":", "_").replace("-", "_")
        domain_user: str | None = os.environ.get(f"REGIS_AUTH_{env_domain}_USERNAME")
        domain_pass: str | None = os.environ.get(f"REGIS_AUTH_{env_domain}_PASSWORD")
        if domain_user and domain_pass:
            logger.debug(
                "Using domain-specific env vars for %s (via alias %s)", registry, alias
            )
            return domain_user, domain_pass

    # 3. Check DOCKER_AUTH_CONFIG environment variable (JSON string)
    docker_auth_config = os.environ.get("DOCKER_AUTH_CONFIG")
    if docker_auth_config:
        try:
            config = json.loads(docker_auth_config)
            docker_auth_user, docker_auth_pwd = _extract_from_docker_config(
                registry, config, aliases
            )
            if docker_auth_user and docker_auth_pwd:
                logger.debug("Using DOCKER_AUTH_CONFIG env var for %s", registry)
                return docker_auth_user, docker_auth_pwd
        except Exception as e:
            logger.debug("Failed to parse DOCKER_AUTH_CONFIG: %s", e)

    # 4. Check registry-specific fallbacks (e.g. Docker Hub)
    if registry in ("registry-1.docker.io", "docker.io", "index.docker.io"):
        for prefix in ("DOCKER_HUB", "DOCKER"):
            prefix_user: str | None = os.environ.get(f"{prefix}_USERNAME")
            prefix_pwd: str | None = os.environ.get(f"{prefix}_PASSWORD")
            if prefix_user and prefix_pwd:
                logger.debug("Using %s_* env vars for %s", prefix, registry)
                return prefix_user, prefix_pwd

    # 5. Check global environment variables
    global_user: str | None = os.environ.get("REGIS_USERNAME")
    global_pass: str | None = os.environ.get("REGIS_PASSWORD")
    if global_user and global_pass:
        logger.debug("Using global env vars for %s", registry)
        return global_user, global_pass

    # 6. Check Docker config.json
    try:
        docker_config_path = Path.home() / ".docker" / "config.json"
        if docker_config_path.exists():
            with open(docker_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            user_config, pwd_config = _extract_from_docker_config(
                registry, config, aliases
            )
            if user_config and pwd_config:
                logger.debug("Using Docker config.json credentials for %s", registry)
                return user_config, pwd_config
    except Exception as e:
        logger.debug("Failed to read ~/.docker/config.json: %s", e)

    return None, None


def _extract_from_docker_config(
    registry: str, config: dict[str, Any], aliases: set[str]
) -> tuple[str | None, str | None]:
    """Extract credentials from a Docker config-style dictionary."""
    auths = config.get("auths", {})
    candidates = [
        registry,
        f"https://{registry}",
        f"https://{registry}/v1/",
        f"https://{registry}/v2/",
    ]
    if registry in ("docker.io", "registry-1.docker.io", "index.docker.io"):
        candidates.append("https://index.docker.io/v1/")

    for candidate in candidates:
        if candidate in auths and "auth" in auths[candidate]:
            auth_b64 = auths[candidate]["auth"]
            try:
                auth_str = base64.b64decode(auth_b64).decode("utf-8")
                if ":" in auth_str:
                    return tuple(auth_str.split(":", 1))  # type: ignore[return-value]
            except Exception as e:
                logger.debug(
                    "Failed to decode auth from config for %s: %s",
                    candidate,
                    e,
                )
    return None, None
