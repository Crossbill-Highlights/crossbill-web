#!/bin/bash
# Build+push a nightly image and deploy it to Railway on-demand.
#
# Why not `railway redeploy`? Railway caches a floating tag's digest for hours and
# redeploy reuses the existing deployment's image reference, so it will NOT pick up
# a freshly-pushed :nightly. Instead we push a uniquely-tagged image and point the
# service at it via the GraphQL API, which forces an immediate deploy of the new
# digest. You never copy a tag by hand; the pinned tag also gives clean rollbacks.
#
# Requirements (no `railway` CLI / login needed — talks to the API directly):
#   - RAILWAY_API_TOKEN   Account/Team token: railway.com -> Account -> Tokens.
#                         NOTE: must be this name, NOT RAILWAY_TOKEN (the CLI
#                         reserves RAILWAY_TOKEN for project tokens and will
#                         reject an account token placed there).
#   - RAILWAY_SERVICE_ID / RAILWAY_ENVIRONMENT_ID   which service+env to deploy.
#                         Resource IDs (not kept in-repo). Find them once with
#                         `railway status --json` and export alongside the token.
#   - docker buildx, jq, curl
set -euo pipefail

: "${RAILWAY_API_TOKEN:?Set RAILWAY_API_TOKEN (railway.com -> Account -> Tokens; NOT RAILWAY_TOKEN)}"

SERVICE_ID="${RAILWAY_SERVICE_ID:?Set RAILWAY_SERVICE_ID (find it with: railway status --json)}"
ENVIRONMENT_ID="${RAILWAY_ENVIRONMENT_ID:?Set RAILWAY_ENVIRONMENT_ID (find it with: railway status --json)}"
API="https://backboard.railway.com/graphql/v2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

TAG="nightly-$(date +%Y%m%d%H%M%S)"
IMAGE="tumetsu/crossbill:${TAG}"

# 1. Build & push the pinned tag (also refreshes the moving :nightly tag).
"${SCRIPT_DIR}/build-for-docker-hub.sh" "$TAG"

gql() {
  # $1 = full JSON request body; fails the script on a GraphQL error.
  local resp
  resp="$(curl -sS -X POST "$API" \
    -H "Authorization: Bearer ${RAILWAY_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "$1")"
  if echo "$resp" | jq -e '.errors' >/dev/null 2>&1; then
    echo "Railway API error: $resp" >&2
    exit 1
  fi
}

echo "Pointing Railway service at ${IMAGE} and deploying..."

# 3. Update the service's source image to the freshly-pushed tag.
gql "$(jq -n --arg svc "$SERVICE_ID" --arg env "$ENVIRONMENT_ID" --arg image "$IMAGE" '{
  query: "mutation($serviceId: String!, $environmentId: String, $input: ServiceInstanceUpdateInput!) { serviceInstanceUpdate(serviceId: $serviceId, environmentId: $environmentId, input: $input) }",
  variables: { serviceId: $svc, environmentId: $env, input: { source: { image: $image } } }
}')"

# 4. Trigger the deployment.
gql "$(jq -n --arg svc "$SERVICE_ID" --arg env "$ENVIRONMENT_ID" '{
  query: "mutation($serviceId: String!, $environmentId: String!) { serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId) }",
  variables: { serviceId: $svc, environmentId: $env }
}')"

echo "Deployed ${IMAGE} to Railway."
