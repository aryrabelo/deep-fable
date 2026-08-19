#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Pairwise McNemar exact test over aider_polyglot results JSONL file(s).

Paired design: every (task_id, arm) is compared against the SAME task_id
under a different arm, so the right test is McNemar's exact test on the
discordant pairs — never a two-proportion z-test, which assumes independent
samples we don't have here.

A task is dropped from every pairing if any record for it carries a
`notes: "skip: ..."` marker (missing toolchain) or `notes: "dry-run"` — those
aren't pass/fail signal, and silently scoring a skip as a fail would bias
every arm identically but still corrupt the discordant count.

If a (task_id, arm) has more than one run, "passed" is best-of-N (True if any
run passed), matching aider's own pass_rate_2 definition.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

MIN_DISCORDANT = 10

# The placebo is length-matched to the ~60-token always-on snippet, not to
# the skill it routes to (SKILL.md alone is 3,834 tokens; the full payload
# with modules + references is up to 42,675 — see profile/APPEND_SYSTEM.md
# and .omp/skills/j-space/). So mean tokens_in is expected to diverge once
# jspace actually reads skill://j-space: reading nothing (ratio ~1x) means
# the instruction never fired and jspace is behaviorally indistinguishable
# from placebo; reading the *entire* skill on every task (which a working
# dynamic-routing skill should never do — it should route to the one
# relevant module) would swamp a typical multi-turn exercise session with
# raw token volume rather than targeted instructions. 4x is chosen as the
# ceiling because reading SKILL.md plus one module (the intended routed
# behavior) is a small fraction of a real session's token count, while
# reading the full 42,675-token payload on every task is not — it stops
# being "the same idea, shorter vs. longer" and starts being "meaningfully
# more compute," which is exactly the confound placebo exists to rule out.
LENGTH_RATIO_MIN = 1.0
LENGTH_RATIO_MAX = 4.0


def load_records(paths: list[Path]):
    for path in paths:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)


def aggregate(records) -> dict[str, dict[str, bool]]:
    passed: dict[str, dict[str, bool]] = defaultdict(dict)
    skip_or_dry: set[str] = set()
    for r in records:
        if r.get("benchmark") != "aider_polyglot":
            continue
        task_id, arm = r["task_id"], r["arm"]
        note = r.get("notes") or ""
        if note.startswith("skip:") or note == "dry-run":
            skip_or_dry.add(task_id)
            continue
        passed[task_id][arm] = passed[task_id].get(arm, False) or bool(r["passed"])
    for task_id in skip_or_dry:
        passed.pop(task_id, None)
    return passed


def mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact McNemar test: binomial(n=b+c, p=0.5) tail doubled."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1))
    return min(1.0, 2 * tail * (0.5**n))


def pair_table(passed: dict[str, dict[str, bool]], arm1: str, arm2: str) -> tuple[int, int, int, int]:
    both = only1 = only2 = neither = 0
    for arms in passed.values():
        if arm1 not in arms or arm2 not in arms:
            continue
        p1, p2 = arms[arm1], arms[arm2]
        if p1 and p2:
            both += 1
        elif p1:
            only1 += 1
        elif p2:
            only2 += 1
        else:
            neither += 1
    return both, only1, only2, neither


def tokens_in_by_arm(records) -> dict[str, list[int]]:
    """Per-arm tokens_in for real (non-skip, non-dry-run) invocations only."""
    by_arm: dict[str, list[int]] = defaultdict(list)
    for r in records:
        if r.get("benchmark") != "aider_polyglot":
            continue
        note = r.get("notes") or ""
        if note.startswith("skip:") or note == "dry-run":
            continue
        by_arm[r["arm"]].append(int(r.get("tokens_in", 0)))
    return by_arm


