#!/bin/sh
set -eu
cd "$(dirname "$0")"
PORT="${PORT:-43827}"
mkdir -p data/public data/priv logs
exec python3 copyparty-sfx.py -i 127.0.0.1 -p "$PORT" \
  -a alice:alicepw -a bob:bobpw \
  -v "$PWD/data/public:/public:A,alice" \
  -v "$PWD/data/priv:/priv:A,alice" \
  -v "$PWD/data:/root:r,bob"
