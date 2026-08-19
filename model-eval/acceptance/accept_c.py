#!/usr/bin/env python3
"""Held-out acceptance for task C: alpha reject aliases must word-match, not substring."""
import importlib.util
import sys
import tempfile
from pathlib import Path

wd = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("v", wd / "verify.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    ({"expect_any": ["north"], "reject": ["no"]}, "FINAL ANSWER: north", "PASS"),
    ({"expect_any": ["50"], "reject": ["100"]}, "FINAL ANSWER: 100", "TRAP"),
    ({"expect_any": ["50"], "reject": ["100"]}, "FINAL ANSWER: 1100", "FAIL"),
]
tmp = Path(tempfile.mkdtemp())
ok = True
for i, (spec_, content, want) in enumerate(cases):
    f = tmp / f"r{i}.txt"
    f.write_text(content)
    got = mod.score_tier1(f, spec_)
    good = got == want or (want == "FAIL" and str(got).startswith("FAIL"))
    print(f"case{i}: want={want} got={got} -> {'ok' if good else 'BAD'}")
    ok = ok and good
sys.exit(0 if ok else 1)
