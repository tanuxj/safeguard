#!/bin/sh

echo "Waiting for database..."

sleep 5

echo "Running migrations..."

uv run aerich upgrade

echo "Starting FastAPI..."

uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload