#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""McNemar / Wilcoxon analysis over aider_polyglot results JSONL file(s),
mechanically enforced against the locked plan in bench/PREREGISTRATION.md.

Paired design: every (task_id, arm) is compared against the SAME task_id
under a different arm, so the right test is McNemar's exact test on the
discordant pairs — never a two-proportion z-test, which assumes independent
samples we don't have here.

A task is dropped from every pairing if any record for it carries a
`notes: "skip: ..."` marker (missing toolchain) or `notes: "dry-run"` — those
aren't pass/fail signal, and silently scoring a skip as a fail would bias
every arm identically but still corrupt the discordant count.

Nothing about which comparison is primary, which side is being tested, the
significance level, the discordant-pair floor, or the length-control band is
hard-coded here: all of it is read from the single fenced ```json block in
bench/PREREGISTRATION.md (override with --prereg) on every run. If that file
is missing or the block doesn't parse, this script refuses to print any
verdict at all — an unregistered analysis is exactly what pre-registration
exists to prevent, and a script that "helpfully" falls back to hard-coded
defaults would defeat the whole point.

Two pre-specified analyses run over the same multi-run data (plan's
`runs_per_exercise`):
  (a) PRIMARY — one binary pass/fail per (task, arm), taken as the strict
      majority vote across that exercise's runs, fed to an exact McNemar
      test (one- or two-sided per the plan).
  (b) graded SECONDARY — the per-exercise pass *proportion* across runs
      (0, 1/3, 2/3, 1 at runs_per_exercise=3), compared with a Wilcoxon
      signed-rank test. This is always descriptive, never inferential, even
      when run on the primary arm pair — only one test in the whole report
      carries a significance verdict, which is what lets the primary skip a
      multiplicity correction.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
DEFAULT_PREREG_PATH = REPO_ROOT / "bench" / "PREREGISTRATION.md"

# Below this many non-zero paired differences, the normal approximation to
# the Wilcoxon signed-rank null distribution is not considered reliable
# (commonly-cited floor; see e.g. Conover, "Practical Nonparametric
# Statistics", 3rd ed., ch. 5.7). This is a property of the approximation
# itself, not a plan decision, so it isn't read from PREREGISTRATION.md.
WILCOXON_MIN_N = 10

_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
_ALT_RE = re.compile(r"^\s*(\S+)\s*>\s*(\S+)\s*$")

_REQUIRED_PLAN_KEYS: dict[str, type | tuple[type, ...]] = {
    "primary_comparison": list,
    "sided": int,
    "alternative": str,
    "alpha": (int, float),
    "power": (int, float),
    "expected_discordant_rate": (int, float),
    "usable_exercises": int,
    "runs_per_exercise": int,
    "mde_pp": (int, float),
    "min_discordant_pairs": int,
    "length_control_band": list,
    "secondary_comparisons": list,
    "multiplicity": str,
}


class PreregError(Exception):
    """The pre-registration plan is missing, unreadable, or unparseable.

    Every caller of load_prereg()/parse_alternative() MUST treat this as
    "refuse to print any verdict", not "fall back to a default" — a default
    is exactly the hard-coded, trust-me analysis this file exists to avoid.
    """


def load_prereg(path: Path) -> tuple[dict, str, str]:
    """Read, hash, and validate the locked plan. Returns (plan, sha256_hex,
    raw_text). Raises PreregError on any problem."""
    if not path.exists():
        raise PreregError(f"no such file: {path}")
    raw_bytes = path.read_bytes()
    sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise PreregError(f"{path} is not valid utf-8: {e}") from e

    blocks = _JSON_BLOCK_RE.findall(raw_text)
    if len(blocks) == 0:
        raise PreregError(f"no fenced ```json block found in {path}")
    if len(blocks) > 1:
        raise PreregError(
            f"expected exactly one fenced ```json block in {path} (the locked "
            f"machine-readable plan), found {len(blocks)} — ambiguous"
        )
    try:
        plan = json.loads(blocks[0])
    except json.JSONDecodeError as e:
        raise PreregError(f"malformed json in {path}'s fenced block: {e}") from e
    if not isinstance(plan, dict):
        raise PreregError(f"{path}'s json block must be an object, got {type(plan).__name__}")

    for key, types in _REQUIRED_PLAN_KEYS.items():
        if key not in plan:
            raise PreregError(f"{path} json block missing required key {key!r}")
        if not isinstance(plan[key], types) or isinstance(plan[key], bool):
            raise PreregError(
                f"{path} json block key {key!r} has wrong type: expected {types}, "
                f"got {type(plan[key]).__name__}"
            )
    if plan["sided"] not in (1, 2):
        raise PreregError(f"{path}: sided must be 1 or 2, got {plan['sided']!r}")
    if len(plan["primary_comparison"]) != 2:
        raise PreregError(f"{path}: primary_comparison must name exactly 2 arms")
    if len(plan["length_control_band"]) != 2:
        raise PreregError(f"{path}: length_control_band must have exactly 2 numbers")
    for pair in plan["secondary_comparisons"]:
        if not (isinstance(pair, list) and len(pair) == 2):
            raise PreregError(f"{path}: each secondary_comparisons entry must name exactly 2 arms")

    return plan, sha256_hex, raw_text


