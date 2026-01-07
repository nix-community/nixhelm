#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHARTS_DIR="$SCRIPT_DIR/charts"
REGISTRY_URL="http://localhost:45010"

CHART_FILES="$(find $CHARTS_DIR -maxdepth 1 -type f -path '*.tgz' | sort)"

echo "==> Pushing charts to HTTP registry"

echo "==> Uploading charts..."
for CHART_FILE in $CHART_FILES;
do
  echo "  $(basename $CHART_FILE)"
  curl --silent --show-error --fail --output /dev/null \
    --data-binary "@$CHART_FILE" "$REGISTRY_URL/api/charts?force=1"
done

echo ""
echo "==> Charts pushed successfully to HTTP registry!"
echo "    Registry: $REGISTRY_URL"
echo ""
