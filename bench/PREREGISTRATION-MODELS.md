# Pre-registration — model comparison (Q2) and equivalence (Q3)

Locked 2026-08-19, before any run of these arms. `bench/PREREGISTRATION.md` stays untouched
and continues to govern the skill-efficacy question (Q0) on a fixed model. This document
governs the two model questions from `bench/RESUME.md` and nothing else.

**Amendment 1, 2026-08-19, before any arm produced data.** A `kimi-max` arm
(`kimi-code/k3`, thinking `max`, no skill) was added at the user's request, with a third Q3
equivalence comparison. This is an amendment to a plan with **zero observations in hand**, not
a post-hoc revision: had it been made after the sweep ran, it would have voided the
pre-registration and is why it was made now. It costs margin — Bonferroni over three
comparisons instead of two moves alpha from 0.025 to 0.0167, and the registered margin from
15.0pp to 16.0pp (see "Why 16pp"). No other parameter changed. Provider auth for `kimi-code`
was not yet configured at amendment time; if the arm cannot run, it will be reported as **not
run**, and its absence will not be filled in by any substitute.

Status at lock time: **~$0.02 spent (three Q1 config probes), zero Anthropic quota consumed.**
No data from any arm exists. Every number below was computed from the committed code in
`bench/aider_polyglot/analyze.py` before seeing any outcome.

## Questions

- **Q2 (estimation).** deepseek+J-Space vs deepseek plain vs opus:medium — what are the
  numbers? Answered by point estimates with intervals, not by a verdict.
- **Q3 (equivalence).** Which other model does deepseek+J-Space match? Answered only by TOST
  against the margin registered below, against Opus, Sonnet, and Kimi k3. A non-significant
  superiority test is **not** evidence of parity and will never be reported as one.

## The locked plan (machine-readable)

Exactly one fenced `json` block, as `load_prereg()` requires. `equivalence_margin_pp` and
`equivalence_alpha` are the Q3 parameters; the superiority keys describe the single
confirmatory Q2 McNemar. Changing this block after data exists voids the pre-registration.

```json
{
  "primary_comparison": ["ds-jspace", "opus-med"],
  "sided": 2,
  "alternative": "ds-jspace > opus-med",
  "alpha": 0.05,
  "power": 0.80,
  "expected_discordant_rate": 0.25,
  "usable_exercises": 178,
  "runs_per_exercise": 1,
  "mde_pp": 12.15,
  "min_discordant_pairs": 10,
  "length_control_band": [1.0, 4.0],
  "secondary_comparisons": [["ds-jspace", "sonnet-med"], ["ds-jspace", "ds-plain"], ["ds-plain", "opus-med"]],
  "multiplicity": "Bonferroni across the three pre-specified Q3 equivalence tests (alpha 0.0167 each, family-wise 0.05); the single Q2 McNemar is reported at alpha 0.05; all other comparisons are descriptive",
  "equivalence_margin_pp": 16.0,
  "equivalence_alpha": 0.0167,
  "equivalence_comparisons": [["ds-jspace", "opus-med"], ["ds-jspace", "sonnet-med"], ["ds-jspace", "kimi-max"]],
  "equivalence_underpowered_above_discordant_rate": 0.35
}
```

`sided: 2` and `alternative` coexist because the schema requires the key; with `sided: 2` the
direction in `alternative` carries no claim and `analyze.py` reports the two-sided p. `mde_pp`
is the achievable equivalence margin at alpha 0.0167 and p_discordant 0.25 (12.78pp), not a
superiority MDE.

## Arms

Each arm is a `(model, thinking, skill)` triple; see `ARM_SPECS` in `bench/arms/arms.py`,
which is the executable copy of this table.

| Arm | Model | Thinking | Skill | Serves |
|---|---|---|---|---|
| `ds-jspace` | `openrouter/deepseek/deepseek-v4-flash-0731` | max | jspace | Q2, Q3 |
| `ds-plain` | `openrouter/deepseek/deepseek-v4-flash-0731` | max | none | Q2, Q3 |
| `ds-placebo` | `openrouter/deepseek/deepseek-v4-flash-0731` | max | placebo | skill efficacy only |
| `opus-med` | `anthropic/claude-opus-5` | medium | none | Q2, Q3 |
| `sonnet-med` | `anthropic/claude-sonnet-5` | medium | none | Q3 (brackets where `ds-jspace` lands) |
| `kimi-max` | `kimi-code/k3` | max | none | Q2, Q3 (second non-Anthropic reference point) |

Thinking is constant across the three deepseek arms, so the skill is the only difference
between them. The Anthropic arms use `medium` because that is the comparison asked for; they
are therefore **not** an all-effort-levels claim about Opus or Sonnet.

## Sample and runs

- **n = 178**, the full Aider polyglot exercise set. No subsampling. Subsampling only loses
  power (see the margin table: n=120 already needs ~13.4pp at p_discordant=0.25 vs ~11.0pp at
  n=178), and dollars are not the binding constraint.