def parse_alternative(plan: dict) -> tuple[str, str]:
    """Return (favored_arm, other_arm) from plan['alternative'], e.g.
    'jspace > placebo' -> ('jspace', 'placebo'). The two arms named must be
    exactly the two arms in primary_comparison — a plan that tests one pair
    but declares a direction over a different pair is internally
    inconsistent and refused, not silently reinterpreted."""
    m = _ALT_RE.match(plan["alternative"])
    if not m:
        raise PreregError(f"cannot parse alternative {plan['alternative']!r}; expected '<arm> > <arm>'")
    favored, other = m.group(1), m.group(2)
    if {favored, other} != set(plan["primary_comparison"]):
        raise PreregError(
            f"alternative {plan['alternative']!r} does not name the same two arms as "
            f"primary_comparison {plan['primary_comparison']!r}"
        )
    return favored, other


def print_header(plan: dict, sha256_hex: str, path: Path) -> None:
    arm_a, arm_b = plan["primary_comparison"]
    sidedness = f"one-sided ({plan['alternative']})" if plan["sided"] == 1 else "two-sided"
    print(f"Pre-registration: {path} (sha256 {sha256_hex})")
    print(f"  primary comparison: {arm_a} vs {arm_b}   sidedness: {sidedness}")
    print(f"  declared MDE: {plan['mde_pp']}pp at alpha={plan['alpha']}, power={plan['power']}")
    print(f"  multiplicity: {plan['multiplicity']}")


def load_records(paths: list[Path]):
    for path in paths:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)


def aggregate_runs(records) -> dict[str, dict[str, dict[int, bool]]]:
    """task_id -> arm -> {run_idx: passed}. A task carrying any skip/dry-run
    record (any arm, any run) is dropped entirely — a skip isn't pass/fail
    signal, and scoring it either way would corrupt the discordant count."""
    runs: dict[str, dict[str, dict[int, bool]]] = defaultdict(lambda: defaultdict(dict))
    skip_or_dry: set[str] = set()
    for r in records:
        if r.get("benchmark") != "aider_polyglot":
            continue
        task_id, arm = r["task_id"], r["arm"]
        note = r.get("notes") or ""
        if note.startswith("skip:") or note == "dry-run":
            skip_or_dry.add(task_id)
            continue
        run_idx = int(r.get("run_idx", 1))
        runs[task_id][arm][run_idx] = bool(r["passed"])
    for task_id in skip_or_dry:
        runs.pop(task_id, None)
    return runs


def majority_vote(run_results: dict[int, bool]) -> bool:
    """Strict majority of the k runs recorded for one (task_id, arm). A tie
    (exactly half pass — impossible at the plan's odd runs_per_exercise=3,
    but reachable with partial data) counts as fail: conservative, and
    documented here rather than silently picked."""
    n = len(run_results)
    if n == 0:
        return False
    k = sum(run_results.values())
    return 2 * k > n


def pass_proportion(run_results: dict[int, bool]) -> float:
    n = len(run_results)
    if n == 0:
        return 0.0
    return sum(run_results.values()) / n