def print_length_control(by_arm: dict[str, list[int]], arms: list[str]) -> bool:
    """Print per-arm tokens_in stats and gate the jspace-vs-placebo verdict.

    Returns True iff a jspace-vs-placebo verdict may be printed (either the
    pair isn't present, or the length control held).
    """
    print("\nLength control (tokens_in per real invocation, skip/dry-run excluded):")
    for arm in sorted(arms):
        vals = by_arm.get(arm, [])
        if not vals:
            print(f"  {arm:8s} n=0")
            continue
        print(
            f"  {arm:8s} n={len(vals):<5d} mean={statistics.mean(vals):.0f}"
            f"  median={statistics.median(vals):.0f}"
        )

    if "jspace" not in arms or "placebo" not in arms:
        return True

    jvals, pvals = by_arm.get("jspace", []), by_arm.get("placebo", [])
    if not jvals or not pvals or all(v == 0 for v in jvals + pvals):
        print(
            "\n  length control UNVERIFIED — tokens_in not populated for jspace/placebo "
            "(dry-run data, or the harness did not report usage). The jspace-vs-placebo "
            "verdict below is suppressed: a gate that passes on missing data is worse than "
            "no gate."
        )
        return False

    j_mean, p_mean = statistics.mean(jvals), statistics.mean(pvals)
    if p_mean == 0:
        print("\n  length control UNVERIFIED — placebo mean tokens_in is 0, ratio undefined.")
        return False

    ratio = j_mean / p_mean
    print(
        f"\n  jspace/placebo mean tokens_in ratio: {ratio:.2f}x "
        f"(defensible band: {LENGTH_RATIO_MIN:.1f}x-{LENGTH_RATIO_MAX:.1f}x)"
    )
    if not (LENGTH_RATIO_MIN <= ratio <= LENGTH_RATIO_MAX):
        print(
            "  LENGTH CONTROL FAILED — ratio outside the defensible band. The jspace-vs-placebo "
            "verdict below is suppressed: at this gap, a pass-rate delta could just mean jspace "
            "read more tokens, not that its specific instructions helped."
        )
        return False
    return True


def report(passed: dict[str, dict[str, bool]], arms: list[str], gate_ok: bool = True) -> None:
    for arm1, arm2 in itertools.combinations(sorted(arms), 2):
        both, only1, only2, neither = pair_table(passed, arm1, arm2)
        discordant = only1 + only2
        n_pairs = both + only1 + only2 + neither
        print(f"\n{arm1} vs {arm2}  (n paired tasks = {n_pairs})")
        print(f"  both pass: {both}    both fail: {neither}")
        print(f"  {arm1} only pass: {only1}    {arm2} only pass: {only2}")
        print(f"  discordant pairs: {discordant}")
        if {arm1, arm2} == {"jspace", "placebo"} and not gate_ok:
            print("  verdict suppressed: length control gate failed above (see Length control section).")
            continue
        if discordant < MIN_DISCORDANT:
            print(
                f"  UNDERPOWERED: {discordant} discordant pairs is below the minimum of "
                f"{MIN_DISCORDANT}. No verdict — collect more paired tasks before trusting "
                "any p-value here."
            )
            continue
        p = mcnemar_exact_p(only1, only2)
        if only1 == only2:
            direction = "neither (tied)"
        else:
            direction = arm1 if only1 > only2 else arm2
        verdict = "SIGNIFICANT (p < 0.05)" if p < 0.05 else "not significant (p >= 0.05)"
        print(f"  McNemar exact p-value: {p:.4f}   favors: {direction}")
        print(f"  verdict: {verdict}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+", type=Path, help="One or more results JSONL files")
    ap.add_argument("--arms", default=None, help="Comma-separated arm subset (default: all seen)")
    args = ap.parse_args(argv)

    for p in args.paths:
        if not p.exists():
            print(f"error: no such file: {p}", file=sys.stderr)
            return 1

    records = list(load_records(args.paths))
    if not records:
        print("no aider_polyglot records found", file=sys.stderr)
        return 1

    passed = aggregate(records)
    seen_arms = {a for m in passed.values() for a in m}
    arms = args.arms.split(",") if args.arms else sorted(seen_arms)
    if len(arms) < 2:
        print("need at least 2 arms present in the data", file=sys.stderr)
        return 1

    print(
        f"Loaded {len(records)} record(s) from {len(args.paths)} file(s); "
        f"{len(passed)} task(s) with usable (non-skipped, non-dry-run) pass/fail data."
    )

    by_arm_tokens = tokens_in_by_arm(records)
    gate_ok = print_length_control(by_arm_tokens, arms)
    report(passed, arms, gate_ok=gate_ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
