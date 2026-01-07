#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Stopping Docker Compose services..."
docker compose down -v

echo "==> Removing generated certs..."
rm -rfv ./oauth2-server/certs

echo "==> Cleanup complete!"
