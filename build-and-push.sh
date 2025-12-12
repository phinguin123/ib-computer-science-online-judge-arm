#!/bin/bash
# ============================================
# Build and Push Docker Images for Staging
# ============================================
# This script builds all three Docker images and pushes them to Docker Hub
# under the grow20/onlinejudge namespace

set -e  # Exit on any error

# Configuration
DOCKER_REGISTRY="grow20"
IMAGE_PREFIX="onlinejudge"
TAG="${1:-latest}"  # Use first argument as tag, default to 'latest'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building and Pushing Docker Images${NC}"
echo -e "${GREEN}Registry: ${DOCKER_REGISTRY}${NC}"
echo -e "${GREEN}Tag: ${TAG}${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if user is logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}Warning: You may not be logged into Docker Hub${NC}"
    echo -e "${YELLOW}Run: docker login${NC}\n"
fi

# Function to build and push an image
build_and_push() {
    local SERVICE=$1
    local DOCKERFILE_PATH=$2
    local BUILD_CONTEXT=$3
    local IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_PREFIX}-${SERVICE}:${TAG}"
    
    echo -e "${GREEN}[1/2] Building ${SERVICE}...${NC}"
    echo -e "  Image: ${IMAGE_NAME}"
    echo -e "  Context: ${BUILD_CONTEXT}"
    echo -e "  Dockerfile: ${DOCKERFILE_PATH}\n"
    
    docker build \
        -f "${DOCKERFILE_PATH}" \
        -t "${IMAGE_NAME}" \
        "${BUILD_CONTEXT}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build successful for ${SERVICE}${NC}\n"
    else
        echo -e "${RED}✗ Build failed for ${SERVICE}${NC}\n"
        exit 1
    fi
    
    echo -e "${GREEN}[2/2] Pushing ${SERVICE}...${NC}"
    docker push "${IMAGE_NAME}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Push successful for ${SERVICE}${NC}\n"
    else
        echo -e "${RED}✗ Push failed for ${SERVICE}${NC}\n"
        exit 1
    fi
}

# Build and push Backend
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Backend${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
build_and_push "backend" "backend/Dockerfile" "backend"

# Build and push Frontend
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Frontend${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
build_and_push "frontend" "frontend/Dockerfile" "frontend"

# Build and push Judge Server
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Judge Server${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
build_and_push "judge" "judge-server/Dockerfile" "judge-server"

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All images built and pushed successfully!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Images pushed:"
echo -e "  - ${DOCKER_REGISTRY}/${IMAGE_PREFIX}-backend:${TAG}"
echo -e "  - ${DOCKER_REGISTRY}/${IMAGE_PREFIX}-frontend:${TAG}"
echo -e "  - ${DOCKER_REGISTRY}/${IMAGE_PREFIX}-judge:${TAG}\n"

echo -e "${YELLOW}Note: Update docker-compose.yml to use these images${NC}\n"


