#!/bin/sh
# Enhanced healthcheck script with logging

DATA=/data
DEBUG_LOG="$DATA/log/debug.log"

# Helper function to write debug logs
debug_log() {
    local location="$1"
    local message="$2"
    local hypothesis_id="${3:-}"
    local data="${4:-{}}"
    local timestamp=$(python3 -c "import time; print(int(time.time() * 1000))" 2>/dev/null || date +%s000)
    echo "{\"id\":\"log_${timestamp}_$$\",\"timestamp\":${timestamp},\"location\":\"${location}\",\"message\":\"${message}\",\"data\":${data},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"${hypothesis_id}\"}" >> "$DEBUG_LOG" 2>/dev/null || true
}

# #region agent log
debug_log "healthcheck.sh:15" "Healthcheck started" "C" "{}"
# #endregion

# Check if port 8000 is listening
# #region agent log
debug_log "healthcheck.sh:18" "Testing port 8000 connection" "C" "{}"
# #endregion
python3 -c 'import socket; s=socket.socket(); s.settimeout(2); result = s.connect_ex(("localhost", 8000)); s.close(); exit(result)' 2>&1
PORT_EXIT=$?

# #region agent log
debug_log "healthcheck.sh:18" "Port 8000 connection test result" "C" "{\"exit_code\":$PORT_EXIT}"
# #endregion

# Check if gunicorn process is running
# #region agent log
debug_log "healthcheck.sh:24" "Checking gunicorn process" "A" "{}"
# #endregion
GUNICORN_PID=$(pgrep -f "gunicorn.*oj.wsgi" || echo "")
GUNICORN_COUNT=$(echo "$GUNICORN_PID" | grep -c . || echo "0")

# #region agent log
debug_log "healthcheck.sh:24" "Gunicorn process check" "A" "{\"pid\":\"$GUNICORN_PID\",\"count\":$GUNICORN_COUNT}"
# #endregion

# Check if supervisord is running
# #region agent log
debug_log "healthcheck.sh:30" "Checking supervisord process" "A" "{}"
# #endregion
SUPERVISORD_PID=$(pgrep -f "supervisord" || echo "")

# #region agent log
debug_log "healthcheck.sh:30" "Supervisord process check" "A" "{\"pid\":\"$SUPERVISORD_PID\"}"
# #endregion

# Check supervisorctl status
if [ -n "$SUPERVISORD_PID" ]; then
    # #region agent log
    debug_log "healthcheck.sh:36" "Checking supervisorctl status" "A" "{}"
    # #endregion
    SUPERVISOR_STATUS=$(supervisorctl -c /app/deploy/supervisord.conf status 2>&1 || echo "supervisorctl_failed")
    # #region agent log
    debug_log "healthcheck.sh:36" "Supervisorctl status" "A" "{\"status\":\"$SUPERVISOR_STATUS\"}"
    # #endregion
fi

# Exit with port check result (0 = healthy, 1 = unhealthy)
if [ $PORT_EXIT -eq 0 ]; then
    # #region agent log
    debug_log "healthcheck.sh:44" "Healthcheck passed" "C" "{\"port_8000\":\"listening\"}"
    # #endregion
    exit 0
else
    # #region agent log
    debug_log "healthcheck.sh:44" "Healthcheck failed" "C" "{\"port_8000\":\"not_listening\",\"gunicorn_count\":$GUNICORN_COUNT}"
    # #endregion
    exit 1
fi
