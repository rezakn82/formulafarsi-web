#!/usr/bin/env sh
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
    python - <<'PY'
import os
import sys
import time

import psycopg

dsn = os.environ["DATABASE_URL"]
if dsn.startswith(("postgres://", "postgresql://")):
    print("Waiting for PostgreSQL...")
    for attempt in range(30):
        try:
            with psycopg.connect(dsn, connect_timeout=2):
                break
        except Exception as exc:
            if attempt == 29:
                print(f"Database unavailable after 30 attempts: {exc}", file=sys.stderr)
                sys.exit(1)
            time.sleep(1)
PY
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-true}" = "true" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
