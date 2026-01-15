#!/bin/bash
# Usage: ./build-for-docker-hub.sh
# Builds and pushes nightly release to Docker Hub
# Stable releases should be done by CI

set -e # Exit on error

echo "Building nightly release..."
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -t crossbill:nightly -f ./Dockerfile .
docker tag crossbill:nightly tumetsu/crossbill:nightly

echo "Pushing to docker registry..."
docker push tumetsu/crossbill:nightly

echo "Done! Pushed tag: nightly"
