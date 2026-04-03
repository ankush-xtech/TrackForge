#!/bin/bash
# Initialize the database with Alembic migrations
# Run this after docker-compose up

set -e

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Running Alembic migrations..."
cd /app/backend
alembic upgrade head

echo "Database initialized successfully!"
