#!/bin/bash
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

groupmod -o -g "$PGID" monitor
usermod -o -u "$PUID" monitor

chown -R monitor:monitor /app/data /app/logs

exec gosu monitor "$@"
