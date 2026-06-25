#!/usr/bin/env bash
# Non-regression gate for the shared-OCI-pull handoff (#806 part 2).
# Asserts grype/syft over a local OCI layout match a direct remote scan.
# Usage: scripts/verify_oci_handoff.sh [IMAGE] [PLATFORM]
set -euo pipefail

IMG="${1:-debian:12-slim}"
PLAT="${2:-linux/amd64}"
DIR="$(mktemp -d)"
trap 'rm -rf "$DIR"' EXIT

echo "Exporting $IMG ($PLAT) to a local OCI layout..."
regctl image copy --platform "$PLAT" "$IMG" "ocidir://$DIR/layout:regis"

echo "CVE parity (grype oci-dir: vs grype <image>, platform-pinned both sides)..."
grype "oci-dir:$DIR/layout" -o json \
  | jq -r '.matches[].vulnerability.id' | sort -u > "$DIR/cve_local.txt"
grype "$IMG" --platform "$PLAT" -o json \
  | jq -r '.matches[].vulnerability.id' | sort -u > "$DIR/cve_remote.txt"
if ! diff -q "$DIR/cve_local.txt" "$DIR/cve_remote.txt" >/dev/null; then
  echo "FAIL: CVE sets differ"; diff "$DIR/cve_remote.txt" "$DIR/cve_local.txt" | head; exit 1
fi
echo "  CVE sets identical ($(wc -l < "$DIR/cve_local.txt" | tr -d ' ') ids) ✓"

echo "SBOM parity (syft oci-dir: vs syft <image>, component count)..."
LOCAL_N=$(syft "oci-dir:$DIR/layout" -o syft-json | jq '.artifacts | length')
REMOTE_N=$(syft "$IMG" --platform "$PLAT" -o syft-json | jq '.artifacts | length')
if [ "$LOCAL_N" != "$REMOTE_N" ]; then
  echo "FAIL: component counts differ (local=$LOCAL_N remote=$REMOTE_N)"; exit 1
fi
echo "  component counts identical ($LOCAL_N) ✓"
echo "GATE PASSED for $IMG/$PLAT"
