#!/bin/bash
# Usage: ./build-for-gitea.sh
# Then on home-network run deployment with docker compose

set -e  # Exit on error

echo "Building Docker images..."
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -t gitea.lintula.xyz/tuomas/crossbill:latest -f ./Dockerfile .

echo "Pushing to homelab registry..."
docker push gitea.lintula.xyz/tuomas/crossbill:latest

echo "Done!"
