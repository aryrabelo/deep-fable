#!/usr/bin/env python3
"""Held-out acceptance for task D: duplicate **Pass:** drill detection (check #7)."""
import subprocess
import sys
from pathlib import Path

wd = Path(sys.argv[1]).resolve()
suite = wd / "scripts" / "verify_suite.py"
if not suite.exists():
    print("BAD: scripts/verify_suite.py missing in workdir")
    sys.exit(1)


def run():
    return subprocess.run(
        [sys.executable, str(suite)], capture_output=True, text=True, cwd=wd, timeout=60
    )


r = run()
print(f"pristine: exit {r.returncode}")
if r.returncode != 0:
    print((r.stdout + r.stderr)[-600:])
    sys.exit(1)

intro = wd / "modules" / "introspection.md"
markers = wd / "modules" / "markers.md"
pass_lines = [l for l in intro.read_text().splitlines() if l.startswith("**Pass:**")]
dup = pass_lines[0]
lines = markers.read_text().splitlines()
for i, l in enumerate(lines):
    if l.startswith("**Pass:**"):
        lines.insert(i + 1, dup)
        break
markers.write_text("\n".join(lines) + "\n")

r2 = run()
out = r2.stdout + r2.stderr
names_both = "introspection" in out and "markers" in out
print(f"duplicated: exit {r2.returncode}, names both modules: {names_both}")
if r2.returncode != 1 or not names_both:
    print(out[-600:])
    sys.exit(1)
print("ok")
sys.exit(0)
