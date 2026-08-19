#!/usr/bin/env python3
"""Deterministic scorer for the jspace-eval benchmark.

Tier 1: reads results/<model>/<condition>/<TID>.txt, extracts the FINAL ANSWER line,
checks accept/reject substrings from prompts/tier1/answers.json.
Tier 2: runs test_cart.py in each results/<model>/<condition>/T2-01/ workdir.

Usage: python3 jspace-eval/verify.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANSWERS = json.loads((ROOT / "prompts/tier1/answers.json").read_text())
RESULTS = ROOT / "results"
SCAFFOLD = ROOT / "tasks/tier2/T2-01/scaffold"

MODELS = ["deepseek", "fable", "glm", "kimi"]
CONDS = ["baseline", "jspace"]


def extract_marker(text: str):
    """Pull the answer string out of a raw or JSON-structured agent reply."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        data = None
    if data is not None:
        found = []

        def walk(node, key=""):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, k)
            elif isinstance(node, list):
                for v in node:
                    walk(v, key)
            elif isinstance(node, (str, int, float)):
                if not re.search(r"reasoning|verification|explanation|detail|steps|check", key, re.I):
                    found.append(str(node))

        walk(data)
        for s in found:
            if s.strip().upper().startswith("FINAL ANSWER:"):
                return s.split(":", 1)[1].strip().lower()
        short = [s.strip() for s in found if s and len(s) < 80]
        if short:
            return " | ".join(short).lower()
        return None
    for line in reversed(text.splitlines()):
        if line.strip().upper().startswith("FINAL ANSWER:"):
            return line.split(":", 1)[1].strip().lower()
    return None


def score_tier1(path: Path, spec: dict) -> str:
    if not path.exists():
        return "-"
    marker = extract_marker(path.read_text(errors="replace"))
    if marker is None:
        return "NO-MARKER"
    norm = marker.replace("$", "").replace(",", "")
    tokens = re.findall(r"[a-z0-9.]+", norm)

    def hit(alias: str) -> bool:
        a = alias.lower()
        if re.fullmatch(r"[\d.]+", a):  # numeric: exact token, not substring
            return a in tokens
        return re.search(rf"\b{re.escape(a)}\b", norm) is not None

    for bad in spec.get("reject", []):
        if hit(bad):
            return "TRAP"
    for key in ("expect_any",):
        if spec.get(key) and any(hit(a) for a in spec[key]):
            return "PASS"
    if spec.get("expect_all") and all(hit(a) for a in spec["expect_all"]):
        return "PASS"
    return f"FAIL ({marker[:40]})"


def score_tier2(workdir: Path) -> str:
    if not (workdir / "test_cart.py").exists():
        return "-"
    proc = subprocess.run(
        [sys.executable, "test_cart.py"],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    last = (proc.stderr.strip().splitlines() or proc.stdout.strip().splitlines() or [""])[-1]
    return "PASS" if proc.returncode == 0 else f"FAIL ({last[:40]})"


def main() -> None:
    tids = sorted(ANSWERS)
    header = "| task | " + " | ".join(f"{m} {c}" for m in MODELS for c in CONDS) + " |"
    sep = "|" + "---|" * (1 + len(MODELS) * len(CONDS))
    rows = [header, sep]
    for tid in tids:
        cells = [
            score_tier1(RESULTS / m / c / f"{tid}.txt", ANSWERS[tid])
            for m in MODELS
            for c in CONDS
        ]
        rows.append(f"| {tid} | " + " | ".join(cells) + " |")
    cells = [
        score_tier2(RESULTS / m / c / "T2-01") for m in MODELS for c in CONDS
    ]
    rows.append("| T2-01 | " + " | ".join(cells) + " |")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
