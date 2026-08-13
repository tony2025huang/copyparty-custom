#!/bin/sh
set -eu
out="${COPYPARTY_HOOK_LOG:-./results/hook-events.log}"
mkdir -p "$(dirname "$out")"
printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$out"
