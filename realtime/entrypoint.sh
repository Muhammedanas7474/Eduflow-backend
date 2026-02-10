#!/bin/bash
set -e

# Wait for DB if needed (optional, but good practice if we had netcat or similar)
# For now just run migrate

echo "Applying database migrations..."
python manage.py migrate

echo "Starting server..."
exec "$@"
