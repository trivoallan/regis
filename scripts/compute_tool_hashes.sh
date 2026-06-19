#!/usr/bin/env bash
set -euo pipefail

TOOLS=(
  "grype|0.112.0|https://github.com/anchore/grype/releases/download/v{version}/grype_{version}_linux_{arch}.tar.gz"
  "syft|1.44.0|https://github.com/anchore/syft/releases/download/v{version}/syft_{version}_linux_{arch}.tar.gz"
  "trufflehog|3.95.3|https://github.com/trufflesecurity/trufflehog/releases/download/v{version}/trufflehog_{version}_linux_{arch}.tar.gz"
  "regctl|0.11.5|https://github.com/regclient/regclient/releases/download/v{version}/regctl-linux-{arch}"
  "dockle|0.4.15|https://github.com/goodwithtech/dockle/releases/download/v{version}/dockle_{version}_Linux-{arch_alt}.tar.gz"
  "hadolint|2.12.0|https://github.com/hadolint/hadolint/releases/download/v{version}/hadolint-Linux-{arch_alt}"
)

for entry in "${TOOLS[@]}"; do
  IFS='|' read -r name version tpl <<<"$entry"
  # Determine extraction policy: archive type and member name.
  # The ToolFetcher in regis/adapters/driven/tools/fetcher.py verifies the sha256 of the
  # EXTRACTED binary (after unpacking the archive), not the archive itself,
  # so we must extract and hash the inner member for archive=tar.gz tools.
  case "$name" in
    grype|syft|trufflehog|dockle) archive=tar.gz; member="$name" ;;
    regctl|hadolint)              archive=none;   member="" ;;
    *) echo "unknown tool: $name" >&2; exit 1 ;;
  esac
  for arch in amd64 arm64; do
    case "$name/$arch" in
      dockle/amd64) arch_alt=64bit ;;
      dockle/arm64) arch_alt=ARM64 ;;
      hadolint/amd64) arch_alt=x86_64 ;;
      hadolint/arm64) arch_alt=arm64 ;;
      *) arch_alt="$arch" ;;
    esac
    url="${tpl//\{version\}/$version}"
    url="${url//\{arch\}/$arch}"
    url="${url//\{arch_alt\}/$arch_alt}"
    if [ "$archive" = "tar.gz" ]; then
      sha=$(curl -sSfL "$url" | tar -xzO "$member" | sha256sum | awk '{print $1}')
    else
      sha=$(curl -sSfL "$url" | sha256sum | awk '{print $1}')
    fi
    echo "$name  $arch  $sha"
  done
done
