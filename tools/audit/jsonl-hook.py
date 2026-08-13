#!/usr/bin/env python3
"""Write sanitized copyparty hook arguments as one JSON Lines record."""
from __future__ import print_function

import datetime
import json
import os
import re
import sys


SENSITIVE = re.compile(r"(?:pass(?:word)?|pwd|token|secret|authorization|cookie|api[_-]?key)", re.I)
REDACTED = "[REDACTED]"


def scrub(value, key=""):
    if SENSITIVE.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {str(k): scrub(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, str) and re.match(r"^\s*[\w-]*(?:pass(?:word)?|pwd|token|secret|authorization|cookie|api[_-]?key)\s*=", value, re.I):
        return REDACTED
    return value


def parse_arg(value):
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return scrub(value)
    return scrub(parsed)


def append(path, record):
    directory = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(directory):
        os.makedirs(directory, 0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        payload = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        os.write(fd, payload)  # one O_APPEND write: atomic per local POSIX filesystem
    finally:
        os.close(fd)


def main(argv):
    path = os.environ.get("AUDIT_LOG")
    if not path:
        print("AUDIT_LOG is required", file=sys.stderr)
        return 64
    hook = parse_arg(argv[0]) if argv else {}
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "hook": hook,
        "argv": [scrub(arg) for arg in argv[1:]],
    }
    try:
        append(path, record)
    except (IOError, OSError) as exc:
        print("audit append failed: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
