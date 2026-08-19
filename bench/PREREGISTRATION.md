# Pre-registration — J-Space vs. placebo on the Aider polyglot set

This plan is locked before any sweep runs and before any result exists. It is written for a
reader who suspects the opposite — that the analysis choices below were picked *after*
looking at the numbers, to make a result significant that otherwise wouldn't be. Every
number in this document was computed and verified by hand before `bench/aider_polyglot/run.py`
was ever invoked against a real model. `analyze.py` reads the json block below and refuses to
print a primary verdict for any comparison, sidedness, or exercise count that doesn't match it
exactly — the enforcement is mechanical, not a promise kept by memory.

## Hypothesis

The J-Space skill raises the pass rate on the Aider polyglot exercise set relative to a
token-matched placebo addendum, when both are compared against the same model on the same
paired exercises.

## The locked plan (machine-readable)

`bench/aider_polyglot/analyze.py` parses this block and enforces it. Do not edit it after the
sweep starts; a changed plan after data exists is not a pre-registration.

```json
{
  "primary_comparison": ["jspace", "placebo"],
  "sided": 1,
  "alternative": "jspace > placebo",
  "alpha": 0.05,
  "power": 0.80,
  "expected_discordant_rate": 0.25,
  "usable_exercises": 178,
  "runs_per_exercise": 3,
  "mde_pp": 9.3,
  "min_discordant_pairs": 10,
  "length_control_band": [1.0, 4.0],
  "secondary_comparisons": [["jspace", "none"], ["placebo", "none"]],
  "multiplicity": "none applied to the primary; secondaries are descriptive and reported without inferential claims"
}
```

## Why each decision was made — before seeing data

**Why `jspace` vs. `placebo` is the primary, not `jspace` vs. `none`.** `none` has no
system-prompt addendum at all, so a `jspace`-vs-`none` gap is consistent with two different
explanations that cannot be told apart after the fact: "the skill's content helps" or "any
addendum of that length helps, content aside" (Pfau, Merrill & Bowman 2024,
["Let's Think Dot by Dot"](https://arxiv.org/abs/2404.15758), show meaningless filler tokens
alone can move task performance). `placebo` is token-matched to the real intervention and
carries no reasoning-discipline content, so `jspace` vs. `placebo` is the one comparison that
isolates the skill's content from its length. `jspace`-vs-`none` and `placebo`-vs-`none`
remain in the plan as secondary, descriptive comparisons — useful context, never a claim.

**Why one-sided is defensible here, and what it costs.** The claim under test is directional:
the upstream report claims J-Space *helps*, not merely that it *differs*. A one-sided test
matches the actual question being asked and recovers meaningfully more power at fixed n than
a two-sided test would, which is the entire reason this plan can use 178 exercises instead of
requiring the missing 47 Java exercises to reach 225. That power is not free. **A one-sided
test toward `jspace > placebo` cannot claim harm.** If the primary comparison comes out
negative — placebo outperforming jspace — the correct output is **no claim**, not a flipped
hypothesis, not a "well, actually it hurts" write-up, and not a post-hoc switch to a two-sided
test to salvage a headline. Choosing the direction after seeing which way the data leans is
exactly the maneuver a pre-registration exists to block. This document commits, before any
data exists, to publishing a null result as a null result if the sign runs the wrong way.

**Why only one comparison is inferential.** Running `jspace`-vs-`placebo`,
`jspace`-vs-`none`, and `placebo`-vs-`none` and treating all three as independent hypothesis
tests would require a multiplicity correction (e.g. Bonferroni), and a two-comparison
correction on the one-sided design pushes the minimum detectable effect back up to 10.5pp —
throwing away the exact gain the one-sided design bought. This plan avoids that trade by
declaring, in writing, that exactly one comparison (`jspace` vs. `placebo`) carries an
inferential claim; the other two are reported alongside it as descriptive numbers with no
p-value interpreted as a test result. That is a real constraint: it means a striking-looking
secondary number does not get treated as a test result, however striking it looks.

