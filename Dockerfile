# Stage 1: Build the React viewer assets
FROM node:25-slim AS frontend-builder
RUN corepack enable pnpm
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
COPY apps/ apps/
COPY docs/ docs/
RUN pnpm install --frozen-lockfile
WORKDIR /app/apps/report-viewer
RUN pnpm run build

# Stage 2: Build the final Python image
FROM python:3.14-slim

LABEL org.opencontainers.image.title="regis-cli" \
      org.opencontainers.image.description="Container Security & Policy-as-Code Orchestration. Unified analysis, custom playbooks, and highly customizable interactive reports for production-ready CI/CD." \
      org.opencontainers.image.url="https://github.com/trivoallan" \
      org.opencontainers.image.source="https://github.com/trivoallan/regis-cli" \
      org.opencontainers.image.documentation="https://trivoallan.github.io/regis-cli/" \
      org.opencontainers.image.vendor="trivoallan" \
      org.opencontainers.image.authors="trivoallan" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and analyzers
# Consolidation and upgrade for latest security patches
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    skopeo \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with a home directory and ensure it's writable
RUN groupadd -g 1001 regis && \
    useradd -u 1001 -g regis -m -d /home/regis regis && \
    chmod 755 /home/regis
ENV HOME=/home/regis

# Install Trivy (latest version from official install script)
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Install Hadolint
ENV HADOLINT_VERSION="2.12.0"
RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ]; then hadolint_arch="x86_64"; else hadolint_arch="arm64"; fi && \
    curl -sSfL "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-Linux-${hadolint_arch}" -o /usr/local/bin/hadolint && \
    chmod +x /usr/local/bin/hadolint

# Install Dockle
ENV DOCKLE_VERSION="0.4.15"
RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ]; then dockle_arch="64bit"; else dockle_arch="ARM64"; fi && \
    curl -L -o dockle.tar.gz https://github.com/goodwithtech/dockle/releases/download/v${DOCKLE_VERSION}/dockle_${DOCKLE_VERSION}_Linux-${dockle_arch}.tar.gz && \
    tar zxvf dockle.tar.gz dockle && \
    mv dockle /usr/local/bin/dockle && \
    rm dockle.tar.gz && \
    chmod +x /usr/local/bin/dockle

# Set work directory and ensure it's owned by regis
WORKDIR /app
RUN chown regis:regis /app && chmod 777 /app

# Copy project files and ensure ownership
COPY --chown=regis:regis . .

# Copy built viewer assets from frontend stage
COPY --from=frontend-builder --chown=regis:regis /app/apps/report-viewer/build ./regis_cli/viewer_assets

# Install regis-cli
RUN git config --global --add safe.directory /app && \
    pip install --no-cache-dir .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD regis-cli list || exit 1

# Switch to non-root user
USER regis

# Default command
ENTRYPOINT ["regis-cli"]
CMD ["--help"]
