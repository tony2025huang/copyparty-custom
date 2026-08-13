# Copyparty Phase 2 repeatable test plan

## Scope and safety

Local synthetic-data POC only. Do not point `DATA_DIR` at production, `safefilehub-clean`, a mounted business directory, or a remote URL. The scripts use Python stdlib and the already-present official SFX; they do not install packages or modify system services.

## Prerequisites

- Linux/macOS shell with Bash, Python 3.12+ (stdlib only), `curl` optional for manual checks.
- `copyparty-sfx.py` in this directory, version `1.20.20`, packed 2026-08-03.
- An unused loopback port and writable POC directory.
- Credentials supplied through environment/arguments; no credentials are stored in scripts.

## Start

```sh
cd /root/.openclaw/workspace/.tmp/openclaw-spikes/copyparty
export PASSWORD='choose-a-local-test-password'
export USERNAME='alice' PORT=43827
./run-phase2.sh
```

The server runs in the foreground. In a second terminal, set the same `PORT`, then run the test:

```sh
cd /root/.openclaw/workspace/.tmp/openclaw-spikes/copyparty
python3 test-phase2.py --base-url "http://127.0.0.1:${PORT:-43827}" --user "${USERNAME:-alice}" --password "$PASSWORD" --data-dir "$PWD/data" --results-dir "$PWD/results"
```

Expected final output includes:

```text
PASS PUT=201 MOVE=201 RANGE=206 UP2K_RESUME=PASS FINAL_SHA256=PASS
```

The test covers PUT upload, full GET and byte-range GET, documented `POST ?move=/destination`, and an actual up2k handshake → first chunk → deliberate interruption → repeated handshake → remaining chunks → final empty missing list. Default synthetic file size is approximately 4 MiB; use `--size-mib 100` for a controlled larger test.

## Optional exact manual checks

```sh
curl -u "$USERNAME:$PASSWORD" -T payload.txt "$BASE_URL/public/manual.txt" -D results/manual-put.headers
curl -u "$USERNAME:$PASSWORD" -H 'Range: bytes=0-9' "$BASE_URL/public/manual.txt" -D results/manual-range.headers -o results/manual-range.out
curl -u "$USERNAME:$PASSWORD" -X POST -d '' "$BASE_URL/public/manual.txt?move=/public/manual-renamed.txt" -D results/manual-move.headers
```

Expected statuses: upload `201` (some versions may return `200`), range `206`, move `201`. Any other status is a failure unless explicitly explained in the result log.

## TLS check (separate local process)

Generate only temporary POC files and use a separate port:

```sh
openssl req -x509 -newkey rsa:2048 -nodes -keyout tls/key.pem -out tls/cert.pem -days 1 -subj '/CN=127.0.0.1' -addext 'subjectAltName=IP:127.0.0.1'
python3 copyparty-sfx.py -i 127.0.0.1 -p 43828 --https-only --cert tls/cert.pem --certkey tls/key.pem -a "$USERNAME:$PASSWORD" -v "$PWD/data/public:/public:A,$USERNAME" > results/tls-server.log 2>&1 & echo $! > results/tls.pid
curl -k -u "$USERNAME:$PASSWORD" -D results/tls.headers https://127.0.0.1:43828/public/ -o results/tls.body
```

Expected status: `200`. Stop the process with `kill "$(cat results/tls.pid)"` after checking it. This validates local TLS only, not a reverse proxy.

## Hooks

`hooks/audit-hook.sh` is a safe append-only synthetic test collector. Start copyparty with `--xau 'j,./hooks/audit-hook.sh' --xar 'j,./hooks/audit-hook.sh' --xbr 'j,./hooks/audit-hook.sh' --xad 'j,./hooks/audit-hook.sh' --xbd 'j,./hooks/audit-hook.sh'`, then inspect `results/hook-events.log`. Expected event types include upload (`xau`), rename (`xbr`/`xar`), and delete (`xbd`/`xad`). There is no dedicated download hook in `--help-hooks`; use server/reverse-proxy access logs for download auditing.

## Cleanup

After confirming test results, stop only POC processes and remove only synthetic artifacts if desired:

```sh
kill "$(cat server.pid)" 2>/dev/null || true
kill "$(cat results/tls.pid)" 2>/dev/null || true
# Review first; this is intentionally not automatic:
# mv data results tls to a recoverable quarantine location, or delete manually.
```

## Failure判定 and risks

- Any assertion failure, non-expected HTTP status, missing resumed chunks, or SHA-256 mismatch is FAIL.
- A server crash during concurrency is FAIL/PARTIAL, not success.
- Keep ports loopback-only. Do not expose test credentials or use `-i 0.0.0.0`.
- The test creates files in `DATA_DIR`, may create `.hist`, and can consume disk proportional to `--size-mib`.
- Do not run multiple large tests without checking free disk and process state.
- A self-signed TLS certificate is not production trust configuration.
- Hooks run local commands; production hooks must be sandboxed, durable, monitored, and protected against argument/log injection.
