#!/usr/bin/env bash
set -euo pipefail

root="${1:?usage: deploy/smoke_check.sh <target-root> [--airflow]}"
current="$root/current"
expected="$(git rev-parse --short HEAD)"

test "$(cat "$current/DEPLOYED_SHA")" = "$expected" || { echo "current release is not $expected"; exit 1; }
test -f "$current/airflow/dags/saola_daily.py" || { echo "DAG file missing from the release"; exit 1; }
python -m py_compile "$current/airflow/dags/saola_daily.py"
(cd "$current/dbt" && dbt parse --profiles-dir . --target "${DBT_TARGET:-dev}" >/dev/null)
python -m json.tool "$(ls -1t "$root"/deploys/*.json | head -1)" >/dev/null

if [ "${2:-}" = "--airflow" ]; then
  airflow dags reserialize >/dev/null
  if airflow dags list-import-errors -o plain | grep -q saola_daily; then
    echo "Airflow cannot import saola_daily"; exit 1
  fi
  airflow dags list -o plain | grep -q saola_daily
fi
echo "smoke check passed for $expected"
