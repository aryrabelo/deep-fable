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

**Amendment 2, 2026-08-19, before any observation in the registered strata.** At the user's
direction the sweep is restricted to **javascript, python and rust** — 113 exercises
(49 / 34 / 30) instead of 178. `cpp` and `go` are dropped by decision; `java` was never usable
on this machine. Consequences, all registered here rather than discovered later:

- `usable_exercises` 178 → **113**, and the registered margin **16.0pp → 19.0pp**, because a
  smaller n buys a wider margin and nothing else (see "Why 19pp").
- Alpha stays 0.0167: the three Q3 comparisons of Amendment 1 are retained. Retaining the third
  comparison costs 1pp of margin — 18pp would suffice for two comparisons at alpha 0.025 — and
  that cost was accepted deliberately while `kimi-code/k3` was still returning
  `403 Connection blocked by network allowlist`. The 403 has since stopped reproducing and
  dispatch is verified (see below), so the arm is expected to run. **If it nevertheless cannot,
  it is reported as not run, the 1pp is forfeit, and no substitute arm takes its place.**
- Four `cpp` records exist from the aborted full-set attempt (see §11 of
  `docs/BENCHMARKS.md`). `cpp` is outside the registered strata, so **zero observations exist
  for anything this plan governs** — that is what keeps this an amendment and not a post-hoc
  revision. Those four records will not be analysed and are not in the sweep's output file.

**What the subset costs, stated plainly.** At 19pp, a positive Q3 result reads "matches within
19 percentage points", which is close to vacuous for a coding benchmark — the interval admits
almost any plausible difference. The defensible value of this run is **Q2 estimation**: per-arm
pass rates with Wilson 95% CIs, whose half-width at n=113 is roughly ±9pp. Q3 is retained
because it was registered, not because 19pp is a strong test.

Status at lock time: **~$0.09 spent** (three Q1 config probes, four aborted-sweep `cpp`
invocations, and two kimi dispatch probes), **zero Anthropic quota consumed.** No observation
exists in any registered stratum (javascript, python, rust). Every number below was computed
from the committed code in `bench/aider_polyglot/analyze.py` before seeing any outcome.

