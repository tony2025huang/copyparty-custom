#!/usr/bin/env python3
"""Conservative static checks for a copyparty configuration file.

This is intentionally a guardrail, not a replacement for reviewing the
copyparty version-specific help text or the surrounding reverse proxy/firewall.
"""
from __future__ import print_function

import argparse
import os
import re
import sys


SEVERE = "CRITICAL"
WARN = "WARNING"
SECRET = re.compile(r"\s+#.*$")


def clean(line):
    return SECRET.sub("", line).strip()


def parse(path):
    sections = []
    current = None
    mode = None
    with open(path, "r") as f:
        for number, raw in enumerate(f, 1):
            line = clean(raw)
            if not line:
                continue
            match = re.match(r"^\[([^]]+)\]$", line)
            if match:
                current = {"name": match.group(1), "line": number, "path": None,
                           "accs": {}, "flags": set(), "global": {}}
                sections.append(current)
                mode = None
                continue
            if not current:
                continue
            if current["name"] in ("accounts", "groups"):
                continue
            if line == "accs:":
                mode = "accs"
                continue
            if line == "flags:":
                mode = "flags"
                continue
            match = re.match(r"^([\w-]+)\s*:\s*(.*)$", line)
            if match:
                key, value = match.groups()
                if mode == "accs":
                    current["accs"][key] = value
                elif mode == "flags":
                    current["flags"].add(key)
                elif current["name"] == "global":
                    current["global"][key] = value
                continue
            if current["name"] == "global":
                current["global"][line.split()[0]] = True
            elif mode == "flags":
                current["flags"].add(line.split()[0].split(":", 1)[0])
            elif current["name"] != "global" and current["path"] is None:
                current["path"] = os.path.expandvars(os.path.expanduser(line))
    return sections


def report(findings, severity, message, line=None):
    findings.append((severity, message, line))


def public_listener(value):
    vals = [x.strip().lower() for x in value.split(",")]
    return any(x in ("0.0.0.0", "::", "[::]") for x in vals)


def writable(accs):
    return any("w" in permission.lower() or permission.lower() == "a"
               for permission in accs)


def check(sections, root, parameters):
    findings = []
    global_section = next((x for x in sections if x["name"] == "global"), None)
    listen = global_section["global"].get("i") if global_section else None
    command_listen = []
    for parameter in parameters:
        match = re.match(r"(?:--?|)?i(?:=|\s+)(.+)$", parameter.strip())
        if match:
            command_listen.append(match.group(1))
    if listen is None and not command_listen:
        report(findings, WARN, "no explicit listen address; copyparty defaults may expose all interfaces")
    elif listen is not None and public_listener(listen):
        report(findings, SEVERE, "public listener configured with i: %s" % listen,
               global_section["line"])
    for value in command_listen:
        if public_listener(value):
            report(findings, SEVERE, "public listener configured by command-line parameter: %s" % value)

    volumes = [x for x in sections if x["name"] not in ("global", "accounts", "groups") and x["path"]]
    global_assert_root = global_section and "vol-or-crash" in global_section["global"]
    canonical = []
    root_real = os.path.realpath(root) if root else None
    for volume in volumes:
        path = os.path.realpath(volume["path"])
        canonical.append((volume, path))
        if root_real and os.path.commonpath((root_real, path)) != root_real:
            report(findings, SEVERE, "volume %s path escapes --root: %s" %
                   (volume["name"], volume["path"]), volume["line"])
        if "assert_root" not in volume["flags"] and not global_assert_root:
            report(findings, WARN, "volume %s lacks assert_root" % volume["name"], volume["line"])
        for permission, users in volume["accs"].items():
            everyone = users.strip() == "*" or "*" in [x.strip() for x in users.split(",")]
            if everyone and permission.lower() == "a":
                report(findings, SEVERE, "volume %s grants anonymous full access (A: *)" %
                       volume["name"], volume["line"])
            elif everyone and "w" in permission.lower():
                report(findings, SEVERE, "volume %s grants anonymous write access (%s: *)" %
                       (volume["name"], permission), volume["line"])
            elif permission.lower() == "a":
                report(findings, WARN, "volume %s grants overly broad A permission" %
                       volume["name"], volume["line"])
        if writable(volume["accs"]) and not ({"maxb", "maxn", "vmaxb", "vmaxn"} & volume["flags"]):
            report(findings, WARN, "writable volume %s has no upload or volume limit" %
                   volume["name"], volume["line"])

    for index, (left, left_path) in enumerate(canonical):
        for right, right_path in canonical[index + 1:]:
            try:
                overlap = os.path.commonpath((left_path, right_path)) in (left_path, right_path)
            except ValueError:
                overlap = False
            if overlap:
                report(findings, SEVERE, "volume paths overlap: %s (%s) and %s (%s)" %
                       (left["name"], left["path"], right["name"], right["path"]), right["line"])
    return findings


def main():
    parser = argparse.ArgumentParser(description="check a copyparty config for common deployment risks")
    parser.add_argument("--config", "-c", required=True, help="path to copyparty config")
    parser.add_argument("--root", help="optional directory all volume paths must remain beneath")
    parser.add_argument("--arg", action="append", default=[],
                        help="effective copyparty parameter to check (repeatable; e.g. --arg=-i=0.0.0.0)")
    args = parser.parse_args()
    try:
        findings = check(parse(args.config), args.root, args.arg)
    except (IOError, OSError) as exc:
        parser.error("cannot read config: %s" % exc)

    print("copyparty configuration security report: %s" % args.config)
    if args.root:
        print("allowed volume root: %s" % os.path.realpath(args.root))
    if not findings:
        print("OK: no findings.")
    else:
        for severity, message, line in findings:
            where = " (line %s)" % line if line else ""
            print("%s%s: %s" % (severity, where, message))
    severe = sum(1 for severity, _, _ in findings if severity == SEVERE)
    warnings = len(findings) - severe
    print("summary: %d critical, %d warning" % (severe, warnings))
    if not severe:
        print("No critical findings.")
    return 2 if severe else 0


if __name__ == "__main__":
    sys.exit(main())
