#!/bin/bash
# Database migration script

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Extract connection details from DATABASE_DSN
# Format: postgresql://user:pass@host:port/dbname
DB_URL=${DATABASE_DSN:-"postgresql://postgres:postgres@localhost:5432/officialdir"}

echo "Running migrations..."
echo "Database: $DB_URL"

# Run migration SQL file
psql "$DB_URL" -f backend/app/db/migrations/0001_create_schema.sql

echo "Migration completed successfully!"
