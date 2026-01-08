#!/bin/bash
# Run Alembic migrations
set -e

echo "🔄 Running database migrations..."
cd /app
alembic upgrade head
echo "✅ Migrations completed successfully!"