`kimi-code/k3` dispatch was verified at lock time from the transcript, not from the model's
self-report: `{"type":"model_change","model":"kimi-code/k3","resolvedModelIsFallback":false}`
with `thinkingLevel: "max"`. The earlier `403 Connection blocked by network allowlist` no
longer reproduces.

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
  "usable_exercises": 113,
  "languages": ["javascript", "python", "rust"],
  "runs_per_exercise": 1,
  "mde_pp": 16.03,
  "min_discordant_pairs": 10,
  "length_control_band": [1.0, 4.0],
  "secondary_comparisons": [["ds-jspace", "sonnet-med"], ["ds-jspace", "ds-plain"], ["ds-plain", "opus-med"]],
  "multiplicity": "Bonferroni across the three pre-specified Q3 equivalence tests (alpha 0.0167 each, family-wise 0.05); the single Q2 McNemar is reported at alpha 0.05; all other comparisons are descriptive",
  "equivalence_margin_pp": 19.0,
  "equivalence_alpha": 0.0167,
  "equivalence_comparisons": [["ds-jspace", "opus-med"], ["ds-jspace", "sonnet-med"], ["ds-jspace", "kimi-max"]],
  "equivalence_underpowered_above_discordant_rate": 0.35
}
```

`sided: 2` and `alternative` coexist because the schema requires the key; with `sided: 2` the
direction in `alternative` carries no claim and `analyze.py` reports the two-sided p. `mde_pp`
is the achievable equivalence margin at alpha 0.0167 and p_discordant 0.25 for n=113
(16.03pp), not a superiority MDE.

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

- **n = 113**: every javascript (49), python (34) and rust (30) exercise in the Aider polyglot
  set. `cpp` and `go` are excluded by decision (Amendment 2); `java` has no working toolchain
  here. Within those three languages there is no subsampling — all 113 run.
- **k = 1 run** per (arm, exercise). Run-to-run variance is therefore inside the outcome
  rather than averaged out. This inflates discordance, and the registered margin below is
  chosen to hold at discordance up to 0.35 for exactly that reason.
- Quota cost, stated before authorisation is requested: **113 Opus invocations, 113 Sonnet
  invocations, and 113 Kimi k3 invocations** (both are subscription plans, $0 cash — a
  `cost_usd` of 0 on those arms is expected and is not a parsing failure). Cash cost of the
  three deepseek arms: **~$2.85** at the measured ~$0.0084 per invocation.

## Outcome and pairing

Primary outcome: binary pass/fail from the exercise's own test command, graded by
`run_tests()`. Pairing is by `task_id` (`lang/name`) across arms. Tasks carrying any skip or
dry-run record are excluded from every arm, as `aggregate_runs()` already enforces.

## Q3 — equivalence test, margin, and multiplicity

- Test: `tost_paired_binary(b, c, n, margin)` — TOST on the paired difference of pass
  proportions, McNemar-style SE, equivalence declared **only** when the whole confidence
  interval lies inside ±margin.
- **Registered margin: 19.0 percentage points.** Two-sided; applies to all three Q3
  comparisons.
- **Registered alpha: 0.0167 per comparison** (Bonferroni over the three pre-specified Q3
  comparisons, family-wise 0.05).
- Pre-specified Q3 comparisons, all three fixed now: `ds-jspace` vs `opus-med`, `ds-jspace` vs
  `sonnet-med`, and `ds-jspace` vs `kimi-max`. No other pair will be TOSTed.

### Why 19pp, and what each choice cost

Achievable margins at 80% power, from `smallest_margin_for_power()` in
`bench/aider_polyglot/analyze.py` (target 0.80, alpha 0.05, computed 2026-08-19):

| n | p_discordant=0.15 | 0.25 | 0.35 |
|---|---|---|---|
| 178 | 8.50pp | 10.97pp | 12.98pp |
| 120 | 10.35pp | 13.36pp | 15.80pp |
| 113 (registered) | 11.81pp | 15.25pp | 18.04pp |
| 90 | 11.95pp | 15.42pp | 18.25pp |
| 60 | 14.63pp | 18.89pp | 22.35pp |

At the registered alpha of 0.0167 the n=113 row becomes **12.42 / 16.03 / 18.97pp**.

**5pp was never reachable** — not even at n=178 and alpha 0.05, where the tightest achievable
margin is ~8.5pp and only if discordance is as low as 0.15.

Two decisions widened it from there, each costed before it was taken:

| decision | margin needed at pd 0.35 | power at 19pp (0.15/0.25/0.35) |
|---|---|---|
| n=178, 2 comparisons (α 0.025) | 14.37pp → registered 15.0pp | — |
| n=178, 3 comparisons (α 0.0167) | 15.12pp → registered 16.0pp | — |
| **n=113, 3 comparisons (α 0.0167)** | **18.97pp → registered 19.0pp** | **0.998 / 0.944 / 0.802** |

So the `kimi-max` arm cost 1pp and the three-language subset cost a further 3pp. At 19pp,
16.0pp would have yielded only 0.545 power at discordance 0.35 — an equivalence test that
cannot fail is worse than none, so the margin moved rather than the ceiling.

**Underpowered branch, registered in advance:** if observed discordance exceeds 0.35 the TOST
result is reported as **underpowered**, with the observed discordance and achieved power
printed and no equivalence claim made. `report_equivalence()` enforces this mechanically — it
is not left to a reader. The existing `min_discordant_pairs` floor is likewise a hard refusal
floor; below it, nothing is concluded.

19pp is a very wide margin, and this document does not pretend otherwise. "Matches within 19
percentage points" is the strongest honest form of a positive Q3 result at this n, and it will
be stated that way, with the margin in the sentence, or not stated at all. The run's real
contribution is Q2 estimation.

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

Added for this run, both enforced per invocation by `run.py` rather than left to a reader:

- **Dispatch verification.** Every invocation's transcript is read for `model_change.model` and
  `resolvedModelIsFallback`, plus `thinking_level_change.thinkingLevel`. A mismatch against the
  arm's registered triple, or any fallback, aborts the sweep. This is the exact failure that
  voided Round 3, and it is not detectable after the fact.
- **Usage verification.** A real invocation reporting `tokens_in == 0` aborts the sweep, since
  the length-control gate and the mean-`tokens_in` requirement are computed from that field.
  Note `cost_usd == 0` is *not* an error on the subscription arms (Opus, Sonnet, Kimi).

## Locked list of everything reported

1. Q2 descriptives: six arms, Wilson CIs, per language (javascript/python/rust),
   cost/latency/tokens.
2. Q2 confirmatory: McNemar `ds-jspace` vs `opus-med`.
3. Q3: TOST `ds-jspace` vs `opus-med`, `ds-jspace` vs `sonnet-med`, and `ds-jspace` vs
   `kimi-max`, margin 19.0pp, alpha 0.0167 each, with the underpowered branch above. If an arm
   could not run, its comparison is reported as **not run**.

Any analysis outside this list is exploratory and will be labelled exploratory.
