# Infrastructure for integration tests

This directory contains an infrastructure for end-to-end integration tests for helmupdater with local Helm registries (HTTP and OCI).

## Components

### Charts

There are sample charts provided for testing purpose:

- nginx
- podinfo

Charts are located at `./charts/`. Pre-built versions are also included so that chart hash is known ahead of time.

Each chart is available in a few release versions. It is used to test update logic. Note that versioning is implemented slightly differently to reflect real-life scenarios:

- `nginx` chart is versioned as "1.0.0", "1.0.1" (numerical only)
- `podinfo` chart is versioned with a "v" prefix: "v1.0.0", "v1.0.1"

### HTTP Registry

- Uses ChartMuseum for chart management
- Accessible at: `http://localhost:45010`
- No authentication required
- Automatically generates and serves `index.yaml`
- Charts are pushed via ChartMuseum API
- Ephemeral storage (data is lost when container stops)

### OCI Registry

- Uses Docker Distribution (registry:3)
- Accessible at: `http://localhost:45020`, debug port is exposed on `http://localhost:45021`
- **Anonymous token authentication** (mimics Docker Hub behavior)
  - Uses OAuth2 token server (cesanta/docker_auth)
  - For read-only access no credentials required - clients can request tokens anonymously
  - For admin access, use username `testuser` with password `testpass`
  - Token server accessible at: `localhost:45030`
  - Issues real JWT tokens for authentication
- Authentication flow:
  1. Client attempts access without auth
  2. Registry returns 401 with token endpoint in WWW-Authenticate header
  3. Client requests JWT token from OAuth2 server (no credentials needed)
  4. Client retries request with Bearer token
  5. Registry validates token and grants access
- Ephemeral storage (data is lost when container stops)

## Prerequisites

- Docker and Docker Compose
- Helm CLI
- bash

## Quick Start

### 1. Setup the test environment

```bash
./setup.sh
```

This will:

- Generate certificates for OCI registry
- Start HTTP, OCI and OAuth2 registries via Docker Compose

### 2. Build a chart

Make a change to the chart, and bump the chart version. Then do the following:

```bash
cd tests/_infra/charts
helm package nginx
helm package podinfo
```

### 3. Publish a chart

```bash
cd tests/_infra
./push-to-http-registry.sh
./push-to-oci-registry.sh
```

This will upload all built charts (`*.tgz`) to the corresponding registry.

### 4. Test with helmupdater

After publishing charts, you can test helmupdater against the HTTP registry:

```bash
# Add a test chart to your nixhelm configuration
helmupdater init http://localhost:45010 localhost/nginx

# Update the chart
helmupdater update localhost/nginx
```

### 5. Cleanup

```bash
./cleanup.sh
```

This will stop all services and remove generated files.

## Manual Testing

### HTTP Registry

```bash
# see all the charts
curl http://localhost:45010/index.yaml

# interact with the registry with helm
helm repo add test-repo http://localhost:45010
helm search repo test-repo
helm pull test-repo/nginx --version 1.0.0
helm repo remove test-repo

# pull the chart directly
helm pull http://localhost:45010/charts/nginx-1.0.0.tgz
```

### OCI Registry

See "Authentication flow" for OCI registry described above. Here is an example with `curl`:

```bash
TOKEN=$(curl -s 'http://localhost:45030/auth/token?scope=registry:catalog:*&service=oci-registry' | jq -r .token)

curl -v http://localhost:45020/v2/_catalog -H "Authorization: Bearer $TOKEN"

# see versions of a chart and pull the specific version
TOKEN=$(curl -s 'http://localhost:45030/auth/token?scope=repository:charts/nginx:pull&service=oci-registry' | jq -r .token)

curl -v http://localhost:45020/v2/charts/nginx/tags/list -H "Authorization: Bearer $TOKEN"

DIGEST=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.manifest.v1+json" \
  http://localhost:45020/v2/charts/nginx/manifests/1.0.0 | jq -r '.layers[0].digest')

curl -H "Authorization: Bearer $TOKEN" \
  -L http://localhost:45020/v2/charts/nginx/blobs/${DIGEST} \
  -o nginx-1.0.0.tgz
```

Both `helm` and `crane` handle authentication automatically.

```bash
# helm
# * helm shows only the latest version
helm show chart oci://localhost:45020/charts/nginx
helm pull oci://localhost:45020/charts/nginx --version 1.0.0

# crane
crane catalog localhost:45020
crane ls localhost:45020/charts/nginx
crane digest localhost:45020/charts/nginx:1.0.0
crane manifest localhost:45020/charts/nginx:1.0.0
DIGEST=$(crane manifest localhost:45020/charts/nginx:1.0.0 | jq -r '.layers[0].digest')
crane blob localhost:45020/charts/nginx@$DIGEST > nginx-1.0.0.tgz
```

## Troubleshooting

```bash
# check registries logs
docker compose logs

# check service health
docker compose ps
```