## Power arithmetic

All rows hold α=0.05, power=0.80, and an expected discordant rate of 0.25 (McNemar's test on
paired pass/fail outcomes; see `docs/BENCHMARKS.md` §3 for the underlying formula). Minimum
detectable effect (MDE) is the smallest jspace-vs-placebo pass-rate gap the design can
reliably distinguish from noise at that exercise count and sidedness.

| Design | Exercises | Comparisons | MDE at n |
|---|---|---|---|
| Two-sided, one primary | 225 | 1 | **9.3pp** |
| Two-sided, one primary | 178 | 1 | 10.5pp |
| **One-sided, one primary (this plan)** | **178** | **1** | **9.3pp** |
| One-sided, two comparisons Bonferroni-corrected | 178 | 2 | 10.5pp |

| Target MDE | Exercises needed, two-sided | Exercises needed, one-sided | Exercises needed, one-sided + two corrected comparisons |
|---|---|---|---|
| 10pp | 196 | 155 | 196 |

**Conclusion.** One-sided plus exactly one pre-registered primary comparison makes 178
exercises statistically equivalent to 225 exercises tested two-sided (9.3pp MDE both ways).
This equivalence is legitimate *only* because both decisions — the direction and the single
primary — are written down here, before any sweep has run and before any pass/fail record
exists. Made after seeing results, either decision would be p-hacking with extra steps; made
before, they are ordinary, defensible design choices that happen to close the gap the missing
47 Java exercises would otherwise leave open.

## Stopping rule

The sweep runs exactly once: all 178 usable exercises (per
`bench/aider_polyglot/README.md`'s toolchain probe — Java unavailable on this machine), 3
arms (`jspace`, `none`, `placebo`), 3 runs per exercise per arm. The analysis
(`bench/aider_polyglot/analyze.py` against this plan) is run exactly once against the
resulting results file(s).

- No peeking at partial results and extending the sweep if the trend looks weak.
- No dropping exercises after seeing which ones the arms disagree on.
- No swapping the primary comparison, or the sidedness, after seeing the sign of the result.
- A failed length-control gate (`tokens_in` ratio outside the `[1.0, 4.0]` band, or
  unverified/zero token capture) **invalidates the primary comparison**. It is reported as
  `LENGTH CONTROL FAILED` or `UNVERIFIED`, not worked around, not re-run with a different
  token-counting method chosen after the fact, and not silently dropped from the report.

## What would falsify the claim

The claim is falsified — or more precisely, not supported — if the `jspace`-vs-`placebo`
McNemar test on the 178-exercise, 3-run sweep does not reach significance at α=0.05
one-sided, **or** if the discordant pair count falls below `min_discordant_pairs` (10),
in which case the study reports "underpowered," not "no effect." A p-value ≥0.05 with
adequate discordant pairs means: no measurable effect at this sample size.

This is a **bounded negative result**, not proof that J-Space has no effect. This design
cannot see an effect smaller than roughly 9.3 percentage points; a true effect anywhere below
that threshold would produce exactly this outcome even if it were real. "No measurable
effect" here means "no effect of at least ~9.3pp was detected," never "the skill does
nothing."

## Sign-off

Locked: 2026-08-19, before any sweep ran and before any result existed.

This document deliberately contains no hash of itself and no reference to the commit that
carries it — both would be circular, since neither value exists until after the bytes are
final. Verify the lock externally instead:

```bash
# the commit that introduced this plan, and its date
git log --diff-filter=A --format='%H %ad' -- bench/PREREGISTRATION.md

# the hash analyze.py will print, computed over the current bytes
shasum -a 256 bench/PREREGISTRATION.md
```

Compare that commit date against the timestamps in whichever `bench/results/*.jsonl` the
analysis consumed. If the plan's commit is later than the results it governs, it is not a
pre-registration and every claim resting on it is void. Any published verdict must cite the
sha256 that `analyze.py` printed, so the plan version can be matched to the bytes above.
