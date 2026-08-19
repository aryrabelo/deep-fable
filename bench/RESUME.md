# Resume here — the three questions that actually need answering

Written 2026-08-19 before a machine restart. Everything needed to continue is in this file.
Nothing paid has been run. No sweep exists.

Resume with:

```bash
cd ~/Sites/deep-fable && omp
# then: "read bench/RESUME.md and continue"
```

## State at handoff

| | |
|---|---|
| Branch / HEAD | `main` @ `525f2cd`, pushed, CI green |
| Tests | 44 passing (`uv run --with pytest python -m pytest tests/ -q`) |
| Money spent on benchmarks | $0 — every driver is dry-run verified only |
| Anthropic quota spent | none |

Built and committed: `bench/arms/` (three skill conditions incl. the token-matched placebo
skill), `bench/aider_polyglot/` (driver + McNemar/Wilcoxon analysis + length-control gate),
`bench/terminal_bench/` (omp adapter + 12-task subset), `bench/PREREGISTRATION.md` (locked
plan, mechanically enforced by `analyze.py`), `docs/BENCHMARKS.md` (the honest accounting).

## The reframing that supersedes the current design

The harness as built answers **"does the skill work?"** — arms `jspace` / `none` / `placebo`
on a fixed model. That is internal validity. The three questions actually wanted are
different, and two of them need arms the current driver cannot express:

**Q1. Does the `jspace` profile really use the model and thinking level it declares?**
Configuration question, free to answer, no sweep needed.

**Q2. deepseek+J-Space vs deepseek plain vs opus:medium — what are the numbers?**
Model-comparison question. Needs arms that vary the *model*, not just the skill.

**Q3. Which Anthropic model does deepseek+J-Space match?**
Equivalence question. This is the one with a statistical trap: **a non-significant
difference is not evidence of parity.** Claiming "matches" requires a pre-specified
equivalence margin and a TOST (two one-sided tests) showing the confidence interval falls
inside that margin. The existing `analyze.py` only does superiority testing, so it cannot
answer Q3 as written.

## What is already known about Q1

Both keys in `profile/config.yml` are real omp keys, verified for free:

```yaml
modelRoles:
  default: openrouter/deepseek/deepseek-v4-flash-0731
defaultThinkingLevel: max
```

`defaultThinkingLevel` appears at line 150 of the user's own working `~/.omp/agent/config.yml`
(value `auto` there), so the key name is correct and the profile is not a silent no-op on that
front. `modelRoles.default` likewise matches the live config's structure.

Still unverified: that a live session started with `--profile jspace` actually *reports* that
model and thinking level at runtime. Earlier in this work the model was confirmed to apply via
`omp --config profile/config.yml`, but `defaultThinkingLevel: max` was never confirmed
end-to-end. Cheapest honest check, roughly one cent:

```bash
omp --profile jspace -p "Reply with exactly two lines: your model id, and your thinking level."
```

`profile/config.yml` is byte-locked by an existing test. If the probe shows the thinking level
is not applied, that is a real finding — do **not** edit the file to make it pass; report it.

## Design change needed for Q2 and Q3

An arm is currently just a skill condition. It has to become a `(model, thinking, skill)`
triple. Proposed spec, to be locked in a second pre-registration before any run:

| Arm | Model | Thinking | Skill | Serves |
|---|---|---|---|---|
| `ds-jspace` | deepseek-v4-flash-0731 | max | jspace | Q2, Q3, and the existing Q0 |
| `ds-plain` | deepseek-v4-flash-0731 | max | none | Q2, Q3 |
| `ds-placebo` | deepseek-v4-flash-0731 | max | placebo | the skill-efficacy question only |
| `opus-med` | claude-opus-5 | medium | none | Q2, Q3 |
| `sonnet-med` | claude-sonnet-5 | medium | none | Q3 — needed to bracket where deepseek+J-Space lands |

Thinking level stays constant *within* the deepseek arms so the skill is the only thing that
varies between them. `opus-med` uses medium because that is what was asked for.

Two questions means two pre-registrations. Do not fold Q2/Q3 into
`bench/PREREGISTRATION.md` — that document is locked for the skill-efficacy question and
editing it after the fact voids it. Write `bench/PREREGISTRATION-MODELS.md` instead.

## The cost structure is asymmetric, and quota is the scarce resource

| Arm | Unit cost | 178 exercises × 1 run |
|---|---|---|
| deepseek arms (3 of them) | per token, OpenRouter | ~$2 total for all three |
| `opus-med` | subscription quota, $0 in cash | 178 Opus invocations |
| `sonnet-med` | subscription quota, $0 in cash | 178 Sonnet invocations |

Dollars are not the constraint; Anthropic quota is. Decide before running whether the
Anthropic arms run on all 178 exercises or on a pre-registered stratified subsample (stratify
by language, since exercise difficulty varies sharply across the six). A subsample costs
power, and the prereg must state the resulting detectable margin rather than discovering it
afterwards.

## Statistics that must be added before Q3 can be answered

1. **TOST for equivalence**, paired binary outcomes, with a pre-specified margin. Implement
   stdlib-only alongside the existing exact McNemar.
2. **Do not pick the margin by taste.** Compute the smallest margin for which n=178 (or the
   chosen subsample size) reaches 80% power, and pre-register *that*. Equivalence testing
   needs more n than superiority testing for the same margin, so 5pp may well be out of
   reach at this n — if it is, say so and register the achievable margin instead.
3. **Report descriptives for Q2 regardless**: per-arm pass rate with Wilson 95% CIs, per
   language, plus mean `tokens_in`, latency and cost per arm. Q2 asks for numbers, and
   honest numbers with intervals are the answer even where no test is significant.
4. Keep every existing guard: the discordant-pair floor, the length-control gate (which
   applies to the `ds-jspace` vs `ds-placebo` pair only), and the refusal to analyze without
   a parseable plan.

## Order of work when resuming

1. Answer Q1 with the one-line probe above. Report the result; if the thinking level does not
   apply, that is a finding about the profile, not a test to fix.
2. Generalise arms to `(model, thinking, skill)` triples in `bench/arms/arms.py` and
   `bench/aider_polyglot/run.py`. Keep the existing three arm names working so
   `bench/PREREGISTRATION.md` and the 44 tests stay valid.
3. Add TOST plus the Wilson-CI descriptive report to `analyze.py`.
4. Compute the achievable equivalence margin at the chosen n; write
   `bench/PREREGISTRATION-MODELS.md` and lock it.
5. Only then ask for authorisation to spend, with the quota cost stated per arm.

## Standing constraint

No paid model call, and no Anthropic quota consumption, without explicit authorisation for
that specific run. Dry-run everything first. A published claim must cite the pre-registration
hash `analyze.py` prints, the discordant-pair count, and mean `tokens_in` per arm, or it does
not count under §7 of `docs/BENCHMARKS.md`.
