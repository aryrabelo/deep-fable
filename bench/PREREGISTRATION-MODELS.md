# Pre-registration — model comparison (Q2) and equivalence (Q3)

Locked 2026-08-19, before any run of these arms. `bench/PREREGISTRATION.md` stays untouched
and continues to govern the skill-efficacy question (Q0) on a fixed model. This document
governs the two model questions from `bench/RESUME.md` and nothing else.

Status at lock time: **zero paid calls, zero Anthropic quota consumed.** No data from these
arms exists. Every number below was computed from the committed code in
`bench/aider_polyglot/analyze.py` before seeing any outcome.

## Questions

- **Q2 (estimation).** deepseek+J-Space vs deepseek plain vs opus:medium — what are the
  numbers? Answered by point estimates with intervals, not by a verdict.
- **Q3 (equivalence).** Which Anthropic model does deepseek+J-Space match? Answered only by
  TOST against the margin registered below. A non-significant superiority test is **not**
  evidence of parity and will never be reported as one.

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
  "multiplicity": "Bonferroni across the two pre-specified Q3 equivalence tests (alpha 0.025 each, family-wise 0.05); the single Q2 McNemar is reported at alpha 0.05; all other comparisons are descriptive",
  "equivalence_margin_pp": 15.0,
  "equivalence_alpha": 0.025,
  "equivalence_comparisons": [["ds-jspace", "opus-med"], ["ds-jspace", "sonnet-med"]],
  "equivalence_underpowered_above_discordant_rate": 0.35
}
```

`sided: 2` and `alternative` coexist because the schema requires the key; with `sided: 2` the
direction in `alternative` carries no claim and `analyze.py` reports the two-sided p. `mde_pp`
is the achievable equivalence margin at alpha 0.025 and p_discordant 0.25, not a superiority
MDE.

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
- Anthropic quota cost, stated before authorisation is requested: **178 Opus invocations and
  178 Sonnet invocations.** Cash cost of the three deepseek arms: ~$2 total.

## Outcome and pairing

Primary outcome: binary pass/fail from the exercise's own test command, graded by
`run_tests()`. Pairing is by `task_id` (`lang/name`) across arms. Tasks carrying any skip or
dry-run record are excluded from every arm, as `aggregate_runs()` already enforces.

## Q3 — equivalence test, margin, and multiplicity

- Test: `tost_paired_binary(b, c, n, margin)` — TOST on the paired difference of pass
  proportions, McNemar-style SE, equivalence declared **only** when the whole confidence
  interval lies inside ±margin.
- **Registered margin: 15.0 percentage points.** Two-sided; applies to both Q3 comparisons.
- **Registered alpha: 0.025 per comparison** (Bonferroni over the two pre-specified Q3
  comparisons, family-wise 0.05).
- Pre-specified Q3 comparisons, both fixed now: `ds-jspace` vs `opus-med`, and `ds-jspace` vs
  `sonnet-med`. No other pair will be TOSTed.

### Why 15pp and not 5pp

Achievable margins at 80% power, from `smallest_margin_for_power()` in
`bench/aider_polyglot/analyze.py` (target 0.80, computed 2026-08-19):

| n | p_discordant=0.15 | 0.25 | 0.35 |
|---|---|---|---|
| 178 | 8.50pp | 10.97pp | 12.98pp |
| 120 | 10.35pp | 13.36pp | 15.80pp |
| 90 | 11.95pp | 15.42pp | 18.25pp |
| 60 | 14.63pp | 18.89pp | 22.35pp |

(alpha 0.05; at the registered alpha 0.025 the n=178 row becomes 9.41 / 12.15 / 14.37pp.)

**5pp is not reachable at n=178 at any plausible discordance rate.** The tightest achievable
margin there is ~8.5pp, and only if discordance is as low as 0.15. Registering 15.0pp at
alpha 0.025 gives power 0.999 / 0.959 / 0.845 at p_discordant 0.15 / 0.25 / 0.35.

**Underpowered branch, registered in advance:** if observed discordance exceeds 0.35 —
where power at 15pp falls to 0.694 at 0.45 — the TOST result will be reported as
**underpowered**, with the observed discordance and the achieved power printed, and no
equivalence claim will be made. Likewise the existing `min_discordant_pairs` floor from
`bench/PREREGISTRATION.md` is reused as a hard refusal floor by `report_equivalence()`;
below it, nothing is concluded.

15pp is a wide margin. It is what this n buys. "Matches within 15 percentage points" is the
strongest honest form of a positive Q3 result here, and it will be stated that way, with the
margin in the sentence, or not stated at all.

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

1. Q2 descriptives: five arms, Wilson CIs, per language, cost/latency/tokens.
2. Q2 confirmatory: McNemar `ds-jspace` vs `opus-med`.
3. Q3: TOST `ds-jspace` vs `opus-med` and `ds-jspace` vs `sonnet-med`, margin 15.0pp,
   alpha 0.025 each, with the underpowered branch above.

Any analysis outside this list is exploratory and will be labelled exploratory.
