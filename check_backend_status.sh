#!/bin/bash
# Diagnostic script to check backend status from host

echo "=== Backend Container Status ==="
docker compose ps oj-backend 2>/dev/null || docker-compose ps oj-backend 2>/dev/null

echo -e "\n=== Backend Container Logs (last 50 lines) ==="
docker compose logs --tail=50 oj-backend 2>/dev/null || docker-compose logs --tail=50 oj-backend 2>/dev/null

echo -e "\n=== Checking if backend is listening on port 8000 ==="
docker compose exec -T oj-backend netstat -tuln 2>/dev/null | grep :8000 || docker compose exec -T oj-backend ss -tuln 2>/dev/null | grep :8000 || echo "Port 8000 not found in netstat/ss output"

echo -e "\n=== Checking gunicorn processes ==="
docker compose exec -T oj-backend ps aux 2>/dev/null | grep gunicorn || echo "No gunicorn processes found"

echo -e "\n=== Checking supervisord status ==="
docker compose exec -T oj-backend supervisorctl -c /app/deploy/supervisord.conf status 2>/dev/null || echo "Could not get supervisord status"

echo -e "\n=== Backend Debug Logs (last 30 lines) ==="
if [ -f "./data/backend/log/debug.log" ]; then
    tail -30 ./data/backend/log/debug.log | python3 -m json.tool 2>/dev/null || tail -30 ./data/backend/log/debug.log
else
    echo "Debug log file not found at ./data/backend/log/debug.log"
    echo "Trying to read from container..."
    docker compose exec -T oj-backend tail -30 /data/log/debug.log 2>/dev/null | python3 -m json.tool 2>/dev/null || docker compose exec -T oj-backend tail -30 /data/log/debug.log 2>/dev/null || echo "Could not read debug log from container"
fi

echo -e "\n=== Gunicorn Logs (last 20 lines) ==="
if [ -f "./data/backend/log/gunicorn.log" ]; then
    tail -20 ./data/backend/log/gunicorn.log
else
    echo "Gunicorn log file not found at ./data/backend/log/gunicorn.log"
    echo "Trying to read from container..."
    docker compose exec -T oj-backend tail -20 /data/log/gunicorn.log 2>/dev/null || echo "Could not read gunicorn log from container"
fi

echo -e "\n=== Supervisord Logs (last 20 lines) ==="
if [ -f "./data/backend/log/supervisord.log" ]; then
    tail -20 ./data/backend/log/supervisord.log
else
    echo "Supervisord log file not found at ./data/backend/log/supervisord.log"
    echo "Trying to read from container..."
    docker compose exec -T oj-backend tail -20 /data/log/supervisord.log 2>/dev/null || echo "Could not read supervisord log from container"
fi

echo -e "\n=== Testing backend connectivity from frontend container ==="
docker compose exec -T oj-frontend curl -s -o /dev/null -w "HTTP Status: %{http_code}, Time: %{time_total}s\n" http://oj-backend:8000/api/profile 2>/dev/null || echo "Could not test connectivity from frontend"

echo -e "\n=== Frontend Nginx Error Logs (last 20 lines) ==="
docker compose exec -T oj-frontend tail -20 /var/log/nginx/error.log 2>/dev/null || echo "Could not read nginx error log"

echo -e "\n=== Frontend Nginx API Error Logs (if exists, last 20 lines) ==="
docker compose exec -T oj-frontend tail -20 /var/log/nginx/api_error.log 2>/dev/null || echo "API error log not found or empty"
