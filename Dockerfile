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

RUN VERSION=$(grep -oP '(?<=version = ")[^"]+' pyproject.toml) && \
    SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION" pip install .

# ──────────────────────────────────────────────────────────────────────────────
# Stage 3: tools-fetcher — downloads external analyzer binaries
# ──────────────────────────────────────────────────────────────────────────────
FROM curlimages/curl:8.10.1 AS tools-fetcher
ARG TARGETARCH
ENV HADOLINT_VERSION=2.12.0 \
    DOCKLE_VERSION=0.4.15

USER root
WORKDIR /tools

# Trivy via the official install script
# hadolint ignore=DL4006
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /tools

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
# git is intentionally absent: it is only used by the host-only
# `bootstrap archive --repo` flow (guarded by require_tool). jq has no
# runtime caller (the only --jq usage is gh's built-in flag).
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      skopeo \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -g 1001 regis && \
    useradd -u 1001 -g regis -m -d /home/regis regis
ENV HOME=/home/regis

# Copy artifacts from build stages
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=tools-fetcher /tools/trivy /usr/local/bin/trivy
COPY --from=tools-fetcher /tools/hadolint /usr/local/bin/hadolint
COPY --from=tools-fetcher /tools/dockle /usr/local/bin/dockle

WORKDIR /home/regis
USER regis

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD regis list || exit 1

ENTRYPOINT ["regis"]
CMD ["--help"]
