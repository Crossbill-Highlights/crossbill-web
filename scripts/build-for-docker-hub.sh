#!/bin/bash
# Usage: ./build-for-docker-hub.sh
# Builds and pushes nightly release to Docker Hub with a unique tag.
# Stable releases should be done by CI.
#
# Requires `docker buildx` (BuildKit). Bundled with Docker Engine 23+ on Linux.
# On macOS with the Homebrew docker CLI (no Docker Desktop):
#   brew install docker-buildx
#   mkdir -p ~/.docker/cli-plugins
#   ln -sfn "$(brew --prefix)/opt/docker-buildx/bin/docker-buildx" \
#     ~/.docker/cli-plugins/docker-buildx

set -e # Exit on error

TIMESTAMP=$(date +%Y%m%d%H%M%S)
UNIQUE_TAG="nightly-${TIMESTAMP}"

echo "Building and pushing nightly release (${UNIQUE_TAG})..."

docker buildx build \
  --platform linux/amd64 \
  -t tumetsu/crossbill:nightly \
  -t "tumetsu/crossbill:${UNIQUE_TAG}" \
  -f ./Dockerfile \
  --push \
  .

echo "Pushed tags: nightly, ${UNIQUE_TAG}"
