#!/usr/bin/env python3
"""Held-out acceptance for task F: score_tier2 survives TimeoutExpired/OSError."""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

wd = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("v", wd / "verify.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

td = Path(tempfile.mkdtemp())
(td / "test_cart.py").write_text("# placeholder\n")

ok = True

with mock.patch.object(
    mod.subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1)
):
    try:
        got = mod.score_tier2(td)
        good = isinstance(got, str) and got.startswith("TIMEOUT")
        print(f"timeout: got={got!r} -> {'ok' if good else 'BAD'}")
        ok = ok and good
    except Exception as e:
        print(f"BAD: timeout raised {type(e).__name__}: {e}")
        ok = False

with mock.patch.object(mod.subprocess, "run", side_effect=OSError("boom")):
    try:
        got = mod.score_tier2(td)
        good = isinstance(got, str) and got.startswith("ERROR")
        print(f"oserror: got={got!r} -> {'ok' if good else 'BAD'}")
        ok = ok and good
    except Exception as e:
        print(f"BAD: oserror raised {type(e).__name__}: {e}")
        ok = False

fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="OK\n")
with mock.patch.object(mod.subprocess, "run", return_value=fake):
    got = mod.score_tier2(td)
    good = got == "PASS"
    print(f"normal: got={got!r} -> {'ok' if good else 'BAD'}")
    ok = ok and good

sys.exit(0 if ok else 1)
