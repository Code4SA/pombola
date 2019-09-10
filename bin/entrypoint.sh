#!/bin/sh

mkdir -p ${POMBOLA_DATADIR}/media_root
set -x

postgres_ready() {
python << END
import sys
import psycopg2
try:
    psycopg2.connect("$DATABASE_URL")
except psycopg2.OperationalError as e:
    print(e)
    sys.exit(-1)
sys.exit(0)
END
}
until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'

exec "$@"
