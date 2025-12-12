#!/bin/sh

APP=/app
DATA=/data
DEBUG_LOG="$DATA/log/debug.log"

# Helper function to write debug logs in NDJSON format
debug_log() {
    local location="$1"
    local message="$2"
    local hypothesis_id="${3:-}"
    local data="${4:-{}}"
    local timestamp=$(date +%s%3N)
    if [ -z "$timestamp" ] || [ "$timestamp" = "%s%3N" ]; then
        timestamp=$(python3 -c "import time; print(int(time.time() * 1000))" 2>/dev/null || echo $(date +%s)000)
    fi
    echo "{\"id\":\"log_${timestamp}_$$\",\"timestamp\":${timestamp},\"location\":\"${location}\",\"message\":\"${message}\",\"data\":${data},\"sessionId\":\"debug-session\",\"runId\":\"run1\",\"hypothesisId\":\"${hypothesis_id}\"}" >> "$DEBUG_LOG" 2>/dev/null || true
}

mkdir -p $DATA/log $DATA/config $DATA/ssl $DATA/test_case $DATA/public/upload $DATA/public/avatar $DATA/public/website
debug_log "entrypoint.sh:7" "Entrypoint started" "A" "{\"step\":\"init\",\"data_dir\":\"$DATA\"}"

if [ ! -f "$DATA/config/secret.key" ]; then
    echo $(cat /dev/urandom | head -1 | md5sum | head -c 32) > "$DATA/config/secret.key"
fi

if [ ! -f "$DATA/public/avatar/default.png" ]; then
    cp data/public/avatar/default.png $DATA/public/avatar
fi

if [ ! -f "$DATA/public/website/favicon.ico" ]; then
    cp data/public/website/favicon.ico $DATA/public/website
fi

SSL="$DATA/ssl"
if [ ! -f "$SSL/server.key" ]; then
    openssl req -x509 -newkey rsa:2048 -keyout "$SSL/server.key" -out "$SSL/server.crt" -days 1000 \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Beijing OnlineJudge Technology Co., Ltd./OU=Service Infrastructure Department/CN=`hostname`" -nodes
fi

random_string() {
    tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32
}

ADMIN_USERNAME=${ADMIN_USERNAME:-root}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-$(random_string)}

cd $APP/deploy/nginx
ln -sf locations.conf https_locations.conf
if [ -z "$FORCE_HTTPS" ]; then
    ln -sf locations.conf http_locations.conf
else
    ln -sf https_redirect.conf http_locations.conf
fi

if [ ! -z "$LOWER_IP_HEADER" ]; then
    sed -i "s/__IP_HEADER__/\$http_$LOWER_IP_HEADER/g" api_proxy.conf;
else
    sed -i "s/__IP_HEADER__/\$remote_addr/g" api_proxy.conf;
fi

if [ -z "$MAX_WORKER_NUM" ]; then
    export CPU_CORE_NUM=$(grep -c ^processor /proc/cpuinfo)
    # FIX: Changed [[ to [ for sh compatibility
    if [ $CPU_CORE_NUM -lt 2 ]; then
        export MAX_WORKER_NUM=2
    else
        export MAX_WORKER_NUM=$(($CPU_CORE_NUM))
    fi
fi

# FIX: Check if dist directory exists before trying to cd into it
if [ -d "$APP/dist" ]; then
    cd $APP/dist
    if [ ! -z "$STATIC_CDN_HOST" ]; then
        find . -name "*.*" -type f -exec sed -i "s/__STATIC_CDN_HOST__/\/$STATIC_CDN_HOST/g" {} \;
    else
        find . -name "*.*" -type f -exec sed -i "s/__STATIC_CDN_HOST__\///g" {} \;
    fi
fi

cd $APP

