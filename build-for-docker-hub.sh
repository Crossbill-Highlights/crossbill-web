#!/bin/bash
# Usage: ./build-for-docker-hub.sh
# Then on home-network run deployment with docker compose

set -e  # Exit on error

# Check if we're on the main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Error: You must be on the main branch to build for Docker Hub"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

echo "Fetching latest tags from Docker Hub..."
# Get the latest tags from Docker Hub
LATEST_TAGS=$(curl -s "https://hub.docker.com/v2/repositories/tumetsu/crossbill/tags/?page_size=10" | \
    jq -r '.results[].name' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V -r | head -5)

echo "Latest tags in Docker Hub:"
echo "$LATEST_TAGS"
echo ""

# Prompt for new tag
read -p "Enter the new version tag (e.g., v0.2.0): " NEW_TAG

# Validate tag format
if [[ ! "$NEW_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Tag must be in format vX.Y.Z (e.g., v0.2.0)"
    exit 1
fi

# Check if tag already exists
if echo "$LATEST_TAGS" | grep -q "^$NEW_TAG$"; then
    echo "Error: Tag $NEW_TAG already exists in Docker Hub"
    exit 1
fi

echo "Building Docker images..."
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -t crossbill:latest -f ./Dockerfile .
docker tag crossbill:latest tumetsu/crossbill:latest
docker tag crossbill:latest tumetsu/crossbill:$NEW_TAG

echo "Pushing to docker registry..."
docker push tumetsu/crossbill:latest
docker push tumetsu/crossbill:$NEW_TAG

echo "Done! Pushed tags: latest, $NEW_TAG"