- **k = 1 run** per (arm, exercise). Run-to-run variance is therefore inside the outcome
  rather than averaged out. This inflates discordance, and the registered margin below is
  chosen to hold at discordance up to 0.35 for exactly that reason.
- Quota cost, stated before authorisation is requested: **178 Opus invocations, 178 Sonnet
  invocations, and 178 Kimi k3 invocations** (Kimi is a subscription plan, $0 cash). Cash cost
  of the three deepseek arms: ~$2 total.

## Outcome and pairing

Primary outcome: binary pass/fail from the exercise's own test command, graded by
`run_tests()`. Pairing is by `task_id` (`lang/name`) across arms. Tasks carrying any skip or
dry-run record are excluded from every arm, as `aggregate_runs()` already enforces.

## Q3 — equivalence test, margin, and multiplicity

- Test: `tost_paired_binary(b, c, n, margin)` — TOST on the paired difference of pass
  proportions, McNemar-style SE, equivalence declared **only** when the whole confidence
  interval lies inside ±margin.
- **Registered margin: 16.0 percentage points.** Two-sided; applies to all three Q3
  comparisons.
- **Registered alpha: 0.0167 per comparison** (Bonferroni over the three pre-specified Q3
  comparisons, family-wise 0.05).
- Pre-specified Q3 comparisons, all three fixed now: `ds-jspace` vs `opus-med`, `ds-jspace` vs
  `sonnet-med`, and `ds-jspace` vs `kimi-max`. No other pair will be TOSTed.

### Why 16pp and not 5pp

Achievable margins at 80% power, from `smallest_margin_for_power()` in
`bench/aider_polyglot/analyze.py` (target 0.80, alpha 0.05, computed 2026-08-19):

| n | p_discordant=0.15 | 0.25 | 0.35 |
|---|---|---|---|
| 178 | 8.50pp | 10.97pp | 12.98pp |
| 120 | 10.35pp | 13.36pp | 15.80pp |
| 90 | 11.95pp | 15.42pp | 18.25pp |
| 60 | 14.63pp | 18.89pp | 22.35pp |

At the registered alpha of 0.0167 the n=178 row becomes **9.90 / 12.78 / 15.12pp**.

**5pp is not reachable at n=178 at any plausible discordance rate.** The tightest achievable
margin is ~8.5pp, and only at alpha 0.05 with discordance as low as 0.15.

**What the third comparison cost.** With two Q3 comparisons the plan registered 15.0pp at
alpha 0.025. Adding `kimi-max` moves alpha to 0.0167, where 15.0pp yields power
0.998 / 0.939 / **0.790** at discordance 0.15 / 0.25 / 0.35 — below the 0.80 floor at the top
of the range. 16.0pp restores it: **0.999 / 0.968 / 0.861**. So the kimi arm costs exactly one
percentage point of margin, and that is the trade, stated before any data exists rather than
discovered afterwards.

**Underpowered branch, registered in advance:** if observed discordance exceeds 0.35 the TOST
result is reported as **underpowered**, with the observed discordance and achieved power
printed and no equivalence claim made. `report_equivalence()` enforces this mechanically — it
is not left to a reader. The existing `min_discordant_pairs` floor is likewise a hard refusal
floor; below it, nothing is concluded.

16pp is a wide margin. It is what this n and three comparisons buy. "Matches within 16
percentage points" is the strongest honest form of a positive Q3 result here, and it will be
stated that way, with the margin in the sentence, or not stated at all.

## Q2 — estimation, plus one confirmatory test

- **Descriptives (the primary Q2 answer):** per-arm pass rate with Wilson 95% CIs, overall and
  per language, plus mean `tokens_in`, mean latency and mean cost per arm, from
  `report_descriptives()`. These are reported regardless of any test outcome.
- **One confirmatory test:** exact two-sided McNemar on `ds-jspace` vs `opus-med`, alpha 0.05.
  Direction is not pre-specified — this is a difference question, not a directional claim.
- `ds-jspace` vs `ds-plain` and `ds-jspace` vs `ds-placebo` are the skill-efficacy question and
  are governed by `bench/PREREGISTRATION.md`, including its length-control gate (which applies
  to the `ds-jspace` vs `ds-placebo` pair only). Nothing here relaxes that gate.

## Guards retained

The discordant-pair floor, the length-control gate, the refusal to analyze without a parseable
plan, and the requirement that a published claim cite the pre-registration hash `analyze.py`
prints, the discordant-pair count, and mean `tokens_in` per arm (§7 of `docs/BENCHMARKS.md`).

## Locked list of everything reported

1. Q2 descriptives: six arms, Wilson CIs, per language, cost/latency/tokens.
2. Q2 confirmatory: McNemar `ds-jspace` vs `opus-med`.
3. Q3: TOST `ds-jspace` vs `opus-med`, `ds-jspace` vs `sonnet-med`, and `ds-jspace` vs
   `kimi-max`, margin 16.0pp, alpha 0.0167 each, with the underpowered branch above. If an arm
   could not run (e.g. missing provider auth), its comparison is reported as **not run**.

Any analysis outside this list is exploratory and will be labelled exploratory.
