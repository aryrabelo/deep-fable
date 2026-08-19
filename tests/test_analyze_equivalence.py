"""Tests for the equivalence-statistics additions to
bench/aider_polyglot/analyze.py: wilson_ci, paired_diff_ci, tost_paired_binary,
power_paired_tost, smallest_margin_for_power, report_equivalence, and
report_descriptives. Stdlib-only, no pytest fixtures needed.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "analyze", REPO_ROOT / "bench" / "aider_polyglot" / "analyze.py"
)
analyze = importlib.util.module_from_spec(spec)
sys.modules["analyze"] = analyze
spec.loader.exec_module(analyze)


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


# --------------------------------------------------------------------------
# wilson_ci
# --------------------------------------------------------------------------


def test_wilson_ci_hand_computed_k1_n1():
    # z=1.0, n=1, k=1: p_hat=1, denom=2, center=1.5, adj=0.5 -> (0.5, 1.0)
    lo, hi = analyze.wilson_ci(1, 1, z=1.0)
    assert abs(lo - 0.5) < 1e-12
    assert abs(hi - 1.0) < 1e-12


def test_wilson_ci_hand_computed_k0_n1():
    # z=1.0, n=1, k=0: p_hat=0, denom=2, center=0.5, adj=0.5 -> (0.0, 0.5)
    lo, hi = analyze.wilson_ci(0, 1, z=1.0)
    assert abs(lo - 0.0) < 1e-12
    assert abs(hi - 0.5) < 1e-12


def test_wilson_ci_endpoint_k_zero_is_exactly_zero():
    for n in (1, 10, 178):
        lo, hi = analyze.wilson_ci(0, n)
        assert lo == 0.0
        assert 0.0 < hi < 1.0


def test_wilson_ci_endpoint_k_equals_n_is_exactly_one():
    for n in (1, 10, 178):
        lo, hi = analyze.wilson_ci(n, n)
        assert hi == 1.0
        assert 0.0 < lo < 1.0


# --------------------------------------------------------------------------
# tost_paired_binary
# --------------------------------------------------------------------------


def test_tost_declares_equivalence_on_clearly_equivalent_table():
    # balanced discordance (b=c), large n, generous margin -> tight CI around 0
    result = analyze.tost_paired_binary(b=10, c=10, n=178, margin=0.08, alpha=0.05)
    assert result.equivalent is True
    assert result.ci[0] > -0.08 and result.ci[1] < 0.08
    assert result.p == max(result.p_lower, result.p_upper)


def test_tost_refuses_on_wide_ci_table():
    # small n, few discordant pairs -> CI wider than the margin even though
    # the point estimate itself sits inside it
    result = analyze.tost_paired_binary(b=2, c=1, n=20, margin=0.10, alpha=0.05)
    assert result.equivalent is False
    # CI must actually straddle outside the margin for this to be a real refusal
    assert result.ci[1] >= 0.10 or result.ci[0] <= -0.10


def test_tost_ci_matches_equivalent_flag():
    for b, c, n, margin in [(10, 10, 178, 0.08), (2, 1, 20, 0.10), (30, 5, 178, 0.05)]:
        result = analyze.tost_paired_binary(b, c, n, margin)
        expected = result.ci[0] > -margin and result.ci[1] < margin
        assert result.equivalent == expected


# --------------------------------------------------------------------------
# discordant-floor refusal (report_equivalence)
# --------------------------------------------------------------------------


def _runs_with_discordant(n_discordant_each_side: int, n_concordant: int = 0) -> dict:
    runs: dict = {}
    idx = 0
    for _ in range(n_discordant_each_side):
        runs[f"t{idx}"] = {"a": {1: True}, "b": {1: False}}
        idx += 1
    for _ in range(n_discordant_each_side):
        runs[f"t{idx}"] = {"a": {1: False}, "b": {1: True}}
        idx += 1
    for _ in range(n_concordant):
        runs[f"t{idx}"] = {"a": {1: True}, "b": {1: True}}
        idx += 1
    return runs


def test_report_equivalence_refuses_below_discordant_floor():
    runs = _runs_with_discordant(1)  # only 2 discordant pairs total
    plan = {"min_discordant_pairs": 10}
    out = _capture(analyze.report_equivalence, plan, "a", "b", runs, margin_pp=5.0)
    assert "UNDERPOWERED FOR EQUIVALENCE" in out
    assert "EQUIVALENT" not in out


def test_report_equivalence_concludes_above_discordant_floor():
    runs = _runs_with_discordant(10, n_concordant=100)  # 20 discordant, balanced
    plan = {"min_discordant_pairs": 10}
    out = _capture(analyze.report_equivalence, plan, "a", "b", runs, margin_pp=15.0)
    assert "UNDERPOWERED" not in out
    assert "TOST verdict:" in out
    assert "margin given: +/-15pp" in out
    assert "NOT evidence" in out  # standing non-significance-is-not-parity caveat


def test_report_equivalence_enforces_registered_discordance_ceiling():
    # 40 discordant of 60 pairs = 0.667, far above a registered ceiling of 0.35:
    # the plan's power claim does not hold there, so no verdict may be printed.
    runs = _runs_with_discordant(20, n_concordant=20)
    plan = {"min_discordant_pairs": 10, "equivalence_underpowered_above_discordant_rate": 0.35}
    out = _capture(analyze.report_equivalence, plan, "a", "b", runs, margin_pp=15.0)
    assert "UNDERPOWERED FOR EQUIVALENCE" in out
    assert "TOST verdict:" not in out
    assert "EQUIVALENT" not in out.replace("UNDERPOWERED FOR EQUIVALENCE", "")
    # same data, no ceiling registered -> the gate must not fire
    out2 = _capture(analyze.report_equivalence, {"min_discordant_pairs": 10}, "a", "b", runs, margin_pp=15.0)
    assert "TOST verdict:" in out2


# --------------------------------------------------------------------------
# power_paired_tost / smallest_margin_for_power
# --------------------------------------------------------------------------


def test_power_monotonic_in_n():
    powers = [analyze.power_paired_tost(n, margin=0.08, p_discordant=0.25) for n in (30, 90, 178, 400)]
    assert powers == sorted(powers)
    assert powers[0] < powers[-1]


def test_power_monotonic_in_margin():
    powers = [analyze.power_paired_tost(178, margin=m, p_discordant=0.25) for m in (0.02, 0.05, 0.10, 0.20)]
    assert powers == sorted(powers)
    assert powers[0] < powers[-1]


def test_smallest_margin_for_power_round_trips():
    for n in (60, 178):
        for p_discordant in (0.15, 0.25, 0.35):
            margin = analyze.smallest_margin_for_power(n, p_discordant, target=0.80)
            power_at_margin = analyze.power_paired_tost(n, margin, p_discordant)
            assert abs(power_at_margin - 0.80) < 0.01


# --------------------------------------------------------------------------
# report_descriptives
# --------------------------------------------------------------------------


def test_report_descriptives_runs_on_mixed_arms_missing_model_thinking():
    records = [
        {"benchmark": "aider_polyglot", "task_id": "python/foo", "arm": "ds-jspace", "passed": True,
         "tokens_in": 100, "latency_s": 1.5, "cost_usd": 0.001, "model": "deepseek", "thinking": "max"},
        {"benchmark": "aider_polyglot", "task_id": "python/bar", "arm": "ds-jspace", "passed": False,
         "tokens_in": 200, "latency_s": 2.0, "cost_usd": 0.002},  # no model/thinking keys
        {"benchmark": "aider_polyglot", "task_id": "go/baz", "arm": "opus-med", "passed": True,
         "tokens_in": 50, "latency_s": 0.5, "cost_usd": 0.01, "model": "opus", "thinking": "medium"},
        {"benchmark": "aider_polyglot", "task_id": "go/qux", "arm": "opus-med", "passed": False,
         "notes": "skip: no toolchain"},
    ]
    out = _capture(analyze.report_descriptives, records)
    assert "ds-jspace" in out
    assert "opus-med" in out
    assert "pass rate: 1/2" in out  # ds-jspace: skip excluded elsewhere, this arm has 2 real records
    assert "pass rate: 1/1" in out  # opus-med: the skip record is excluded
    assert "Wilson 95% CI" in out


# --------------------------------------------------------------------------
# CLI still exposes --help (existing invocation paths must keep working)
# --------------------------------------------------------------------------


def test_cli_help_exits_zero(capsys):
    import subprocess

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bench" / "aider_polyglot" / "analyze.py"), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--equivalence" in result.stdout
    assert "--descriptives" in result.stdout


if __name__ == "__main__":
    import subprocess

    r = subprocess.run([sys.executable, "-m", "pytest", __file__, "-q"])
    raise SystemExit(r.returncode)
