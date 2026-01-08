#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHARTS_DIR="$SCRIPT_DIR/charts"
REGISTRY_URL="oci://localhost:45020"

CHART_FILES="$(find $CHARTS_DIR -maxdepth 1 -type f -path '*.tgz' | sort)"

echo "==> Pushing charts to OCI registry"

echo "==> Uploading charts..."
for CHART_FILE in $CHART_FILES;
do
  echo "  $(basename $CHART_FILE)"
  helm push "$CHART_FILE" "$REGISTRY_URL/charts" \
    --username testuser \
    --password testpass
done

echo "==> Charts pushed successfully to OCI registry!"
echo "    Registry: $REGISTRY_URL/charts"
echo ""
