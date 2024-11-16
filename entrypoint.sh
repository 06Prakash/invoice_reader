#!/bin/bash
# entrypoint.sh

set -e

# Wait for the database to be ready
host="$1"
shift
cmd="$@"

export PGPASSWORD=$POSTGRES_PASSWORD

>&2 echo "Waiting for PostgreSQL to be ready..."
until psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - initializing the database"

# Debugging: print the current working directory and list files
>&2 echo "Current working directory: $(pwd)"
>&2 echo "Listing files in current working directory:"
ls -al

cd /app

# Debugging: print the current working directory and list files after changing directory
>&2 echo "Current working directory after cd: $(pwd)"
>&2 echo "Listing files in /app directory:"
ls -al

python init_db.py

>&2 echo "Database initialized - starting the app"
exec $cmd
