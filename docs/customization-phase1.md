# Copyparty customization — phase 1

This directory contains deployment-side guardrails only. It does **not** alter
`copyparty/*.py`, replace the upstream security model, deploy a service, or
make a configuration safe without an operator review.

## 1. Check a configuration

Run the static checker before deploying a config change:

```sh
python3 tools/security/check-config.py --config /etc/copyparty/copyparty.conf \
  --root /srv/copyparty --arg=-i=127.0.0.1
```

It exits `2` if it finds a critical issue, otherwise `0`. It reports common
risks: public listeners, anonymous write or `A` access, broad `A` access,
volume-path overlap, paths escaping `--root`, missing `assert_root`, and
writable volumes without any `maxb`, `maxn`, `vmaxb`, or `vmaxn` limit.

The parser deliberately supports the normal simple copyparty config layout;
it is conservative and does not resolve every config include, environment
variable, symlink race, CLI override, firewall, proxy, or copyparty-version
semantic. Supply effective command-line options with repeatable `--arg` values
when they can override the configuration, then review the final effective
command and configuration manually.
`assert_root` protects against a missing volume root at startup; it does not
make arbitrary paths safe.

## 2. Reverse proxy

Start from `contrib/nginx/copyparty-custom.conf.example`. Replace every
placeholder, especially `server_name`, TLS paths, upstream, and
`client_max_body_size`. Keep copyparty bound to loopback or a Unix socket; do
not expose its listener directly when nginx is intended to be the edge.

The template emits one JSON object per Nginx access-log line and disables
request/response buffering with long upload timeouts. Nginx must only trust
client-address forwarding headers from known proxy/CDN source ranges. Never
accept user-supplied `Forwarded` or `X-Forwarded-*` values as authoritative.

**Download auditing depends on Nginx:** retain/protect the Nginx JSON access
log (or replace it with an equivalent edge logger). The hook below only logs
hook invocations; it cannot establish that every download completed.

## 3. Hook JSONL audit log

Configure an event hook with its JSON argument enabled, for example an upload
after-hook in a volume config:

```yaml
flags:
  xau: f,j,c1,/absolute/path/to/tools/audit/jsonl-hook.sh
```

Set `AUDIT_LOG` in the service environment to an absolute log path, then make
that directory owned by the service account and unreadable by untrusted users:

```sh
install -d -m 0700 -o copyparty -g copyparty /var/log/copyparty
# systemd Environment=AUDIT_LOG=/var/log/copyparty/events.jsonl
```

`jsonl-hook.sh` runs its stdlib-only Python wrapper, safely encodes hook JSON
and remaining argv into one JSONL record, and redacts fields/arguments named
like passwords, tokens, cookies, authorization, secrets, or API keys. It
creates/appends the log as mode `0600`; one `O_APPEND` write is atomic on a
local POSIX filesystem. Use normal rotation that preserves restrictive
ownership/mode. Network filesystems and multiple independent writers can have
different atomicity guarantees.

Do not put credentials in hook arguments or configuration anyway: redaction is
best effort and cannot protect secrets copied into unrelated field names or
file paths. The hook returns nonzero if `AUDIT_LOG` is missing or the append
fails; decide whether the selected copyparty hook flags should make that
failure block the user operation.

## Verification

```sh
python3 -m unittest tests.test_custom_tools -v
python3 -m py_compile tools/security/check-config.py tools/audit/jsonl-hook.py
sh -n tools/audit/jsonl-hook.sh
```
