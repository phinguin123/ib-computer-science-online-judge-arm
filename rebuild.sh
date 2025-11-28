#!/bin/bash
# Quick rebuild script for docker-compose

echo "Rebuilding and restarting services..."

# Rebuild specific service (faster)
if [ -n "$1" ]; then
    docker compose build --no-cache "$1"
    docker compose up -d "$1"
else
    # Rebuild all services
    docker compose build --no-cache
    docker compose up -d
fi

echo "Done! Services restarted."

