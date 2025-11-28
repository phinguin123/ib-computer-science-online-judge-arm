#!/bin/sh
set -ex

rm -rf /judger/*
mkdir -p /judger/run /judger/spj /log

chown compiler:code /judger/run
chmod 711 /judger/run

chown compiler:spj /judger/spj
chmod 710 /judger/spj

CPU_CORE_NUM="$(nproc)"
if [ "$CPU_CORE_NUM" -lt 2 ]; then
    export WORKER_NUM=2;
else
    export WORKER_NUM="$CPU_CORE_NUM";
fi

# Start heartbeat process in background if not disabled
if [ -z "$DISABLE_HEARTBEAT" ]; then
    .venv/bin/python3 heartbeat.py &
    HEARTBEAT_PID=$!
    echo "Heartbeat process started with PID $HEARTBEAT_PID"
fi

exec .venv/bin/gunicorn server:app --workers $WORKER_NUM --threads 4 --error-logfile /log/gunicorn.log --bind 0.0.0.0:8080
