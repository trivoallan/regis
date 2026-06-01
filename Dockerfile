# syntax=docker/dockerfile:1.7
ARG VARIANT=slim

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: python-builder — compiles Python deps into a venv
# ──────────────────────────────────────────────────────────────────────────────
# Alpine 3.11 builder paired with Alpine 3.11 runtime — matching musl libc and
# CPython ABIs so the venv's symlinked interpreter resolves cleanly at runtime.
# regis requires python>=3.10 per pyproject.toml.
FROM python:3.11-alpine AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# build-base: gcc/musl-dev for any source-wheel fallback
# linux-headers, libffi-dev, openssl-dev: required by cffi/cryptography-style
# C extensions if PyPI has no musl wheel for the version we resolve.
# Symlinked venv (no --copies): runtime base ships the matching python3.11
# interpreter, so the symlink resolves and we save ~10 MB vs copying.
# hadolint ignore=DL3018
RUN apk add --no-cache build-base linux-headers libffi-dev openssl-dev && \
    python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
COPY pyproject.toml Pipfile Pipfile.lock ./
COPY regis/ regis/

# Core install only. The interactive dashboard + its FastAPI server moved to
# the standalone regis-dashboard repo, so there is no Node build stage and no
# dashboard_assets baked into the image.
# --no-compile skips .pyc generation (PYTHONDONTWRITEBYTECODE keeps runtime
# from regenerating them); prune any residual bytecode caches afterwards.
SHELL ["/bin/ash", "-o", "pipefail", "-c"]
RUN VERSION=$(awk -F'"' '/^version = / { print $2; exit }' pyproject.toml) && \
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
# Runtime base: python:3.11-alpine (round-3 task 14 — Alpine pivot).
# Alpine's ~50 MB base + musl libc beats both python:3.11-slim (~165 MB) and
# distroless (~80 MB but with libpython copy overhead) for this use case.
# PyYAML, MarkupSafe, and other C-extension deps have musl wheels on PyPI;
# the Anchore Go scanners are CGO-free and run cleanly on musl; hadolint
# (Haskell) needs Alpine's gcompat glibc shim in the full variant.
FROM python:3.11-alpine AS final-slim

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
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/opt/venv/lib/python3.11/site-packages \
    REGIS_VARIANT=slim \
    HOME=/home/regis

# ca-certificates for HTTPS to registries / GitHub releases (regis bootstrap
# tools / lazy ensure_tool fetcher uses urllib from stdlib, which honours
# /etc/ssl/certs).
# hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates

# Non-root user (uid 1001) — matches the previous image's runtime identity so
# bind-mounts and CI cache permissions don't break.
RUN addgroup -g 1001 regis && \
    adduser -D -u 1001 -G regis -h /home/regis regis

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
FROM python:3.11-alpine AS final-full

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
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH=/opt/venv/lib/python3.11/site-packages \
    REGIS_VARIANT=full \
    HOME=/home/regis

# ca-certificates: HTTPS to registries.
# gcompat: glibc shim for Alpine — hadolint is a Haskell-compiled binary
# that depends on glibc's dynamic loader; gcompat provides the shim so it
# can run on musl. Adds ~500 KB but is required for hadolint to start.
# hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates gcompat

RUN addgroup -g 1001 regis && \
    adduser -D -u 1001 -G regis -h /home/regis regis

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
