# syntax=docker/dockerfile:1.7
ARG VARIANT=slim

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: frontend-builder — builds the Docusaurus dashboard
# ──────────────────────────────────────────────────────────────────────────────
FROM node:25-slim AS frontend-builder
RUN npm install -g pnpm@10.10.0
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
COPY apps/ apps/
RUN pnpm install --frozen-lockfile
WORKDIR /app/apps/dashboard
RUN pnpm run build

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: python-builder — compiles Python deps into a venv
# ──────────────────────────────────────────────────────────────────────────────
# Was python:3.14-slim. Pinned to 3.11 because the runtime base
# (gcr.io/distroless/python3-debian12) ships Python 3.11; aligning ABIs.
# regis requires python>=3.10 per pyproject.toml.
FROM python:3.11-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# --copies (not symlinks): distroless has no /usr/local/bin/python to satisfy
# the venv's default interpreter symlink. Real binary lets the regis console
# script shebang resolve at runtime.
RUN python -m venv --copies /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
COPY pyproject.toml Pipfile Pipfile.lock ./
COPY regis/ regis/
COPY --from=frontend-builder /app/apps/dashboard/build regis/dashboard_assets

# Core install only — the optional [server] extra (FastAPI/Uvicorn) is
# intentionally excluded to keep the runtime image small. Use a host with
# `pip install 'regis[server]'` for `regis dashboard serve`.
# --no-compile skips .pyc generation (PYTHONDONTWRITEBYTECODE keeps runtime
# from regenerating them); prune any residual bytecode caches afterwards.
RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install --no-compile . && \
    find /opt/venv -type d -name __pycache__ -prune -exec rm -rf {} + && \
    find /opt/venv -type f -name '*.pyc' -delete

# ──────────────────────────────────────────────────────────────────────────────
# Stage 3: tools-fetcher — downloads external analyzer binaries
# ──────────────────────────────────────────────────────────────────────────────
FROM curlimages/curl:8.10.1 AS tools-fetcher
ARG TARGETARCH
ENV HADOLINT_VERSION=2.12.0 \
    DOCKLE_VERSION=0.4.15 \
    REGCTL_VERSION=0.11.5 \
    GRYPE_VERSION=0.112.0 \
    SYFT_VERSION=1.44.0 \
    TRUFFLEHOG_VERSION=3.95.3

USER root
WORKDIR /tools

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

# Hadolint
RUN case "$TARGETARCH" in \
      amd64) hadolint_arch="x86_64" ;; \
      arm64) hadolint_arch="arm64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-Linux-${hadolint_arch}" \
      -o /tools/hadolint && \
    chmod +x /tools/hadolint

# Dockle
RUN case "$TARGETARCH" in \
      amd64) dockle_arch="64bit" ;; \
      arm64) dockle_arch="ARM64" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/goodwithtech/dockle/releases/download/v${DOCKLE_VERSION}/dockle_${DOCKLE_VERSION}_Linux-${dockle_arch}.tar.gz" \
      -o /tmp/dockle.tar.gz && \
    tar -xzf /tmp/dockle.tar.gz -C /tools dockle && \
    chmod +x /tools/dockle && \
    rm /tmp/dockle.tar.gz

# regctl (static binary; replaces skopeo for registry inspection)
RUN case "$TARGETARCH" in \
      amd64|arm64) regctl_arch="$TARGETARCH" ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sSfL "https://github.com/regclient/regclient/releases/download/v${REGCTL_VERSION}/regctl-linux-${regctl_arch}" \
      -o /tools/regctl && \
    chmod +x /tools/regctl

USER curl_user

# ──────────────────────────────────────────────────────────────────────────────
# Stage 4a: final-slim — minimal runtime with only regctl baked
# ──────────────────────────────────────────────────────────────────────────────
# Runtime base: python:3.11-slim (Fallback 3 from the round-3 plan).
# Distroless (gcr.io/distroless/python3-debian12) was the original target but
# does not ship libpython3.11.so.1.0 as a usable shared library, so a venv's
# `--copies` Python interpreter cannot dynamically link against it at runtime
# (it fails with "libpython3.11.so.1.0: cannot open shared object file").
# python:3.11-slim adds ~30-40 MB vs distroless but lifts the size ceiling
# from <100 MB to ~120-140 MB, still well under the 150 MB target.
FROM python:3.11-slim AS final-slim

LABEL org.opencontainers.image.title="regis" \
      org.opencontainers.image.description="Regis — Slim variant (scanners lazy-loaded at first use)." \
      org.opencontainers.image.url="https://github.com/trivoallan" \
      org.opencontainers.image.source="https://github.com/trivoallan/regis" \
      org.opencontainers.image.documentation="https://trivoallan.github.io/regis/" \
      org.opencontainers.image.vendor="trivoallan" \
      org.opencontainers.image.authors="trivoallan" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/opt/venv/lib/python3.11/site-packages \
    REGIS_VARIANT=slim \
    HOME=/home/regis

# Minimal runtime dependencies — ca-certificates for HTTPS, plus the tools
# fetcher (regis bootstrap tools / lazy ensure_tool) needs curl-style network
# access; the regis.tools.fetcher module uses urllib from the stdlib so no
# extra apt deps are required here.
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Non-root user (uid 1001) — matches the previous image's runtime identity so
# bind-mounts and CI cache permissions don't break.
RUN groupadd -g 1001 regis && \
    useradd -u 1001 -g regis -m -d /home/regis regis

COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/regctl /usr/local/bin/regctl

WORKDIR /home/regis
USER regis

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["regis", "list"]
ENTRYPOINT ["regis"]
CMD ["--help"]

# ──────────────────────────────────────────────────────────────────────────────
# Stage 4b: final-full — minimal runtime with all scanners baked
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS final-full

LABEL org.opencontainers.image.title="regis" \
      org.opencontainers.image.description="Regis — Full variant (all scanners baked)." \
      org.opencontainers.image.url="https://github.com/trivoallan" \
      org.opencontainers.image.source="https://github.com/trivoallan/regis" \
      org.opencontainers.image.documentation="https://trivoallan.github.io/regis/" \
      org.opencontainers.image.vendor="trivoallan" \
      org.opencontainers.image.authors="trivoallan" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/opt/venv/lib/python3.11/site-packages \
    REGIS_VARIANT=full \
    HOME=/home/regis

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1001 regis && \
    useradd -u 1001 -g regis -m -d /home/regis regis

COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/grype      /usr/local/bin/grype
COPY --from=tools-fetcher /tools/syft       /usr/local/bin/syft
COPY --from=tools-fetcher /tools/trufflehog /usr/local/bin/trufflehog
COPY --from=tools-fetcher /tools/hadolint   /usr/local/bin/hadolint
COPY --from=tools-fetcher /tools/dockle     /usr/local/bin/dockle
COPY --from=tools-fetcher /tools/regctl     /usr/local/bin/regctl

WORKDIR /home/regis
USER regis

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["regis", "list"]
ENTRYPOINT ["regis"]
CMD ["--help"]

# ──────────────────────────────────────────────────────────────────────────────
# Final selector — picks final-slim or final-full based on VARIANT build-arg.
# DL3006/CKV_DOCKER_7 are suppressed: `final-${VARIANT}` resolves to a local
# build stage (final-slim or final-full above), not an external image, so the
# "pin the tag" advice does not apply.
# ──────────────────────────────────────────────────────────────────────────────
# trunk-ignore(checkov/CKV_DOCKER_7,hadolint/DL3006)
FROM final-${VARIANT} AS final