def majority_table(runs: dict[str, dict[str, dict[int, bool]]]) -> dict[str, dict[str, bool]]:
    return {tid: {arm: majority_vote(rr) for arm, rr in arms.items()} for tid, arms in runs.items()}


def proportion_table(runs: dict[str, dict[str, dict[int, bool]]]) -> dict[str, dict[str, float]]:
    return {tid: {arm: pass_proportion(rr) for arm, rr in arms.items()} for tid, arms in runs.items()}


def mcnemar_two_sided_p(b: int, c: int) -> float:
    """Two-sided exact McNemar test: binomial(n=b+c, p=0.5) tail doubled."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1))
    return min(1.0, 2 * tail * (0.5**n))


def mcnemar_one_sided_p(favor: int, against: int) -> float:
    """One-sided exact McNemar test for the pre-registered directional claim
    "favor-arm > against-arm". Caller MUST only invoke this after confirming
    favor > against (the observed effect runs the predicted way) — see
    report_primary_verdict()'s NO CLAIM branch for what happens otherwise.

    Formula: p = P(X <= against), X ~ Binomial(n=favor+against, p=0.5) — the
    probability, under the null of no true difference, of an imbalance at
    least this extreme *in the predicted direction only*. This is exactly
    half of mcnemar_two_sided_p(favor, against) whenever favor > against,
    because the two-sided test's tail is symmetric and this one spends all
    of it on the single predicted side.
    """
    assert favor > against, "one-sided p only defined once the direction is confirmed"
    n = favor + against
    tail = sum(math.comb(n, i) for i in range(against + 1))
    return min(1.0, tail * (0.5**n))


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


def print_length_control(by_arm: dict[str, list[int]], arms: list[str], plan: dict) -> bool:
    """Print per-arm tokens_in stats and gate the PRIMARY verdict.

    Returns True iff the primary verdict may be printed (either the primary
    pair isn't present in this data, or the length control held). Band and
    the arm pair it gates come from the plan, not a hard-coded pair name.
    """
    ratio_min, ratio_max = plan["length_control_band"]
    arm_a, arm_b = plan["primary_comparison"]

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

    if arm_a not in arms or arm_b not in arms:
        return True

    a_vals, b_vals = by_arm.get(arm_a, []), by_arm.get(arm_b, [])
    if not a_vals or not b_vals or all(v == 0 for v in a_vals + b_vals):
        print(
            f"\n  length control UNVERIFIED — tokens_in not populated for {arm_a}/{arm_b} "
            "(dry-run data, or the harness did not report usage). The PRIMARY verdict below "
            "is suppressed: a gate that passes on missing data is worse than no gate."
        )
        return False

    a_mean, b_mean = statistics.mean(a_vals), statistics.mean(b_vals)
    if b_mean == 0:
        print(f"\n  length control UNVERIFIED — {arm_b} mean tokens_in is 0, ratio undefined.")
        return False

    ratio = a_mean / b_mean
    print(
        f"\n  {arm_a}/{arm_b} mean tokens_in ratio: {ratio:.2f}x "
        f"(pre-registered band: {ratio_min:.1f}x-{ratio_max:.1f}x)"
    )
    if not (ratio_min <= ratio <= ratio_max):
        print(
            "  LENGTH CONTROL FAILED — ratio outside the pre-registered band. The PRIMARY "
            f"verdict below is suppressed: at this gap, a pass-rate delta could just mean "
            f"{arm_a} read more tokens, not that its specific instructions helped."
        )
        return False
    return True


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def normal_ppf(p: float) -> float:
    """Inverse standard normal CDF (probit), via bisection over normal_cdf
    (stdlib only -- no scipy). Accurate to ~1e-12, plenty for a z-score used
    in a CI half-width."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"p must be in (0, 1), got {p!r}")
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if normal_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def wilcoxon_signed_rank(diffs: list[float]) -> tuple[float, float, int]:
    """Wilcoxon signed-rank test, normal approximation with tie correction
    and continuity correction (stdlib only — no scipy).

    This is the graded companion to the binary majority-vote/McNemar
    primary: majority vote collapses each exercise's 3 runs to one bit and
    throws away *how* discordant the runs were (2/3 vs 3/3 both become
    "pass"). The signed-rank test instead ranks the *magnitude* of each
    exercise's proportion gap between arms, so an exercise where one arm
    clearly dominates (diff = 1) contributes more to the statistic than one
    where the arms barely differ (diff = 1/3) — using information the
    binary test discards, which is why the graded version has more power
    for a fixed set of exercises.

    Algorithm: drop zero differences (no signed information), rank |d_i|
    ascending with average ranks on ties, split into W+ (positive d_i) and
    W- (negative d_i):
      mu    = n(n+1)/4
      sigma = sqrt( n(n+1)(2n+1)/24 - sum(t_j^3 - t_j)/48 )   # t_j = tie-group sizes
      z     = (W+ - mu - 0.5*sign(W+ - mu)) / sigma            # continuity correction

    Returns (z, w_plus, n) where n counts only the non-zero differences.
    Validity floor: WILCOXON_MIN_N (see module docstring) — caller must
    check n before trusting z.
    """
    nz = [d for d in diffs if d != 0]
    n = len(nz)
    if n == 0:
        return 0.0, 0.0, 0

    order = sorted(range(n), key=lambda i: abs(nz[i]))
    ranks = [0.0] * n
    tie_correction = 0.0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(nz[order[j + 1]]) == abs(nz[order[i]]):
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        t = j - i + 1
        tie_correction += t**3 - t
        for m in range(i, j + 1):
            ranks[order[m]] = avg_rank
        i = j + 1

    w_plus = sum(ranks[k] for k in range(n) if nz[k] > 0)
    mu = n * (n + 1) / 4.0
    sigma2 = n * (n + 1) * (2 * n + 1) / 24.0 - tie_correction / 48.0
    if sigma2 <= 0:
        return 0.0, w_plus, n
    sigma = math.sqrt(sigma2)
    cc = 0.5 if w_plus > mu else (-0.5 if w_plus < mu else 0.0)
    z = (w_plus - mu - cc) / sigma
    return z, w_plus, n


def report_graded_secondary(arm1: str, arm2: str, proportions: dict[str, dict[str, float]]) -> None:
    diffs = [arms[arm1] - arms[arm2] for arms in proportions.values() if arm1 in arms and arm2 in arms]
    n_total = len(diffs)
    mean_diff = statistics.mean(diffs) if diffs else 0.0
    z, _w_plus, n_nonzero = wilcoxon_signed_rank(diffs)
    print(
        "  graded (per-run pass proportion, Wilcoxon signed-rank, pre-specified secondary — "
        "descriptive, no inferential claim):"
    )
    print(
        f"    n paired tasks: {n_total}   non-zero differences: {n_nonzero}   "
        f"mean proportion diff ({arm1}-{arm2}): {mean_diff:+.3f}"
    )
    if n_nonzero < WILCOXON_MIN_N:
        print(
            f"    normal approximation UNRELIABLE below n={WILCOXON_MIN_N} non-zero pairs "
            f"(have {n_nonzero}) — no z/p printed."
        )
        return
    p_two_sided = min(1.0, 2 * (1 - normal_cdf(abs(z))))
    print(f"    z = {z:.3f}   two-sided p (descriptive) = {p_two_sided:.4f}")


def report_primary_verdict(
    plan: dict, favored: str, other: str, arm1: str, arm2: str, only1: int, only2: int, discordant: int, gate_ok: bool
) -> None:
    if not gate_ok:
        print("  PRIMARY verdict suppressed: length control gate failed above (see Length control section).")
        return
    if discordant < plan["min_discordant_pairs"]:
        print(
            f"  UNDERPOWERED: {discordant} discordant pairs is below the pre-registered minimum "
            f"of {plan['min_discordant_pairs']}. No verdict — collect more paired tasks before "
            "trusting any p-value here."
        )
        return

    if plan["sided"] == 2:
        p = mcnemar_two_sided_p(only1, only2)
        direction = "neither (tied)" if only1 == only2 else (arm1 if only1 > only2 else arm2)
        verdict = f"SIGNIFICANT (p < {plan['alpha']})" if p < plan["alpha"] else f"not significant (p >= {plan['alpha']})"
        print(f"  McNemar exact two-sided p-value: {p:.4f}   favors: {direction}")
        print(f"  PRIMARY verdict: {verdict}")
        return

    # sided == 1: favor/against are oriented to the plan's declared direction,
    # not to arm1/arm2's alphabetical order.
    favor_count, against_count = (only1, only2) if arm1 == favored else (only2, only1)
    if favor_count == against_count:
        print(f"  observed: tied ({favor_count} vs {against_count} discordant pairs)")
        print("  PRIMARY verdict: NO CLAIM (effect opposes the pre-registered direction)")
        return
    if favor_count < against_count:
        print(f"  observed direction: {other} ({against_count} vs {favor_count} discordant pairs) — opposes the pre-registered direction ({favored} > {other})")
        print("  PRIMARY verdict: NO CLAIM (effect opposes the pre-registered direction)")
        return

    p = mcnemar_one_sided_p(favor_count, against_count)
    verdict = f"SIGNIFICANT (p < {plan['alpha']})" if p < plan["alpha"] else f"not significant (p >= {plan['alpha']})"
    print(f"  McNemar exact one-sided p-value ({favored} > {other}): {p:.4f}")
    print(f"  PRIMARY verdict: {verdict}")


def report(
    plan: dict,
    favored: str,
    other: str,
    runs: dict[str, dict[str, dict[int, bool]]],
    arms: list[str],
    gate_ok: bool,
) -> None:
    majority = majority_table(runs)
    proportions = proportion_table(runs)
    primary_pair = frozenset(plan["primary_comparison"])
    secondary_pairs = {frozenset(p) for p in plan["secondary_comparisons"]}

    if primary_pair - set(arms):
        print(f"\nNOTE: primary comparison {sorted(primary_pair)} not fully present in this data "
              f"(arms seen: {arms}) — no PRIMARY verdict will be printed this run.")

    for arm1, arm2 in itertools.combinations(sorted(arms), 2):
        pair = frozenset((arm1, arm2))
        both, only1, only2, neither = pair_table(majority, arm1, arm2)
        discordant = only1 + only2
        n_pairs = both + only1 + only2 + neither
        print(f"\n{arm1} vs {arm2}  (n paired tasks = {n_pairs}, majority-vote binary outcome)")
        print(f"  both pass: {both}    both fail: {neither}")
        print(f"  {arm1} only pass: {only1}    {arm2} only pass: {only2}")
        print(f"  discordant pairs: {discordant}")

        if pair == primary_pair:
            report_primary_verdict(plan, favored, other, arm1, arm2, only1, only2, discordant, gate_ok)
        elif pair in secondary_pairs:
            print("  descriptive, no inferential claim (secondary comparison per pre-registration)")
        else:
            print("  UNREGISTERED comparison — not named in the pre-registration; descriptive only, no inferential claim")

        report_graded_secondary(arm1, arm2, proportions)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n. Unlike the naive
    (Wald) normal approximation, this is well-behaved at the boundaries:
    exactly 0.0 at k=0 and exactly 1.0 at k=n, never negative or above 1."""
    if n <= 0:
        return 0.0, 1.0
    z2 = z * z
    p_hat = k / n
    denom = 1.0 + z2 / n
    center = p_hat + z2 / (2 * n)
    adj = z * math.sqrt(p_hat * (1 - p_hat) / n + z2 / (4 * n * n))
    lo, hi = (center - adj) / denom, (center + adj) / denom
    return max(0.0, lo), min(1.0, hi)


def paired_diff_ci(b: int, c: int, n: int, z: float) -> tuple[float, float]:
    """CI for the paired difference in pass proportions (b-c)/n, using the
    standard McNemar-style SE sqrt(b + c - (b-c)**2/n) / n. b, c are
    discordant counts; n is the total number of paired tasks."""
    diff = (b - c) / n
    se = math.sqrt(max(0.0, b + c - (b - c) ** 2 / n)) / n
    return diff - z * se, diff + z * se


@dataclass(frozen=True)
class TOSTResult:
    p_lower: float  # one-sided p, H0: true diff <= -margin
    p_upper: float  # one-sided p, H0: true diff >= +margin
    p: float        # max(p_lower, p_upper) -- the TOST p-value
    ci: tuple[float, float]
    equivalent: bool


def tost_paired_binary(b: int, c: int, n: int, margin: float, alpha: float = 0.05) -> TOSTResult:
    """Two one-sided tests (TOST) for equivalence of paired binary outcomes,
    on the McNemar paired-difference-of-proportions scale. b, c are
    discordant counts (arm-A-only-pass, arm-B-only-pass); n is the total
    number of paired tasks; margin is a proportion (0.05 = 5 percentage
    points). Declares equivalence iff the (1 - 2*alpha)-level two-sided CI
    for the paired difference falls strictly inside (-margin, +margin) --
    the standard CI-inclusion form of TOST, equivalent to both one-sided
    tests separately clearing alpha.

    Caller decides whether there are enough discordant pairs to trust this
    at all -- see report_equivalence(), which reuses the plan's existing
    min_discordant_pairs floor rather than inventing a second one here.
    """
    assert n > 0, "n must be positive"
    diff = (b - c) / n
    se = math.sqrt(max(0.0, b + c - (b - c) ** 2 / n)) / n

    if se == 0.0:
        # ponytail: degenerate case (zero discordant pairs, or every
        # discordant pair favors the same side) -- the point estimate is
        # certain, so decide directly instead of dividing by a zero SE.
        p_lower = 0.0 if diff > -margin else 1.0
        p_upper = 0.0 if diff < margin else 1.0
        ci = (diff, diff)
    else:
        z_tost = normal_ppf(1 - alpha)
        p_lower = 1.0 - normal_cdf((diff + margin) / se)
        p_upper = normal_cdf((diff - margin) / se)
        ci = paired_diff_ci(b, c, n, z_tost)

    p = max(p_lower, p_upper)
    equivalent = ci[0] > -margin and ci[1] < margin
    return TOSTResult(p_lower=p_lower, p_upper=p_upper, p=p, ci=ci, equivalent=equivalent)


def power_paired_tost(n: int, margin: float, p_discordant: float, alpha: float = 0.05) -> float:
    """Approximate power of the paired-binary TOST (normal approximation;
    Phillips 1990 / Diletti, Hauschke & Steinijans 1991 formula), assuming
    the true difference is 0 (the standard a-priori best-case assumption)
    and that discordant pairs split evenly (b ~ c ~ n*p_discordant/2), so
    SE ~= sqrt(p_discordant / n). The real SE depends on the unknown b/c
    split once data exists; this is only for choosing a margin before it
    does.
    """
    if n <= 0 or p_discordant <= 0 or margin <= 0:
        return 0.0
    se = math.sqrt(p_discordant / n)
    z = normal_ppf(1 - alpha)
    return max(0.0, min(1.0, 2 * normal_cdf(margin / se - z) - 1))


def smallest_margin_for_power(n: int, p_discordant: float, target: float = 0.80, alpha: float = 0.05) -> float:
    """Smallest equivalence margin (as a proportion) reaching `target` power
    at fixed n and an assumed discordant rate, found by bisection -- power
    is monotonically increasing in margin, so this is well-defined."""
    lo, hi = 0.0, 1.0
    if power_paired_tost(n, hi, p_discordant, alpha) < target:
        return hi  # ponytail: target unreachable at any margin <=100pp; caller should raise n
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if power_paired_tost(n, mid, p_discordant, alpha) < target:
            lo = mid
        else:
            hi = mid
    return hi


def report_equivalence(
    plan: dict, arm_a: str, arm_b: str, runs: dict[str, dict[str, dict[int, bool]]], margin_pp: float,
    alpha: float = 0.05,
) -> None:
    """Q3: TOST equivalence report between two arms. Confirmatory -- requires
    the same locked plan as the primary verdict, and refuses below the
    plan's existing min_discordant_pairs floor rather than a second one."""
    majority = majority_table(runs)
    both, only1, only2, neither = pair_table(majority, arm_a, arm_b)
    discordant = only1 + only2
    n_pairs = both + only1 + only2 + neither
    margin = margin_pp / 100.0

    print(f"\nEquivalence test (TOST): {arm_a} vs {arm_b}")
    print(f"  margin given: +/-{margin_pp:g}pp   alpha: {alpha}")
    print(
        "  NOTE: a non-significant superiority test (McNemar/Wilcoxon above) is NOT evidence "
        "of parity -- only this pre-specified TOST, with its own margin, can support an "
        "equivalence claim."
    )
    print(
        f"  n paired tasks: {n_pairs}   discordant pairs: {discordant} "
        f"({arm_a} only: {only1}, {arm_b} only: {only2})"
    )

    if discordant < plan["min_discordant_pairs"]:
        print(
            f"  UNDERPOWERED FOR EQUIVALENCE: {discordant} discordant pairs is below the "
            f"pre-registered minimum of {plan['min_discordant_pairs']}. Refusing to conclude "
            "equivalence or non-equivalence -- collect more paired tasks first."
        )
        return

    result = tost_paired_binary(only1, only2, n_pairs, margin, alpha)
    lo_pp, hi_pp = result.ci[0] * 100, result.ci[1] * 100
    print(f"  paired difference ({arm_a}-{arm_b}) CI: [{lo_pp:+.2f}pp, {hi_pp:+.2f}pp]")
    print(f"  one-sided p-values: p_lower={result.p_lower:.4f}  p_upper={result.p_upper:.4f}  TOST p={result.p:.4f}")

    # The plan may register a discordance rate above which the margin's 80%
    # power no longer holds. Enforce it here rather than trusting a reader to
    # notice: an equivalence claim at a discordance the plan called
    # underpowered is exactly the after-the-fact reinterpretation this file
    # exists to prevent.
    # ponytail: only this one optional key is enforced; add others the same
    # way if the plan grows them.
    ceiling = plan.get("equivalence_underpowered_above_discordant_rate")
    if ceiling is not None and n_pairs and discordant / n_pairs > ceiling:
        achieved = power_paired_tost(n_pairs, margin, discordant / n_pairs, alpha)
        print(
            f"  UNDERPOWERED FOR EQUIVALENCE: observed discordance "
            f"{discordant / n_pairs:.3f} exceeds the pre-registered ceiling of {ceiling} "
            f"for this margin (achieved power {achieved:.3f} at +/-{margin_pp:g}pp). "
            "Per the plan, no equivalence claim is made; the interval above is descriptive."
        )
        return
    verdict = f"EQUIVALENT within +/-{margin_pp:g}pp" if result.equivalent else "NOT shown equivalent at this margin"
    print(f"  TOST verdict: {verdict}")


def _lang_of(task_id: str) -> str:
    return task_id.split("/", 1)[0] if "/" in task_id else "unknown"


def _mean(vals: list[float]) -> float:
    return statistics.mean(vals) if vals else 0.0


def report_descriptives(records, arms: list[str] | None = None) -> None:
    """Q2: descriptive report, no pre-registration and no inferential claim
    -- per-arm pass rate with Wilson 95% CI, broken down per language, plus
    mean tokens_in/latency_s/cost_usd. Tolerates records that predate the
    model/thinking fields."""
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        if r.get("benchmark") != "aider_polyglot":
            continue
        note = r.get("notes") or ""
        if note.startswith("skip:") or note == "dry-run":
            continue
        by_arm[r["arm"]].append(r)

    print("\nDescriptive report (Q2) -- pass rates with Wilson 95% CI. Descriptive only, no")
    print("inferential claim (use --equivalence for a pre-registered hypothesis test).")

    for arm in sorted(arms if arms is not None else by_arm):
        recs = by_arm.get(arm, [])
        if not recs:
            print(f"\n{arm}: n=0")
            continue
        models = sorted({r.get("model") or "(unrecorded)" for r in recs})
        thinkings = sorted({r.get("thinking") or "(unrecorded)" for r in recs})
        k, n = sum(1 for r in recs if r["passed"]), len(recs)
        lo, hi = wilson_ci(k, n)
        print(f"\n{arm}  (model: {', '.join(models)}  thinking: {', '.join(thinkings)})")
        print(f"  pass rate: {k}/{n} = {k / n:.3f}   Wilson 95% CI: [{lo:.3f}, {hi:.3f}]")

        by_lang: dict[str, list[dict]] = defaultdict(list)
        for r in recs:
            by_lang[_lang_of(r["task_id"])].append(r)
        for lang in sorted(by_lang):
            lr = by_lang[lang]
            lk, ln = sum(1 for r in lr if r["passed"]), len(lr)
            llo, lhi = wilson_ci(lk, ln)
            print(f"    {lang:10s} {lk}/{ln} = {lk / ln:.3f}   CI: [{llo:.3f}, {lhi:.3f}]")

        tin = [float(r.get("tokens_in", 0)) for r in recs]
        lat = [float(r.get("latency_s", 0.0)) for r in recs]
        cost = [float(r.get("cost_usd", 0.0)) for r in recs]
        print(f"  mean tokens_in={_mean(tin):.0f}  mean latency_s={_mean(lat):.2f}  mean cost_usd={_mean(cost):.4f}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+", type=Path, help="One or more results JSONL files")
    ap.add_argument("--arms", default=None, help="Comma-separated arm subset (default: all seen)")
    ap.add_argument(
        "--prereg", type=Path, default=DEFAULT_PREREG_PATH,
        help="Path to the locked pre-registration plan (default: bench/PREREGISTRATION.md)",
    )
    ap.add_argument(
        "--descriptives", action="store_true",
        help="Print the Q2 descriptive report (pass rate + Wilson CI, per language, means) "
        "and exit. Runs without a pre-registration; descriptive only, no inferential claim.",
    )
    ap.add_argument(
        "--equivalence", nargs=2, metavar=("ARM_A", "ARM_B"), default=None,
        help="Run a TOST equivalence test between two arms instead of the confirmatory report. "
        "Requires --margin and a parseable pre-registration.",
    )
    ap.add_argument(
        "--margin", type=float, default=None,
        help="Equivalence margin in percentage points (required with --equivalence)",
    )
    ap.add_argument(
        "--alpha", type=float, default=0.05,
        help="Significance level for --equivalence (default: 0.05)",
    )
    args = ap.parse_args(argv)

    if args.equivalence and args.margin is None:
        ap.error("--equivalence requires --margin")

    if args.descriptives:
        for p in args.paths:
            if not p.exists():
                print(f"error: no such file: {p}", file=sys.stderr)
                return 1
        records = list(load_records(args.paths))
        if not records:
            print("no aider_polyglot records found", file=sys.stderr)
            return 1
        print("Descriptive-only mode: no pre-registration read, no inferential claim made.")
        seen_arms = sorted({r["arm"] for r in records if r.get("benchmark") == "aider_polyglot"})
        arms = args.arms.split(",") if args.arms else seen_arms
        report_descriptives(records, arms)
        return 0

    try:
        plan, sha256_hex, _raw = load_prereg(args.prereg)
        favored, other = parse_alternative(plan)
    except PreregError as e:
        print(f"REFUSING TO ANALYZE: {e}", file=sys.stderr)
        print(
            "analyze.py enforces the locked plan in bench/PREREGISTRATION.md mechanically; "
            "an unregistered or unparseable plan means no verdict can be trusted.",
            file=sys.stderr,
        )
        return 1

    print_header(plan, sha256_hex, args.prereg)

    for p in args.paths:
        if not p.exists():
            print(f"error: no such file: {p}", file=sys.stderr)
            return 1

    records = list(load_records(args.paths))
    if not records:
        print("no aider_polyglot records found", file=sys.stderr)
        return 1

    runs = aggregate_runs(records)
    seen_arms = {a for m in runs.values() for a in m}
    arms = args.arms.split(",") if args.arms else sorted(seen_arms)
    if len(arms) < 2:
        print("need at least 2 arms present in the data", file=sys.stderr)
        return 1

    print(
        f"\nLoaded {len(records)} record(s) from {len(args.paths)} file(s); "
        f"{len(runs)} task(s) with usable (non-skipped, non-dry-run) pass/fail data."
    )

    if args.equivalence:
        arm_a, arm_b = args.equivalence
        report_equivalence(plan, arm_a, arm_b, runs, args.margin, args.alpha)
        return 0

    by_arm_tokens = tokens_in_by_arm(records)
    gate_ok = print_length_control(by_arm_tokens, arms, plan)
    report(plan, favored, other, runs, arms, gate_ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
