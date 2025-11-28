# Development Workflow with Docker Compose

## Quick Reference

### Option 1: Rebuild After Changes (Current Setup)

After making code changes, rebuild and restart:

```bash
# Rebuild and restart just the backend
docker-compose build --no-cache oj-backend
docker-compose up -d oj-backend

# Or use the helper script
./rebuild.sh oj-backend

# Rebuild and restart all services
docker-compose build --no-cache
docker-compose up -d

# Or use the helper script
./rebuild.sh
```

**When to use this:**
- Production deployments
- When you want to test the exact production build
- When frontend changes are involved (requires rebuild)

### Option 2: Development Mode with Volume Mounts (Faster Iteration)

For faster development, you can mount your source code as volumes. This allows you to make changes without rebuilding, but you'll need to restart the service for changes to take effect.

**Note:** This approach has limitations:
- Frontend assets (`/app/dist`) won't be available if you mount the entire backend
- You may need to rebuild frontend separately if making frontend changes

To enable development mode, uncomment line 33 in `docker-compose.yml`:
```yaml
- ./backend:/app
```

Then restart:
```bash
docker-compose up -d oj-backend
```

**After making backend code changes:**
```bash
# Restart the service (no rebuild needed)
docker-compose restart oj-backend

# Or exec into the container and restart gunicorn
docker-compose exec oj-backend supervisorctl restart gunicorn
```

## Common Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f oj-backend
```

### Rebuild specific service
```bash
docker-compose build --no-cache oj-backend
docker-compose up -d oj-backend
```

### Stop all services
```bash
docker-compose down
```

### Start all services
```bash
docker-compose up -d
```

### Check service status
```bash
docker-compose ps
```

## Tips

1. **Backend Python changes**: After rebuilding, changes take effect immediately
2. **Frontend changes**: Always require a rebuild (frontend is built during Docker build)
3. **Database migrations**: Run automatically on container start via entrypoint.sh
4. **Judge server changes**: Rebuild with `docker-compose build --no-cache oj-judge-server`






