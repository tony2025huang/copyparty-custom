#!/bin/sh
# Stdlib-only copyparty event-hook wrapper.  Example: xau: f,j,c1,/path/jsonl-hook.sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$base/jsonl-hook.py" "$@"
