#!/bin/sh
# Bring the database up to date, then replace this shell with the server, so
# the server receives the container's stop signal.
set -eu

alembic upgrade head
# One worker: SQLite allows a single writer at a time.
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
