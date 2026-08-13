#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-43827}"; USERNAME="${USERNAME:-alice}"; PASSWORD="${PASSWORD:-}"; BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"
DATA_DIR="${DATA_DIR:-$PWD/data}"; LOG_DIR="${LOG_DIR:-$PWD/logs}"; RESULTS_DIR="${RESULTS_DIR:-$PWD/results}"
: "${PASSWORD:?Set PASSWORD (do not put credentials in this script)}"
mkdir -p "$DATA_DIR/public" "$DATA_DIR/priv" "$LOG_DIR" "$RESULTS_DIR"
exec python3 copyparty-sfx.py -i "${BIND:-127.0.0.1}" -p "$PORT" -e2d \
  -a "${USERNAME}:${PASSWORD}" \
  -v "$DATA_DIR/public:/public:A,${USERNAME}" \
  -v "$DATA_DIR/priv:/priv:A,${USERNAME}" \
  >"$LOG_DIR/server.log" 2>&1
