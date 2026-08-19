#!/usr/bin/env python3
"""Scorer for the 5-model coding benchmark. Runs held-out acceptance per run workdir.

Usage: python3 model-eval/score.py
Reads: model-eval/work/<model>/<effort>/<task>/run-<n>/
Writes: stdout markdown table (per-cell pass/3, Wilson 95% CI per model-effort cell).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
ACC = ROOT / "acceptance"

CELLS = {
    "opus": ["low", "medium"],
    "sonnet": ["low", "medium"],
    "glm": ["low", "high", "max"],
    "kimi": ["low", "high", "max"],
    "deepseek": ["low", "high", "max"],
}
TASKS = ["T2-01", "T2-02", "C", "D", "E", "F"]
RUNS = [1, 2, 3]


def run_accept(model, effort, task, n):
    wd = WORK / model / effort / task / f"run-{n}"
    if not wd.exists():
        return "-", None
    meta = {}
    mp = wd / "_meta.json"
    if mp.exists():
        try:
            meta = json.loads(mp.read_text())
        except Exception:
            pass
    if meta.get("error"):
        return "ERR", meta.get("ms")
    try:
        if task == "T2-01":
            cmd, cwd = [sys.executable, "test_cart.py"], wd
        elif task == "T2-02":
            cmd, cwd = [sys.executable, "test_invoice.py"], wd
        else:
            cmd, cwd = [sys.executable, str(ACC / f"accept_{task.lower()}.py"), str(wd)], wd
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        return ("PASS" if p.returncode == 0 else "FAIL"), meta.get("ms")
    except subprocess.TimeoutExpired:
        return "TIMEOUT", meta.get("ms")
    except OSError as e:
        return f"ERR({e.errno})", meta.get("ms")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def main():
    header = "| task | " + " | ".join(f"{m}:{e}" for m, es in CELLS.items() for e in es) + " |"
    sep = "|" + "---|" * (1 + sum(len(es) for es in CELLS.values()))
    print(header)
    print(sep)
    cell_totals = {}
    for task in TASKS:
        row = [task]
        for m, es in CELLS.items():
            for e in es:
                res = [run_accept(m, e, task, n)[0] for n in RUNS]
                k = sum(1 for r in res if r == "PASS")
                cell_totals[(m, e)] = cell_totals.get((m, e), 0) + k
                row.append(str(k) if all(r in ("PASS", "FAIL") for r in res) else f"{k}({','.join(r for r in res if r not in ('PASS','FAIL'))})")
        print("| " + " | ".join(row) + " |")
    print()
    print("| cell | pass/18 | Wilson 95% CI |")
    print("|---|---|---|")
    for m, es in CELLS.items():
        for e in es:
            k = cell_totals[(m, e)]
            lo, hi = wilson(k, 18)
            print(f"| {m}:{e} | {k}/18 | [{lo:.2f}, {hi:.2f}] |")


if __name__ == "__main__":
    main()
