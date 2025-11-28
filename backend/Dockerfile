# --- Stage 1: Build Frontend (Root Context) ---
# FIX: Switched from 'buster' to 'bookworm' to fix apt 404 errors
FROM node:16-bookworm AS frontend-builder
WORKDIR /frontend

# FIX: We use 'frontend/' because we are in the Root Context
COPY frontend/package.json frontend/yarn.lock ./
RUN npm install
COPY frontend/ .
ENV NODE_ENV=production
RUN npm run build:dll
RUN npm run build

# --- Stage 2: Build Backend (Root Context) ---
# FIX: Switched from 'buster' to 'bookworm' to fix apt 404 errors
# ARM64: python:3.9-slim-bookworm has native ARM64 support
FROM python:3.9-slim-bookworm

ENV OJ_ENV=production
WORKDIR /app

# Install system dependencies
# Note: Debian Bookworm has all these packages available
# ARM64: All packages are available for ARM64 architecture
# psycopg2 requires libpq-dev to compile from source on ARM
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    curl \
    gettext \
    nginx \
    supervisor \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create nginx user if it doesn't exist (required by nginx.conf)
RUN getent group nginx >/dev/null || groupadd -r nginx && \
    getent passwd nginx >/dev/null || useradd -r -g nginx -s /sbin/nologin -d /var/cache/nginx -c "nginx user" nginx

# FIX: Add 'backend/' prefix to the source path
COPY backend/deploy/requirements.txt /app/deploy/
RUN pip install --no-cache-dir -r /app/deploy/requirements.txt

# FIX: Copy the specific 'backend' folder into /app
COPY backend/ /app/

# Copy the built frontend assets from Stage 1
COPY --from=frontend-builder /frontend/dist /app/dist/

# Permissions
RUN chmod -R u=rwX,go=rX ./ && chmod +x ./deploy/entrypoint.sh

EXPOSE 8000
ENTRYPOINT [ "/app/deploy/entrypoint.sh" ]
