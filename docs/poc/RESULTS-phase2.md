# Phase 2 POC results

Date: 2026-08-12 UTC. Official single-file `copyparty 1.20.20` (packed 2026-08-03), Python 3.12.3. All tests used synthetic files under this directory; no remote service, `safefilehub-clean`, real data, or system dependencies.

## 1. Move/rename HTTP contract — VALIDATED

Source evidence: `devnotes.md` says `POST ?move=/foo/bar`, and extracted `httpcli.py` calls `self.uparam.get("move")`, requiring a destination vpath. The destination must be in the query string; an empty form body is correct.

Exact commands:
```sh
python3 copyparty-sfx.py -i 127.0.0.1 -p 43827 --xau 'j,./hooks/event.sh' --xar 'j,./hooks/event.sh' --xad 'j,./hooks/event.sh' --xbr 'j,./hooks/event.sh' --xbd 'j,./hooks/event.sh' -a alice:alicepw -v "$PWD/data/public:/public:A,alice" > logs/server.log 2>&1 & echo $! > server.pid
curl -sS -u alice:alicepw -T payload.txt http://127.0.0.1:43827/public/rename-source.txt
curl -sS -u alice:alicepw -X POST -d '' -D results/rename.headers 'http://127.0.0.1:43827/public/rename-source.txt?move=/public/renamed-target.txt' -o results/rename.body
find data/public -maxdepth 1 -type f -printf '%f\n' | sort
```

Observed: upload succeeded; rename response `HTTP/1.1 201 Created`; filesystem contained `renamed-target.txt` and no source. Earlier `POST` without the destination contract returned 500 and is not the API. Hook log records `xbr` then `xar.mv` with `ap_to`/`ap_from`.

## 2. up2k interrupted/resumed upload — VALIDATED

Protocol was actual HTTP, not filesystem assembly. `devnotes.md` and extracted browser `web/up2k.js.gz` were used: JSON handshake `POST` followed by binary `POST` with `X-Up2k-Hash`, `X-Up2k-Wark`, `Content-Length`; browser sends comma-separated chunk hashes and receives missing hashes on repeated handshake.

Exact test driver command:
```sh
python3 <inline driver from shell history>  # generated results/up2k-test.bin (3,145,851 bytes), SHA-256 0d171044af309faeabc2c99f5b3f1b0f95f3888e8a419d9f346d4aef1d0e4285
```

Recorded artifacts: `results/up2k-handshake1.out`, `up2k-chunk0.out`, `up2k-handshake2.out`, `up2k-chunk1.out`..`up2k-chunk3.out`, `up2k-final.out`.

Exact observed outputs: first handshake returned wark `Y5eOw9hOSU97vBuijb19nxYaeEOMrAIoCZZmoNkRC-Vv` and 4 missing hashes; first chunk returned `thank`; second identical handshake returned exactly 3 remaining hashes; three remaining chunk requests each returned `thank`; final handshake returned `"hash": []`; filesystem SHA-256 matched source exactly. This proves same-file continuation after a deliberate interruption between chunk 0 and remaining chunks. It does not prove browser UI persistence across browser restart.

## 3. Hooks / audit coverage — PARTIAL (mechanism VALIDATED)

Configured `--xau`, `--xar`, `--xad`, `--xbr`, `--xbd` as `j,./hooks/event.sh`; event script appends timestamp and JSON argv to `results/hook-events.log`. Exact command is in section 1. Observed events include `xau.http.dump` (simple upload), `xau.up2k` plus wark (resumable upload), `xbr` + `xar.mv` (rename), and `xbd` + `xad` (delete). Therefore hooks can support upload/download/delete/rename *event hooks* where supported; this test did not configure a download hook because `--help-hooks` exposes no download event. Hook payload has useful user/path/ip/host/size/wark fields, but production audit needs a durable, failure-handled collector and explicit download access logging (server request logs or reverse proxy).

## 4. TLS / reverse-proxy feasibility — VALIDATED for local TLS, proxy PARTIAL

No system service was changed. Exact commands:
```sh
openssl req -x509 -newkey rsa:2048 -nodes -keyout tls/key.pem -out tls/cert.pem -days 1 -subj '/CN=127.0.0.1' -addext 'subjectAltName=IP:127.0.0.1'
python3 copyparty-sfx.py -i 127.0.0.1 -p 43828 --https-only --cert tls/cert.pem --certkey tls/key.pem -a alice:alicepw -v "$PWD/data/public:/public:A,alice" > results/tls-server.log 2>&1 &
curl -k -sS -u alice:alicepw -D results/tls.headers https://127.0.0.1:43828/public/ -o results/tls.body
```

Observed `HTTP/1.1 200 OK`; TLS certificate/key worked. A separately managed reverse proxy was not installed or tested; copyparty has `--xf-proto`, `--xf-host`, `--rp-loc` options and upstream nginx guidance, so proxy is feasible but remains unvalidated here.

## 5. Controlled concurrency / large file — PARTIAL

Created two synthetic 100 MiB sparse-backed files. Exact command:
```sh
/usr/bin/time -f 'elapsed=%e rc=%x' curl -sS -u alice:alicepw -T results/large-a.bin -o /dev/null http://127.0.0.1:43827/public/large-a.bin &
/usr/bin/time -f 'elapsed=%e rc=%x' curl -sS -u alice:alicepw -T results/large-b.bin -o /dev/null http://127.0.0.1:43827/public/large-b.bin &
wait
sha256sum results/large-a.bin data/public/large-a.bin
sha256sum results/large-b.bin data/public/large-b.bin
```

`large-a.bin` completed and SHA-256 matched (`0e91fe944cdb91164411eee0b74a2e9e0394b55af6c877c2a1c506cc80f12ec8`); `large-b` request was not completed because the test server exited during the controlled run, so no concurrency success claim is made. This is intentionally recorded as partial rather than hiding the failed run. No uncontrolled traffic was generated.

## Final verdict: PARTIAL

Validated: official version/runtime, correct move contract, up2k same-file chunk continuation and final hash, upload/rename/delete hooks, local HTTPS, one 100 MiB upload with checksum.

Unvalidated/partial: browser-driven interruption/restart UI, download-specific audit hook, reverse-proxy integration, successful simultaneous two-upload run, production auth/permission/security review.

Production recommendation: do not approve yet. Keep copyparty isolated; require a hardened reverse proxy/TLS deployment, durable structured audit pipeline (including download access logs), browser-level resume test, repeatable successful concurrency/load test, resource/rate limits, account/volume review, and security review before production use.
