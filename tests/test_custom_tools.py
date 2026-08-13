#!/usr/bin/env python3
"""Focused tests for phase-one deployment helpers; stdlib-only."""

from __future__ import print_function

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, "tools", "security", "check-config.py")
HOOK = os.path.join(ROOT, "tools", "audit", "jsonl-hook.sh")


class TestCustomTools(unittest.TestCase):
    def run_check(self, config, *args):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(config)
            path = f.name
        try:
            return subprocess.run(
                [sys.executable, CHECK, "--config", path, *args],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        finally:
            os.unlink(path)

    def test_check_config_reports_critical_exposure(self):
        result = self.run_check(
            """[global]
  i: 0.0.0.0
[/drop]
  /srv/drop
  accs:
    A: *
"""
        )
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("CRITICAL", result.stdout)
        self.assertIn("public listener", result.stdout)
        self.assertIn("anonymous full access", result.stdout)

    def test_check_config_reports_public_command_line_listener(self):
        result = self.run_check(
            "[global]\n  i: 127.0.0.1\n",
            "--arg=-i=0.0.0.0",
        )
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("command-line parameter", result.stdout)

    def test_check_config_accepts_restricted_volume(self):
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "uploads"))
            result = self.run_check(
                """[global]
  i: 127.0.0.1
[/uploads]
  {root}/uploads
  accs:
    rw: alice
  flags:
    assert_root
    maxb: 1g,300
    maxn: 100,600
    vmaxb: 10g
    vmaxn: 10000
""".format(root=root),
                "--root",
                root,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("No critical findings", result.stdout)

    def test_audit_hook_redacts_and_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            log = os.path.join(td, "audit.jsonl")
            event = json.dumps({"user": "alice", "password": "secret", "vp": "/a b"})
            env = os.environ.copy()
            env["AUDIT_LOG"] = log
            result = subprocess.run(
                [HOOK, event, "token=also-secret"],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            with open(log, "r") as f:
                record = json.loads(f.read())
            self.assertEqual("alice", record["hook"]["user"])
            self.assertEqual("[REDACTED]", record["hook"]["password"])
            self.assertEqual("[REDACTED]", record["argv"][0])
            self.assertEqual(0o600, stat.S_IMODE(os.stat(log).st_mode))


if __name__ == "__main__":
    unittest.main()
