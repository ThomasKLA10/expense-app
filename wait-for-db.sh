#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=postgres psql -h db -U postgres -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
eval $cmd