# copyparty POC

Date: 2026-08-12 UTC
Scope: isolated local POC only. No `safefilehub-clean`, remote service, or real business data touched. All created artifacts are under this directory; runtime data is `data/`.

## Question
Can current copyparty provide a low-friction local file hub with Unicode-safe paths, resumable/range-capable transfer, archive downloads, per-user volume isolation, file management, and observable logs without system dependencies?

## Upstream facts (GitHub official repository)
- Source: https://github.com/9001/copyparty ; fetched `README.md`, `docs/devnotes.md`, `LICENSE`; latest GitHub release API reported `v1.20.20` (`more wopi`), released 2026-08-03.
- License: MIT (LICENSE copyright 2019 ed <oss@ocv.me>).
- Install: official single-file `copyparty-sfx.py` from latest release; README also documents `python3 -m pip install --user -U copyparty` and zipapp. SFX says server only needs Python; optional dependencies are not required for basic HTTP.
- Resumability: README says browser `up2k` uploads chunk/checksums and autoresumes network/browser/PC interruptions; client re-upload of same files avoids existing data. This was not fully browser-automated here. HTTP Range download was directly validated below.
- Volumes: `-v SRC:DST:permissions`; permissions include `r` read/list/download, `w` upload, `m` move, `d` delete, `g` download without listing, `A` all. `-a USER:PASS` accounts. Config files are recommended for complex setups.
- Archives: `?zip`, `?tar`, plus gzip/xz/pax variants; hidden files are excluded unless visible to account.
- Hooks: event hooks can run before/after upload, move/rename, and delete (`--help-hooks`; README `## event hooks`); `--xau` supports ZeroMQ event messages. Logging is sent to stdout by default (README feature list); captured to `logs/server.log` here.
- HTTP API from official `docs/devnotes.md`: PUT binary upload; multipart `act=mkdir`; POST `?move=/...`; POST `?delete`; GET `?zip`/`?tar`; Basic auth is supported.

## Exact local setup/run
```sh
cd /root/.openclaw/workspace/.tmp/openclaw-spikes/copyparty
mkdir -p data/priv data/public logs
python3 copyparty-sfx.py -i 127.0.0.1 -p 43827 \
  -a alice:alicepw -a bob:bobpw \
  -v "$PWD/data/public:/public:A,alice" \
  -v "$PWD/data/priv:/priv:A,alice" \
  -v "$PWD/data:/root:r,bob" > logs/server.log 2>&1 &
```
Port `43827` was a random high local port. Python 3.12.3; no packages/system dependencies installed. SFX version printed `copyparty 1.20.20`.

## Results (exact observed status/results)
- Startup: `HTTP/1.1 403` anonymous `/root/`; authenticated alice `/public/` returned `200`.
- Unicode/path upload: `curl -u alice:alicepw -T payload.txt http://127.0.0.1:43827/public/<URL-encoded Chinese folder>/emoji%20%F0%9F%98%80%20%25.txt` -> `201`. Filesystem retained `public/测试 folder/emoji 😀 %.txt`.
- Download: `200`, 30 bytes; SHA-256 matched source `34b696d03cecbe5ea2a073f0fd0540ab20b17f54e1a752d5c31f55002ab9a35c`.
- Range: `curl -H 'Range: bytes=0-9' ...` -> `HTTP/1.1 206 Partial Content`, exactly 10 bytes.
- Archive: folder `?zip` -> `200`, `application/zip`, 236 bytes; `file`: Zip archive. `?tar` -> `200`, `application/x-tar`, 10240 bytes; `file`: POSIX tar archive (GNU tar).
- Isolation: bob `/public/` -> `403`; bob `/priv/` -> `403`; anonymous missing path -> `403`; authenticated missing path -> `404`.
- Directory management: multipart `act=mkdir`, `name=临时 空格 😀 %` -> `201`; delete via `POST .../?delete` -> `200`, directory removed.
- Upload/delete: simple PUT `public/test.txt` -> `201`; DELETE was attempted with `DELETE` and returned `200` (server supports it in this run); official API docs specify POST `?delete`. Official move API `POST ?move=/public/renamed.txt` returned `500` in this minimal request, so rename is not claimed validated; browser/API payload details need follow-up.
- Logs: stdout captured in `logs/server.log`; contained listening line, volume initialization, worker status, optional dependency warnings, and request/event activity. TLS warning noted because cfssl was not installed; HTTP-only local test was intentional.

## Repeatable Phase 2 tests

- `run-phase2.sh`: parameterized local server launcher. Set `PASSWORD`, optionally `USERNAME`, `PORT`, `DATA_DIR`, `LOG_DIR`, `RESULTS_DIR`; it does not contain credentials.
- `test-phase2.py`: Python stdlib-only HTTP test covering PUT/GET/Range, documented move, and actual interrupted up2k continuation with final SHA-256 verification. Use `--base-url`, `--user`, `--password`, `--data-dir`, `--results-dir`, and optional `--size-mib`.
- `hooks/audit-hook.sh`: append-only synthetic hook collector.
- `TEST_PLAN.md`: prerequisites, start/run/cleanup, expected status codes, failure criteria, risks, and TLS/hooks procedures.

## Phase 2 update

See `RESULTS-phase2.md` for exact commands, raw result artifacts, and limitations. Phase 2 validated the correct rename contract (`POST` with `?move=/destination`), actual up2k chunk continuation with final SHA-256 verification, upload/rename/delete hooks, and local HTTPS. A download-specific hook is not exposed by `--help-hooks`; reverse-proxy integration and successful simultaneous large uploads remain partial.

## Verdict: PARTIAL

Question: feasible as an isolated Python-only local file hub with transfer, archives, Unicode paths, and volume isolation?

Evidence: single-file official release ran on Python 3.12.3; PUT/GET/Range/archive/auth/permissions/mkdir/delete all produced the statuses above.

What worked: installation friction, local HTTP service, Unicode + spaces + emoji + `%` names, upload/download, byte-range response, ZIP/TAR streaming, per-volume/per-user denial, mkdir/delete, stdout logs.

What failed or remains unvalidated: browser UI interruption/restart was not exercised (HTTP up2k continuation was validated); the first incorrect rename request lacked the required destination query parameter, while the documented contract was then validated; hooks, local HTTPS, and a 100 MiB checksum test were exercised; successful simultaneous large uploads and reverse-proxy integration remain unvalidated.

Recommendation: use only as a promising local POC, not production-approved yet. Before production, complete browser-level resume/restart testing, successful controlled concurrency, reverse-proxy validation, and a durable audit design covering downloads (hooks expose upload/move/delete but no download event). Keep all testing on synthetic data and an isolated host.
