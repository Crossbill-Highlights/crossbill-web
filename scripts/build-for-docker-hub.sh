#!/bin/bash
# Usage: ./build-for-docker-hub.sh
# Builds and pushes nightly release to Docker Hub with a unique tag
# Stable releases should be done by CI

set -e # Exit on error

TIMESTAMP=$(date +%Y%m%d%H%M%S)
UNIQUE_TAG="nightly-${TIMESTAMP}"

echo "Building nightly release (${UNIQUE_TAG})..."
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -t crossbill:nightly -f ./Dockerfile .
docker tag crossbill:nightly tumetsu/crossbill:nightly
docker tag crossbill:nightly tumetsu/crossbill:${UNIQUE_TAG}

echo "Pushing to docker registry..."
docker push tumetsu/crossbill:nightly
docker push tumetsu/crossbill:${UNIQUE_TAG}

echo "Pushed tags: nightly, ${UNIQUE_TAG}"
