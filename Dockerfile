# syntax=docker/dockerfile:1.7

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
FROM python:3.14-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
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
# Stage 4: final — minimal runtime image
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.14-slim AS final

LABEL org.opencontainers.image.title="regis" \
      org.opencontainers.image.description="Regis — Registry Scores. Container Security & Policy-as-Code Orchestration." \
      org.opencontainers.image.url="https://github.com/trivoallan" \
      org.opencontainers.image.source="https://github.com/trivoallan/regis" \
      org.opencontainers.image.documentation="https://trivoallan.github.io/regis/" \
      org.opencontainers.image.vendor="trivoallan" \
      org.opencontainers.image.authors="trivoallan" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH"

# Minimal runtime dependencies only — no curl, no gnupg, no build-essential.
# skopeo is intentionally absent: registry inspection now uses the regctl
# static binary (copied from the tools-fetcher stage below), which removes the
# skopeo apt layer and its transitive dependencies.
# git is intentionally absent: it is only used by the host-only
# `bootstrap archive --repo` flow (guarded by require_tool). jq has no
# runtime caller (the only --jq usage is gh's built-in flag).
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -g 1001 regis && \
    useradd -u 1001 -g regis -m -d /home/regis regis
ENV HOME=/home/regis

# Copy artifacts from build stages
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/grype /usr/local/bin/grype
COPY --from=tools-fetcher /tools/syft /usr/local/bin/syft
COPY --from=tools-fetcher /tools/trufflehog /usr/local/bin/trufflehog
COPY --from=tools-fetcher /tools/hadolint /usr/local/bin/hadolint
COPY --from=tools-fetcher /tools/dockle /usr/local/bin/dockle
COPY --from=tools-fetcher /tools/regctl /usr/local/bin/regctl

WORKDIR /home/regis
USER regis

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD regis list || exit 1

ENTRYPOINT ["regis"]
CMD ["--help"]
