#!/usr/bin/env python3
"""Held-out acceptance for task E: jspace.py stats subcommand."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

wd = Path(sys.argv[1]).resolve()
script = wd / "jspace.py"
if not script.exists():
    print("BAD: jspace.py missing in workdir")
    sys.exit(1)
tmp = tempfile.mkdtemp()
pat = re.compile(r"^verified=\d+ open=\d+ core=\d+$")


def run(*args):
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, cwd=tmp, timeout=30,
    )


r1 = run("stats")
ok1 = r1.returncode == 0 and any(pat.match(l.strip()) for l in r1.stdout.splitlines())
print(f"empty dir: exit {r1.returncode}, pattern ok: {ok1}")

r2 = run("note", "--goal", "g", "--next", "n")
r3 = run("stats")
ok3 = r3.returncode == 0 and any(pat.match(l.strip()) for l in r3.stdout.splitlines())
print(f"after note: note exit {r2.returncode}, stats exit {r3.returncode}, pattern ok: {ok3}")

sys.exit(0 if (ok1 and r2.returncode == 0 and ok3) else 1)
