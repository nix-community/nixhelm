#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Setting up integration test environment"

# Generate self-signed certificates for docker_auth if they don't exist
if [ ! -f "oauth2-server/certs/server.pem" ] || [ ! -f "oauth2-server/certs/server-key.pem" ]; then
    echo "==> Generating self-signed certificates for OAuth2 token server..."
    mkdir -p oauth2-server/certs
    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
        -subj "/C=US/ST=Test/L=Test/O=Test/CN=localhost" \
        -keyout oauth2-server/certs/server-key.pem \
        -out oauth2-server/certs/server.pem
    echo "    Certificates generated in oauth2-server/certs/"
else
    echo "==> Certificates already exist, skipping generation"
fi

echo "==> Starting Docker Compose services..."
if ! docker compose up --detach --wait --wait-timeout 10; then
  docker compose logs
  exit 1
fi

./push-to-http-registry.sh
./push-to-oci-registry.sh

echo "==> Integration test environment is ready!"
echo ""
echo "HTTP Registry: http://localhost:45010"
echo "OCI Registry:  oci://localhost:45020"
echo ""
echo "To stop: docker compose down"
echo "To clean: ./cleanup.sh"