debug_log "entrypoint.sh:69" "Starting database migration loop" "B" "{\"attempt\":0,\"max_attempts\":5}"
n=0
while [ $n -lt 5 ]
do
    debug_log "entrypoint.sh:72" "Attempting database migration" "B" "{\"attempt\":$n}"
    python manage.py migrate --no-input
    MIGRATE_EXIT=$?
    debug_log "entrypoint.sh:72" "Migration completed" "B" "{\"attempt\":$n,\"exit_code\":$MIGRATE_EXIT}"
    
    if [ $MIGRATE_EXIT -eq 0 ]; then
        debug_log "entrypoint.sh:73" "Creating admin user" "B" "{\"username\":\"$ADMIN_USERNAME\"}"
        python manage.py inituser --username="$ADMIN_USERNAME" --password="$ADMIN_PASSWORD" --action=create_super_admin
        INITUSER_EXIT=$?
        debug_log "entrypoint.sh:73" "Inituser completed" "B" "{\"exit_code\":$INITUSER_EXIT}"
        
        if [ $INITUSER_EXIT -eq 0 ]; then
            debug_log "entrypoint.sh:74" "Setting judge server token" "B" "{}"
            echo "from options.options import SysOptions; SysOptions.judge_server_token='$JUDGE_SERVER_TOKEN'" | python manage.py shell
            TOKEN_EXIT=$?
            debug_log "entrypoint.sh:74" "Token set" "B" "{\"exit_code\":$TOKEN_EXIT}"
            
            if [ $TOKEN_EXIT -eq 0 ]; then
                debug_log "entrypoint.sh:75" "Updating judge server task numbers" "B" "{}"
                echo "from conf.models import JudgeServer; JudgeServer.objects.update(task_number=0)" | python manage.py shell
                UPDATE_EXIT=$?
                debug_log "entrypoint.sh:75" "Update completed" "B" "{\"exit_code\":$UPDATE_EXIT}"
                
                if [ $UPDATE_EXIT -eq 0 ]; then
                    debug_log "entrypoint.sh:76" "All database operations successful" "B" "{\"attempt\":$n}"
                    break
                fi
            fi
        fi
    fi
    n=$(($n+1))
    echo "Failed to migrate, going to retry..."
    debug_log "entrypoint.sh:78" "Database operations failed, retrying" "B" "{\"attempt\":$n,\"sleep_seconds\":8}"
    sleep 8
done

# FIX: Use Debian syntax for user/group creation (not Alpine)
getent group spj >/dev/null || groupadd -g 903 spj
getent passwd server >/dev/null || useradd -u 900 -r -g spj -s /sbin/nologin -d /nonexistent -c "OJ server user" server

# FIX: Only chown dist if it exists, and create it if it doesn't
mkdir -p $APP/dist
chown -R server:spj $DATA
if [ -d "$APP/dist" ]; then
    chown -R server:spj $APP/dist
fi
find $DATA/test_case -type d -exec chmod 710 {} \;
find $DATA/test_case -type f -exec chmod 640 {} \;

# Check if port 8000 is already in use
debug_log "entrypoint.sh:94" "Checking port 8000 availability" "C" "{}"
if command -v netstat >/dev/null 2>&1; then
    PORT_CHECK=$(netstat -tuln | grep :8000 || true)
    debug_log "entrypoint.sh:94" "Port 8000 check result" "C" "{\"netstat_output\":\"$PORT_CHECK\"}"
elif command -v ss >/dev/null 2>&1; then
    PORT_CHECK=$(ss -tuln | grep :8000 || true)
    debug_log "entrypoint.sh:94" "Port 8000 check result" "C" "{\"ss_output\":\"$PORT_CHECK\"}"
fi

# Check database connectivity
debug_log "entrypoint.sh:94" "Testing database connectivity" "B" "{\"host\":\"${POSTGRES_HOST:-oj-postgres}\",\"db\":\"${POSTGRES_DB:-onlinejudge}\"}"
python3 -c "import psycopg2; conn = psycopg2.connect(host='${POSTGRES_HOST:-oj-postgres}', port='${POSTGRES_PORT:-5432}', dbname='${POSTGRES_DB:-onlinejudge}', user='${POSTGRES_USER:-onlinejudge}', password='${POSTGRES_PASSWORD}'); conn.close()" 2>&1
DB_CONN_EXIT=$?
debug_log "entrypoint.sh:94" "Database connectivity test" "B" "{\"exit_code\":$DB_CONN_EXIT}"

# Check Redis connectivity
debug_log "entrypoint.sh:94" "Testing Redis connectivity" "B" "{\"host\":\"${REDIS_HOST:-oj-redis}\",\"port\":\"${REDIS_PORT:-6379}\"}"
python3 -c "import redis; r = redis.Redis(host='${REDIS_HOST:-oj-redis}', port=${REDIS_PORT:-6379}, password='${REDIS_PASSWORD}', decode_responses=False); r.ping()" 2>&1
REDIS_CONN_EXIT=$?
debug_log "entrypoint.sh:94" "Redis connectivity test" "B" "{\"exit_code\":$REDIS_CONN_EXIT}"

debug_log "entrypoint.sh:94" "Starting supervisord" "A" "{\"config\":\"/app/deploy/supervisord.conf\",\"max_workers\":\"${MAX_WORKER_NUM:-2}\"}"
exec supervisord -c /app/deploy/supervisord.conf
