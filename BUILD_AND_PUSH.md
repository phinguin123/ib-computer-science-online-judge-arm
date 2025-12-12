# Building and Pushing Docker Images for Staging

This guide explains how to build and push all Docker images to Docker Hub for staging deployment.

## Prerequisites

1. **Docker installed** and running
2. **Logged into Docker Hub**:
   ```bash
   docker login
   ```
   Enter your Docker Hub username and password (or access token)

3. **Docker Hub permissions**: You need push access to the `grow20` organization on Docker Hub

## Quick Start

### Build and Push All Images (Latest Tag)

```bash
./build-and-push.sh
```

This will build and push:
- `grow20/onlinejudge-backend:latest`
- `grow20/onlinejudge-frontend:latest`
- `grow20/onlinejudge-judge:latest`

### Build and Push with Custom Tag

```bash
./build-and-push.sh v1.0.0
```

This will create images with the tag `v1.0.0`:
- `grow20/onlinejudge-backend:v1.0.0`
- `grow20/onlinejudge-frontend:v1.0.0`
- `grow20/onlinejudge-judge:v1.0.0`

## Manual Build (Individual Services)

If you need to build and push individual services:

### Backend
```bash
docker build -f backend/Dockerfile -t grow20/onlinejudge-backend:latest backend/
docker push grow20/onlinejudge-backend:latest
```

### Frontend
```bash
docker build -f frontend/Dockerfile -t grow20/onlinejudge-frontend:latest frontend/
docker push grow20/onlinejudge-frontend:latest
```

### Judge Server
```bash
docker build -f judge-server/Dockerfile -t grow20/onlinejudge-judge:latest judge-server/
docker push grow20/onlinejudge-judge:latest
```

## After Pushing

Once images are pushed, you can deploy using `docker-compose.yml`:

```bash
docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d
```

## Troubleshooting

### Authentication Issues
If you get authentication errors:
```bash
docker login
# Enter your Docker Hub credentials
```

### Build Failures
- Check that all source files are present
- Ensure Docker has enough resources (memory, disk space)
- Review Dockerfile syntax and paths

### Push Failures
- Verify you have push permissions to `grow20` organization
- Check your internet connection
- Ensure the image names match exactly

## Image Names Reference

The images follow this naming convention:
- `grow20/onlinejudge-{service}:{tag}`

Where:
- `{service}` is one of: `backend`, `frontend`, `judge`
- `{tag}` is typically `latest` for staging, or a version number for releases


