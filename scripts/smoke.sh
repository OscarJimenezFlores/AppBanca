#!/usr/bin/env bash
# Humo del API. Sin API_BASE_URL no hay entorno remoto configurado:
# en development el paso avisa y termina; en staging y production falla.
set -euo pipefail

target="${TARGET:-development}"
base="${API_BASE_URL:-}"

if [[ -z "$base" ]]; then
  if [[ "$target" == "development" ]]; then
    echo "development no tiene API_BASE_URL. El humo remoto se omite."
    echo "En local: docker compose up --build y luego curl http://127.0.0.1:8080/health"
    exit 0
  fi
  echo "Falta el secreto API_BASE_URL en el entorno ${target}." >&2
  exit 1
fi

base="${base%/}"
echo "Probando ${base} (${target})"
health="$(curl --fail --silent --show-error --max-time 20 "${base}/health")"
echo "$health"
HEALTH="$health" python3 -c 'import json,os; body=json.loads(os.environ["HEALTH"]);
assert body.get("status")=="ok" and body.get("service")=="andesbank-api", body'
curl --fail --silent --show-error --max-time 20 "${base}/ready" >/dev/null
echo "ready"
