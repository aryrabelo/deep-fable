# Benchmarks — what we know, what we don't, and how not to fool ourselves

This document exists so nobody — including the people who wrote this repo — can point at
`model-eval/` and claim it says something it doesn't. It is the single place that states,
plainly, what has been measured, what the upstream J-Space report claims, why our current
budget cannot adjudicate that claim, and the design that will let us find out honestly.

## 1. What we have measured so far — and what it is worth

Three rounds ran in `model-eval/`. None of them measured whether the J-Space skill changes
coding outcomes.

**Round 1 — ceiling effect, zero discriminative signal.** 5 models × effort levels × 6
hand-written, fully-specified, single-file maintenance tasks × 3 runs = 234 runs.
`model-eval/REPORT.md` states the result directly:

> **234/234 PASS.** Every model, every effort level, every task, every run.
> Wilson 95% CI per cell: [0.82, 1.00] — indistinguishable.

Every cell passed everything. An item every model passes carries zero bits of comparative
information — that is the textbook definition of a ceiling effect. No model, effort level,
or (by construction, since no skill was in play) skill condition could have looked different
on this task set even if one genuinely were better.

**Round 3 — verdict is UNREPRODUCED.** `model-eval/round3/REPORT.md` reports a narrow blind
human A/B between `opus-medium` and `deepseek-max` on a five-stage landing-page build, judge
seeing only sealed labels:

> **Verdict: X (opus-medium) wins, narrowly** — judge's words: "quase um empate mas a X
> tá melhor".

That verdict does not survive the methodology check `model-eval/round4/REPORT.md` ran on it.
Round 3 pinned models via `agent(prompt, { model })` in the JS eval kernel, and Round 4
found that pin does nothing:

> Round 3 pinned models with `agent(prompt, { model })` in the JS eval kernel. **That option
> is ignored.** Probes on 2026-08-19: ... Dispatches pinned to opus and to deepseek, asked
> to self-report their model id, both answered `claude-sonnet-5` — the default subagent
> model.

Both "cells" in Round 3 were most likely the same model (the session default,
`claude-sonnet-5`), running the same prompt twice. The 12/12-both objective score is
consistent with that — it never discriminated either — and the "narrow win" is now
unattributable to any model difference, let alone a skill difference. Nothing in Round 3
should be cited as a finding.

**Round 4 — real discrimination, but it answered adapter-integration questions, not
skill-efficacy questions.** `model-eval/round4/REPORT.md` opens by naming exactly what it is:

> First round in this series that **discriminates**. ... The workload was real work: the
> four unverified items blocking the OpenCode / Cursor / Gemini CLI adapters in
> `ROADMAP.md` (see `BRIEF.md`).

The task was factual research with source-verification grading — "does Gemini CLI load
skills without an extension", "does Cursor allow a repo-committed model override" — dispatched
with `--no-skills` on both cells. It is a genuinely useful, correctly-pinned (via a real
`omp --model` CLI process, verified against a bogus model id erroring) model comparison on
research quality. It has nothing to say about J-Space, because J-Space was explicitly
disabled in both cells and the task class (fact-finding, not coding) is not what the skill
targets.

**Conclusion.** Read together, these three rounds establish a model-cost/latency picture and
one useful research-quality finding — they establish nothing about the skill. **This repo
currently has zero evidence that the J-Space skill changes coding outcomes.** Any claim to
the contrary made anywhere else in this repo (README, ROADMAP, commit messages) is not
backed by `model-eval/`.

## 2. The upstream claim

The upstream capability report
([Tiger3807861189/DeepSeek-V4-J-Space-Capability-Realization-Report](https://github.com/Tiger3807861189/DeepSeek-V4-J-Space-Capability-Realization-Report))
publishes the following table. It is reproduced here faithfully, figure for figure.

> **UPSTREAM SELF-REPORTED, NOT REPRODUCED HERE.** No run in this repo generated any number
> below.

| Benchmark | V4-Flash-0731 | V4-Flash+J-Space | V4-Pro-0813 | V4-Pro+J-Space | GLM-5.3 | Kimi-K3 | Opus-4.6 | Fable 5 w/fallback |
|---|---|---|---|---|---|---|---|---|
| Humanity's Last Exam (no tools) | 37.8 | 45.5 | 42.7 | 48.0 | — | 43.5 | 49.8 | 53.3 |
| Humanity's Last Exam (with tools) | 51.5 | 60.6 | 60.0 | 67.7 | 62.5 | 56.0 | 57.9 | 63.0 |
| Terminal Bench 2.1 (agentic terminal coding) | 82.7 | 87.1 | 87.9 | 90.1 | 88.2 | 88.3 | 85.0 | 88.0 |
| NL2Repo (repo-level code generation) | 54.2 | 70.2 | 61.5 | 73.4 | 58.0 | 58.0 | 69.7 | — |
| CyberGym (cybersecurity agents) | 76.7 | 81.7 | 83.3 | 86.8 | 84.5 | 80.0 | 78.3 | 83.1 |
| DeepSWE (agentic coding) | 54.4 | 67.4 | 62.7 | 72.0 | 66.9 | 67.5 | 58.0 | 70.0 |
| Toolathlon-Verified (tool-use agents) | 70.3 | 77.7 | 74.1 | 79.5 | 73.0 | 76.5 | 76.2 | 77.9 |
| Agents' Last Exam (frontier agentic tasks) | 25.2 | 30.1 | 25.7 | 30.3 | 28.5 | 27.6 | 25.7 | 23.8 |
| AutomationBench Public (automation tasks) | 25.1 | 31.7 | 31.8 | 38.2 | 48.2 | 30.8 | 27.2 | 29.1 |

`—` = not reported in the upstream table.

### Implied J-Space deltas

Only two columns form a with/without pair on the same base model: `V4-Flash-0731` vs.
`V4-Flash+J-Space`, and `V4-Pro-0813` vs. `V4-Pro+J-Space`. Every other column is a
different model entirely and cannot be attributed to the skill.

| Benchmark | Δ V4-Flash (+J-Space) | Δ V4-Pro (+J-Space) |
|---|---|---|
| HLE (no tools) | +7.7 | +5.3 |
| HLE (with tools) | +9.1 | +7.7 |
| Terminal Bench 2.1 | +4.4 | +2.2 |
| NL2Repo | **+16.0** | +11.9 |
| CyberGym | +5.0 | +3.5 |
| DeepSWE | **+13.0** | +9.3 |
| Toolathlon-Verified | +7.4 | +5.4 |
| Agents' Last Exam | +4.9 | +4.6 |
| AutomationBench Public | +6.6 | +6.4 |

The largest implied deltas are **NL2Repo +16.0pp** and **DeepSWE +13.0pp**, both on
V4-Flash — the two benchmarks closest to what this repo actually does (repo-level code
generation, agentic coding). The full spread across all nine rows is +2.2pp to +16.0pp; the
often-quoted "+7 to +16pp" headline is the top half of that spread, not the whole of it.

### What the table omits, and what each omission costs a reader

| Omission | What it costs |
|---|---|
| Harness/scaffold identity | Cannot tell whether the "+J-Space" column changed only the system prompt, or also changed tool access, retries, or agent loop — any of which alone can move a score. |
| Seeds | Zero reproducibility. A different seed on the same setup can move pass rates by points at temperature 0 (see §3/§7 non-determinism note). |
| Number of runs per cell | If n=1 per cell, every number above is a single noisy draw, not an estimate. No error bars anywhere in the table imply n=1 throughout. |
| Confidence intervals | Without them, +2.2pp and +16.0pp cannot be told apart from noise. A number without an interval is not evidence, it is an anecdote with more decimal places. |
| Same prompt scaffold in both arms | If the "+J-Space" arm also got a different tool loop or extra retries, the delta measures more than the skill's content. |
| Length-matched control | Without one, every delta above is consistent with "a longer prompt helps" rather than "J-Space's content helps" — see §5. |

## 3. Why a 15-task pilot cannot test that claim

Paired binary pass/fail outcomes across two arms on the same task are compared with
McNemar's test, not a two-proportion z-test — see `model-eval/METHODOLOGY.md` Rule 3 for
why the independence assumption is wrong here. McNemar's power depends only on the
**discordant pairs** (tasks where the arms disagree), and sample-size planning for it uses:

```
n ≈ (z_{α/2} + z_β)² · (p01 + p10) / (p10 − p01)²
```

where `p01 + p10` is the discordant rate (fraction of paired tasks where the two arms
disagree) and `p10 − p01` is the effect you want to detect (the difference in who wins those
discordant pairs).

Plugging in a conventional design — α=0.05 two-sided (z_{α/2}=1.96), power=0.80
(z_β=0.84), a discordant rate of 0.25 (a quarter of tasks split the two arms), and a 10
percentage-point effect to detect:

```
n ≈ (1.96 + 0.84)² · 0.25 / (0.10)²
  ≈ 7.84 · 0.25 / 0.01
  ≈ 196
```

**About 196 paired tasks** are needed to reliably detect a 10pp effect at these settings —
holding the discordant rate at 0.25 and solving for the detectable effect at smaller n
instead:

| n (paired tasks) | Smallest reliably detectable effect |
|---|---|
| 15 | ~36pp |
| 50 | ~20pp |
| 100 | ~14pp |
| 225 | ~9.3pp |

At n=15 — the size of a quick pilot — the study can only reliably see an effect the size of
"more than a third of the tasks flip," which is larger than any single delta in the
upstream table (§2's largest is +16.0pp). A 10–15 task pilot is real infrastructure work: it
validates the harness end to end and calibrates run cost and latency. **It cannot confirm or
refute a 7–16pp claim** — the study is underpowered by roughly an order of magnitude for
that effect size. Any future report from this repo that runs a 10–20 task pilot and reports
it as an efficacy verdict is making the same mistake as the upstream table: a number with no
attached power analysis, presented as if it settled the question.

## 4. Benchmark decision matrix

| Benchmark | Task count | What it measures | Agent-agnostic | Setup cost | Money/run | Power at our budget | Verdict |
|---|---|---|---|---|---|---|---|
| **Terminal-Bench 2.0** | 89 | End-to-end sandboxed terminal/agentic tasks, binary pass/fail | Yes — `AbstractInstalledAgent` base class; maintained adapters for claude_code, codex, cursor_cli, gemini_cli, opencode | ~40GB Docker | ~$1–$100/full run (model-dependent) | n=15 pilot → ~36pp detectable; full 89 → still only ~20pp | **Keep — realism check.** Run 10–15 tasks to validate Docker + keys, not to claim an effect. |
| **Aider polyglot** | 225 | Isolated coding exercises across 6 languages, one shared Docker image, seconds/exercise | Needs a small custom per-exercise driver (harness drives Aider as a library natively; a driver script gets any CLI in) | One shared image, far lighter than the other two | Seconds/exercise — cheapest of the three | Full 225 → ~9.3pp detectable, the only benchmark on this list that reaches useful power on a realistic budget | **Efficacy vehicle.** The only benchmark here cheap enough to run at the n that makes the McNemar test meaningful. |
| **SWE-bench Verified** | 500 (Lite: 300) | Real historical GitHub issue → patch, decoupled inference/grading via `predictions.json` unified diffs | Yes — any agent that can `git diff` a checkout qualifies | ~120GB Docker; ARM experimental, x86_64 recommended | Not sized in our research; scales with instance count and model, likely comparable order of magnitude to Terminal-Bench per instance | Even a 100-instance subset → ~14pp detectable | **Deferred.** Right shape, best realism, but the Docker footprint (~120GB) is the blocker at our current budget. Revisit with x86_64 capacity. |
| BigCodeBench | — (not sized here) | Single-function pass@1 | Yes technically, but no agent seam | Not sized | Not sized | N/A | **Ruled out.** Wrong framing — function-level, not agentic; doesn't exercise tool use or multi-step work. |
| LiveCodeBench | — (not sized here) | Single-function pass@1, date-tagged releases | Yes technically, but no agent seam | Not sized | Not sized | N/A | **Ruled out.** Contamination-resistant by design, but same framing problem as BigCodeBench — no agent loop to test. |
| RepoBench | — (not sized here) | Fill-in-the-middle code completion | No agent seam | Not sized | Not sized | N/A | **Ruled out.** Not agentic; leaderboard effectively dead. |
| Commit0 | — (not sized here) | Library re-implementation from spec | Right shape, wrong lock-in | Heavy per-library images | Not sized | N/A | **Ruled out.** Hard-wired to Aider's own harness; would need a fork to use with other agents. |
| SWE-bench Multimodal | — (not sized here) | Visual/multimodal repo tasks | No — private cloud grading | Not sized | Not sized | N/A | **Ruled out.** Grading isn't reproducible outside the vendor's cloud. |

**Recommendation carried forward:** Aider polyglot (225 paired exercises) is the efficacy
vehicle, because it is the only benchmark on this list that reaches usable statistical power
(≈9.3pp detectable at full scale) within a realistic Docker/compute/time budget.
Terminal-Bench is the realism check — it has maintained adapters for five of our six target
agents and zero glue code, but its cost profile keeps any run at our budget underpowered for
an efficacy claim, so it stays a calibration/sanity tool, not a verdict source. SWE-bench
Verified is deferred on its ~120GB Docker footprint; it is the best-shaped benchmark for real
repo work and should be revisited if x86_64 Docker capacity becomes available.

## 5. The three-arm design, and why the placebo is mandatory

Any experiment testing whether J-Space changes outcomes must run three arms per task, paired
within the same model:

| arm | condition |
|---|---|
| `jspace` | model + task, J-Space's system-prompt addendum loaded |
| `none` | model + task, no addendum |
| `placebo` | model + task, a length-matched filler addendum with no reasoning-discipline content |

The placebo is not an optional nicety. Pfau, Merrill, and Bowman,
["Let's Think Dot by Dot: Hidden Computation in Transformer Language Models"](https://arxiv.org/abs/2404.15758)
(arXiv:2404.15758, submitted April 2024, published at COLM 2024) show that transformers can
solve algorithmic tasks they otherwise cannot solve immediately by being given **meaningless
filler tokens** (literally `......`) in place of a real chain of thought — extra token
budget and extra forward-pass compute alone, with zero semantic content, can produce a
measurable gain. That means a `jspace` arm beating a `none` arm is consistent with two very
different explanations: "the skill's content helps" or "a longer prompt / more thinking
budget helps, regardless of content." Only a length-matched, content-free placebo arm can
tell those apart. `jspace` beating `none` AND `placebo` supports a content-driven effect;
`jspace` beating `none` but not `placebo` means the effect is prompt length, not J-Space.

Concretely, for this repo's harness (`ARMS = ("jspace", "none", "placebo")` in
`bench/arms/arms.py`, per the shared driver contract):

- The placebo text must be **token-matched to `arm_prompt("jspace")` within 5%**, using the
  same deterministic token-count approximation the harness uses for all three arms.
- The placebo must contain **no reasoning-discipline instruction** — no "think step by
  step," no structured-workspace framing, no instruction that could itself function as a
  scaffold. Filler that reads as content defeats the control.
- Arm order must be **counterbalanced** across tasks (not always `jspace` first) so ordering
  effects don't confound the comparison, and injected at the **same position** in every arm
  so primacy/recency isn't a hidden variable.
- Results are **paired per task**: the same task, run under all three arms (ideally with the
  same model and the same n runs per arm), feeds the same row of the results JSONL so
  McNemar's test has real pairs to compare.

### Matching the right length

The intervention is not one size. Measured with a deterministic token-count proxy on this
repo's own files:

| Artifact | Tokens |
|---|---|
| `profile/APPEND_SYSTEM.md` (the always-on snippet, `arm_prompt("jspace")`'s fixed return value) | 60 |
| `.omp/skills/j-space/SKILL.md` (loaded when the agent actually fires the skill) | 3,834 |
| `modules/` (9 files, loaded selectively by routing) | 22,122 |
| `references/` (3 files, loaded selectively by routing) | 16,719 |
| Full skill payload (SKILL.md + every module + every reference) | 42,675 |

A placebo matched only to the 60-token always-on snippet — which is what `arm_prompt`
returns per the fixed contract, and all the harness can match a priori — controls the static
addendum but not the real intervention. `APPEND_SYSTEM.md` doesn't contain the skill; it
tells the agent to read `skill://j-space`, which is a tool call the agent makes mid-run. What
actually enters context on a `jspace`-arm run is the addendum **plus** `SKILL.md` **plus**
whichever modules and references the skill routes to for that specific task — and routing is
dynamic, so the total is different on every run and cannot be pinned down before the run
starts.

The design therefore does not try to pre-match a fixed placebo to a moving target. Instead:
every driver records `tokens_in` per run in the results schema (already part of the shared
schema in this repo's contract), and the analysis reports **mean `tokens_in` per arm**
alongside every pass-rate comparison. A large `jspace`-vs-`placebo` gap in mean `tokens_in`
is not a footnote — it is a **failed length control**, and any pass-rate delta measured under
a failed control must be reported as unattributable to content, not as a result.

Threshold this repo treats as defensible: the placebo text itself should be enlarged to match
**`SKILL.md`'s 3,834 tokens**, not the 60-token snippet, because `SKILL.md` is the floor of
the intervention — it loads on every single run the moment the skill fires, before any
routing decision — while the 60-token snippet controls under 2% of that floor (1.6%) and
the routed modules/references remain uncontrollable a priori by design.

## 6. Vibe coding: what it is and how to test it honestly

Nothing in §4's benchmark list measures "vibe coding" — the subjective sense that one
agent's output on an open-ended build (a landing page, a small app, a creative artifact) is
better crafted, better designed, or more pleasant to use than another's. Terminal-Bench,
SWE-bench, and Aider polyglot all score closed tasks against a deterministic pass/fail
grader; vibe quality has no ground truth to check against, because the task itself doesn't
specify a single correct output. It is a preference judgment, and preference judgments need
a different experimental design than pass/fail benchmarks — not a looser one, a different
one.

**A runnable design:**

1. **Fixed set of open-ended build prompts**, written before any run (e.g. "build a landing
   page for X," "prototype a small tool that does Y"), identical text across arms except for
   the system-prompt addendum under test.
2. **Two arms produce artifacts** — e.g. `jspace` vs. `placebo` (never `jspace` vs. `none`
   alone; see §5, the placebo is what makes a preference result attributable to content
   rather than length).
3. **Blind pairwise comparison.** The judge sees two unlabeled artifacts (screenshot,
   rendered page, or the code itself) and picks a preference or declares a tie. The judge
   must not know which arm produced which artifact — label assignment sealed before viewing,
   exactly as `model-eval/round3/` did (`.blind-assignment.json`).
4. **A second judge for agreement.** Run the same blind comparison past a second human or a
   different model, and report the two judges' agreement rate. A single judge's preference is
   an anecdote; agreement between independent judges is evidence.
5. **Statistics over paired preferences.** With ties allowed and preference strength
   irrelevant, a simple **sign test** over paired win/loss/tie counts is enough; if a graded
   preference scale is collected instead of a binary win/loss, use the **Wilcoxon
   signed-rank test** on the paired differences.

**Failure modes that make most vibe evals worthless — and this design's defense against
each:**

| Failure mode | Why it invalidates the result | Defense here |
|---|---|---|
| Judge sees the arm label | Judges rate the *label* they already have an opinion about, not the artifact | Sealed blind assignment, labels revealed only after judging |
| One arm gets a longer prompt | Confounds "better content" with "more instruction," exactly §5's Pfau et al. problem | Same token-matched placebo control as the pass/fail arms |
| Position bias in the pair | Judges systematically favor whichever artifact they see first/left | Counterbalance left/right position per pair, same as arm-order counterbalancing in §5 |
| Same model judging its own output | Documented self-enhancement bias — a model rates its own style favorably ([Zheng et al., 2023](https://arxiv.org/abs/2306.05685)) | Judge is never the model that produced either artifact under comparison; use a human or a third model |

## 7. Standing rules for any benchmark claim in this repo

Before any future round in this repo is allowed to make a claim ("the skill helps," "model A
beats model B," "the placebo control failed"), it must satisfy every line below:

- [ ] **Name the harness and version.** Which benchmark, which release/commit, which driver.
- [ ] **Publish seeds and run counts.** How many runs per cell, and the seed(s) used, so the
      run is reproducible and its variance is visible.
- [ ] **Report confidence intervals or exact-test p-values.** Wilson intervals for a single
      arm's raw rate, McNemar (exact when discordant pairs are few) for paired comparisons —
      never a bare percentage with no uncertainty attached.
- [ ] **Include the length-matched control.** Any skill/prompt-content claim without a
      `placebo` arm (§5) is a prompt-length claim wearing a content claim's clothes.
- [ ] **Publish the raw results JSONL.** One record per (task, arm, run) under
      `bench/results/`, so anyone can recompute the statistics independently.
- [ ] **State the detectable effect size given n, before running.** §3's table, or the
      equivalent calculation for the design at hand, computed and written down *before* the
      run — not fitted to the result afterward.
- [ ] **Publish mean input tokens per arm.** Report mean `tokens_in` for `jspace`, `none`,
      and `placebo` alongside every pass-rate claim, so a reader can see whether the length
      control (§5, "Matching the right length") actually held for that run.
- [ ] **Cite the pre-registration hash.** Any claim about the `jspace`-vs-`placebo`
      comparison must quote the hash of the locked plan that `analyze.py` prints alongside
      its verdict, so a reader can confirm the plan being cited is the one that was written
      down before the sweep ran, not a later edit.

## 8. Pre-registration: the locked analysis plan for the 178-exercise sweep

The Aider polyglot sweep runs on 178 usable exercises (Java toolchain unavailable on this
machine — see `bench/aider_polyglot/README.md`) instead of the full 225. `bench/PREREGISTRATION.md`
is the locked plan that makes 178 exercises statistically equivalent to 225 run two-sided,
written and committed before any sweep data exists. The full justification, power arithmetic,
stopping rule, and falsification criteria live there; this section is the pointer and a short
summary.

| Field | Locked value |
|---|---|
| Primary comparison | `jspace` vs. `placebo` (the comparison that isolates skill content from prompt length) |
| Sidedness | One-sided, `jspace > placebo` — cannot claim harm |
| α / power | 0.05 / 0.80 |
| Expected discordant rate | 0.25 |
| Usable exercises | 178 |
| Runs per exercise | 3 |
| Minimum detectable effect | 9.3pp — equal to 225 exercises run two-sided |
| Minimum discordant pairs | 10 |
| Length-control band | 1.0x–4.0x mean `tokens_in` ratio |
| Secondary comparisons | `jspace` vs. `none`, `placebo` vs. `none` — descriptive only, no inferential claim |
| Multiplicity correction | None on the primary; the one-primary constraint is what makes that legitimate |

See `bench/PREREGISTRATION.md` for the full prose justification of each decision, the four-row
power table this summary condenses, the no-peeking stopping rule, and what outcome would count
as a falsifying (bounded) null result.

## 9. The model questions (Q2/Q3), and what n=178 actually buys

§8 governs the skill question on a fixed model. Two further questions — how
deepseek+J-Space compares to Opus/Sonnet at `medium` (Q2), and which Anthropic model it
*matches* (Q3) — need arms that vary the model, so an arm is now a `(model, thinking, skill)`
triple (`ARM_SPECS` in `bench/arms/arms.py`): `ds-jspace`, `ds-plain`, `ds-placebo`,
`opus-med`, `sonnet-med`. `bench/PREREGISTRATION-MODELS.md` is their locked plan.
`bench/PREREGISTRATION.md` was not touched — editing a locked plan to cover new questions
voids it.

**Q3 is an equivalence question, and superiority tests cannot answer it.** A non-significant
McNemar is not evidence of parity. Equivalence requires a margin fixed in advance and a TOST
whose whole confidence interval falls inside it (`tost_paired_binary()` in `analyze.py`).

**The margin this design can support is wide.** From `smallest_margin_for_power()` at 80%
power, α = 0.05:

| n | p_discordant = 0.15 | 0.25 | 0.35 |
|---|---|---|---|
| 178 | 8.50pp | 10.97pp | 12.98pp |
| 120 | 10.35pp | 13.36pp | 15.80pp |
| 90 | 11.95pp | 15.42pp | 18.25pp |
| 60 | 14.63pp | 18.89pp | 22.35pp |

A 5pp margin is **not reachable** at n=178 at any plausible discordance rate. The registered
margin is therefore **15.0pp at α = 0.025** (Bonferroni over the two Q3 comparisons), which
gives power 0.999 / 0.959 / 0.845 at discordance 0.15 / 0.25 / 0.35. Above a discordance of
0.35 the plan declares itself underpowered, and `report_equivalence()` enforces that
mechanically — it prints the achieved power and refuses the verdict rather than leaving the
judgement to a reader.

So the strongest honest positive Q3 result available here is "matches within 15 percentage
points", stated with the margin in the sentence. Anything tighter needs more exercises, not a
different test. Q2 is answered primarily by pass rates with Wilson 95% CIs per arm and per
language plus cost/latency/token means (`--descriptives`), with a single confirmatory
two-sided McNemar on `ds-jspace` vs `opus-med`.

Cost, measured rather than projected (2026-08-19/20). The three deepseek arms over the
n=113 javascript+python+rust subset cost **$4.36 cash** for 339 invocations — metered, and
the only metered provider in the ladder.

On the Anthropic arms `cost_usd` is **non-zero but notional**: `opus-med` records ~$1.64 per
invocation, and that figure is a list-price equivalent computed by the harness, not a
charge. The billing path was verified three ways: no `ANTHROPIC_API_KEY` in the environment,
`omp usage` reports Anthropic as subscription buckets (`5h`, `7d`), and a 3-unit Opus probe
moved the `5h` bucket from 1% to 3% — the spend came out of quota. Extrapolated, 113 Opus
units consume roughly 75 points of a 5-hour window (so ~3 windows, ~13h wall time) and up to
38 points of the weekly bucket. `kimi-max` records $0.000 and is plan-backed.

So a reader reconciling the JSONL against a credit-card statement must not sum `cost_usd`
across arms: it mixes real dollars (deepseek) with notional ones (Anthropic). Quota, not
dollars, is the binding constraint on the Anthropic arms, and it is why `runs_per_exercise`
is 1 here rather than §8's 3.

## 10. Q1 — the `jspace` profile does apply what it declares, and model self-reports are noise

Answered 2026-08-19, three deepseek probes, roughly $0.02 total.

**The configuration is applied.** `omp --profile jspace config get` reads the profile's
*effective* settings and is free:

| Query | `jspace` profile | default profile |
|---|---|---|
| `defaultThinkingLevel` | `max` | `auto` |
| `modelRoles` | `{"default":"openrouter/deepseek/deepseek-v4-flash-0731"}` | — |

So `profile/config.yml` is not a silent no-op on either key. It stays byte-locked; nothing was
edited to make this pass.

**But asking the model was worthless, and nearly produced a false finding.** The same probe —
"reply with your model id and your thinking level" — answered:

| Invocation | Self-reported thinking level | Actual |
|---|---|---|
| `--profile jspace` | `fast` | max |
| `--profile jspace --thinking max` | `minimum` | max |
| `--profile jspace --thinking off` | `default` | off |

Three runs, three different answers, none of them the truth, and the value moved in no
relation to the flag. The model id was reported correctly every time; the thinking level is
simply not something the model has access to. Read as a finding, the first probe would have
said "the profile fails to apply `max`" — the opposite of what the free config query shows.

**Rule this establishes:** verify harness configuration by querying the harness, never by
asking the model about itself. This is the same failure mode that voided Round 3 (§1), where
pinned dispatches self-reported the wrong model. Model self-report is admissible evidence
about nothing except the model id, and even that only corroboratively.

One fragility noted while checking: the installed profile at
`~/.omp/profiles/jspace/agent/config.yml` is a **copy**, not a symlink to `profile/config.yml`.
The two agree today on both keys. An edit to the repo file will not reach a live profile
without a reinstall, so any future claim about the profile must re-run the `config get` query
rather than cite the repo file.

## 11. The first sweep attempt was aborted after 5 minutes, and why that was right

The deepseek sweep (`ds-jspace`, `ds-plain`, `ds-placebo`) was launched 2026-08-19 and killed
after ~5 minutes and one completed record. That record is why:

```json
{"task_id":"cpp/all-your-base","arm":"ds-placebo","passed":false,"latency_s":248.65,
 "tokens_in":0,"cost_usd":0.0,
 "notes":"add_executable): Cannot find source file: work_test.cpp ..."}
```

Three harness bugs, none of them about any model:

**1. Every C++ exercise was unwinnable.** `make_scratch()` copied each exercise into a
directory literally named `work`. The upstream C++ `CMakeLists.txt` derives the project and
source filenames from the directory name:

```cmake
get_filename_component(exercise ${CMAKE_CURRENT_SOURCE_DIR} NAME)
```

so CMake demanded `work.cpp` / `work_test.cpp` and the build failed regardless of what the
agent wrote. All 29 C++ exercises would have scored `passed: false` for every arm — a harness
artifact indistinguishable, in the results file, from 29 genuine model failures. Fixed by
naming the working directory after the exercise (`work_dir()`), which is the layout upstream
exercises are known to work under for every language.

**2. Every usage figure was 0.** `_find_session_file()` globbed
`**/sessions/<slug>/*.jsonl`. The real layout is `<session_dir>/<timestamp>_<uuid>.jsonl` with
a `__advisor.jsonl` side-car — singular, no slug directory. The glob matched nothing, so
`invoke_omp()` took its "no transcript" branch and recorded `tokens_in=0, cost_usd=0.0` every
time. That silently destroys the length-control gate (§5) and the mean-`tokens_in` figure §7
requires for any claim. The docstring had flagged that path as unconfirmed `[INFERENCE]`; it
was wrong. Fixed and verified against the aborted run's own transcripts, which parse to real
figures (e.g. 318,026 input tokens / $0.0070 for one `ds-jspace` invocation).

**3. Nothing would have complained.** The driver wrote zero-usage rows without protest. It now
raises on the first real invocation that reports `tokens_in == 0`, keeping the scratch
directory for inspection, on the principle that a row which cannot support a claim is a
failure and not a datum.

**Cost correction.** Real per-invocation cost measured from those transcripts is ~$0.007–0.009,
so 534 deepseek invocations is **~$4.3, not the ~$2** estimated in §9 and
`bench/PREREGISTRATION-MODELS.md`. The estimate was wrong, not the plan; no registered
statistical parameter depends on it.

**What this says about the earlier rounds.** Bugs 1 and 2 were both *silent* — they produced a
well-formed results file full of plausible-looking failures and zeros. Had the sweep run its
full 9+ hours, the analysis would have reported a real McNemar test over data whose C++ stratum
was pure harness noise, and the length-control gate would have compared zero against zero and
passed. §7's checklist would not have caught it. The lesson is the one from Round 3 and from Q1
in §10, a third time: **the first real record of any sweep must be read by a human before the
rest are paid for.**

## 12. The headroom diagnostic — why the deepseek null is a real null, and why Opus/Kimi skill arms would be uninterpretable

Run 2026-08-20. Nine purposive units (six `opus-med`, three `kimi-max`), both arms **plain**
(`skill: none`), ~$0 cash and ~2 points of the Anthropic 5-hour bucket. Recorded outside
`bench/results/` because purposive selection cannot feed a pre-registered estimate; the
`--only` flag added for it says so in its own help text.

The n=113 deepseek sweep left 26 tasks where **all three** arms failed. Two rival readings of
that floor: broken toolchain, or difficulty beyond any model. Both are testable with a
reference model run plain, so three floor tasks were chosen to separate them —
`rust/acronym` (trivial; a floor here indicts the harness), `python/list-ops` (same test on an
independent toolchain), `rust/alphametics` (genuine combinatorial search; where a reasoning
skill should bite if it bites anywhere).

| task | ds-jspace | ds-plain | ds-placebo | opus-med | kimi-max |
|---|---|---|---|---|---|
| `rust/acronym` | fail | fail | fail | **pass** | **pass** |
| `python/list-ops` | fail | fail | fail | **pass** | **pass** |
| `rust/alphametics` | fail | fail | fail | **pass** | **pass** |

`opus-med` 6/6 (Wilson 95% [0.610, 1.000]), `kimi-max` 3/3 ([0.438, 1.000]). Under a true
reference rate of 0.50 the chance of 6/6 is 0.016.

Both rival readings die. The rust toolchain works, so deepseek's 16 rust floor tasks are model
weakness and not a harness bug; and the hardest task probed is solvable plain, so the floor is
not beyond reach. **Real headroom existed**, which is what upgrades the §-primary result from
"no effect detected" to "no effect where an effect had room to appear": J-Space had solvable
failures available and converted none of them (p = 0.711 two-sided, and nominally *negative*
against `ds-plain`, 15 discordant pairs to 17).

The same fact forecloses the obvious follow-up. Skill-on arms for Opus or Kimi would measure an
intervention in a region where both models already score at ceiling on the hardest tasks this
benchmark can identify, so a null there would be **uninterpretable** — indistinguishable from
"nothing left to fix". Testing J-Space against strong models needs a harder benchmark where
they sit plain somewhere near 0.4–0.6, not more units of this one.

Bounded honestly: three hand-picked tasks show saturation at the top of the difficulty band
*inferable from the deepseek data*, not across the whole benchmark.

Side finding, on cost rather than inference: `kimi-max` passed all three floor tasks on a mean
of 255,614 input tokens, against `ds-plain`'s 376,685 mean over the tasks it failed — two
thirds of the tokens, at a measured `cost_usd` of 0.000 that is plan-backed rather than
notional (§9). On the practical question of which cheap model to reach for, the measured
evidence favours Kimi over deepseek on accuracy, tokens, and cash simultaneously.

One operational note: 1 of 7 units (`rust/acronym` [opus-med]) tripped the §11 `tokens_in == 0`
guard on a missing transcript and needed a re-run, so the bounded single retry in
`invoke_omp()` does not cover every transient. The guard did its job — it refused to record an
unusable row.

## 13. Sonnet, paired: zero discordant pairs out of ten

Run 2026-08-20. `sonnet-med` (plain) vs `sonnet-jspace` (same model, same `medium` thinking,
skill on) over the ten tasks named below — chosen because **all three deepseek arms failed every
one of them**, which is where headroom is largest. 20 units, $0 cash, subscription quota.
`sonnet-jspace` is a diagnostic arm outside the registered list (`bench/arms/arms.py`).

| task | `sonnet-med` | `sonnet-jspace` |
|---|---|---|
| `javascript/ledger` | fail | fail |
| `python/bowling`, `python/forth`, `python/paasio`, `python/react` | pass | pass |
| `rust/doubly-linked-list`, `rust/forth`, `rust/grep`, `rust/react`, `rust/xorcism` | pass | pass |

9/10 both arms. `both=9, only-jspace=0, only-plain=0, neither=1`, **discordant = 0**. With no
discordant pairs McNemar has nothing to test, which is itself the result: the skill did not
change a single outcome. It did change the bill — **+5.4% input tokens** (739,286 vs 701,198)
and **+10% latency** (272s vs 247s).

Note what Sonnet did in passing: it converted **9 of deepseek's 10 floor failures** while
running plain, which is the §12 headroom finding again on a second model.

Across the capability range now measured on short, well-specified coding tasks:

| model | design | outcome | token cost of the skill |
|---|---|---|---|
| deepseek-v4-flash (weak) | n=113 paired, 3 arms | p = 0.711, nominally negative vs plain | +3.2% |
| claude-sonnet-5 (mid) | n=10 paired | 0 discordant pairs | +5.4% |
| claude-opus-5 (strong) | n=6 plain | passes the floor plain; no headroom to test | not run |

Three models, three capability tiers, no detected benefit anywhere, and a token surcharge every
time. The n=10 Sonnet probe is not powered for a verdict and is not claimed as one — but a zero
discordant-pair count is a weak result in only one direction. It cannot hide a large effect.

## 14. The long-horizon question is the one still open — bringing the instrument up cost three more bugs

Everything in §8–§13 lives on aider-polyglot: short, single-file, fully-specified exercises with
a test suite handed over. The J-Space skill claims a different domain — chained reasoning,
planning, long-horizon agentic work, complex debugging, global consistency across a large
deliverable. **None of that has been tested.** The null results above are real, and they are
real about exercise-style coding, which is arguably not where the skill claims to work.

`bench/terminal_bench/` is the right instrument (80 real multi-step container tasks, 12 easy /
44 medium / 24 hard, 9 categories) and had never been run for real. Bringing it up on
2026-08-20 surfaced two more silent failures, both now fixed:

**4. Every container build failed on an invalid docker project name.** `run_live()` built its
`--run-id` as `f"{arm}-%Y%m%dT%H%M%SZ"`. Terminal-Bench passes `--run-id` straight to
`docker compose -p`, which accepts only lowercase alphanumerics, hyphens and underscores — the
ISO stamp's `T` and `Z` are fatal. Every build died before the agent existed, and
terminal-bench recorded `unknown_agent_error`, which in `results.json` is indistinguishable
from the model failing the task. Fixed in `make_run_id()`, with the constraint locked by
`tests/test_terminal_bench_run_id.py` rather than left to a comment.

**5. The agent timeout could not cover container setup.** Each fresh container runs `apt-get`
for curl/unzip, the bun installer, then `bun install -g @oh-my-pi/pi-coding-agent` — ~600
packages, 167s for the bun step alone, ~11 min before the model sees its first token. The
default timeout cut the install off mid-flight (observed at package 594/603) and recorded
`agent_timeout` with `total_input_tokens: 0`. Now `--agent-timeout-sec` (default 2400s) is
passed through as `--global-agent-timeout-sec`.

With both fixed the pipeline reaches the model: `omp/17.4.0` installs in-container, receives its
`--append-system-prompt` addendum, and issues the request. It then gets **`401 User not
found.`** from OpenRouter.

That is not a harness bug. The `OPENROUTER_API_KEY` in the environment is dead — verified
directly against `https://openrouter.ai/api/v1/key`, HTTP 401 — and the project's own secret
registry already documents it as such (`openrouter-api-key`: *"a atual responde 401 'User not
found' — rotacionar"*). The aider sweeps were unaffected because local `omp` authenticates
through its own broker on this machine; a fresh container has only the env var.

`openrouter/deepseek/deepseek-v4-flash-0731` is reachable only through OpenRouter here, so the
whole long-horizon question hung on rotating one key — not on money, Docker, disk (321 GiB
free), or code. The key was rotated the same day and verified live (`/api/v1/key` → HTTP 200,
paid tier, no cap); note that the shell's `OPENROUTER_API_KEY` stayed dead, so runs must export
the value from the secret store rather than trust the ambient variable.

**6. The test phase has its own budget, and some tasks spend it installing.** With auth fixed
the pipeline resolved end to end on `hello-world` — container built, `omp/17.4.0` installed,
model acted, tests graded. The task legitimately failed, and instructively: the model wrote
`Hello, world!` with no trailing newline while its own summary claimed *"trailing newline"*, so
`assert hello_path.read_text() == "Hello, world!\n"` failed on the missing byte.

The first real paired probe then burned an hour for nothing. `swe-bench-fsspec` was chosen for
being the most long-horizon-looking task in the subset; its `run-tests.sh` opens with
`apt-get install -y gcc` and `pip install -e .[test]`, against a `max_test_timeout_sec` of
120.0. At the ~300–600 kB/s reachable from here that download alone needs ~11 minutes, so both
trials died as `test_timeout` with **`is_resolved: null`** — full wall-clock cost, no pass/fail,
zero information. `--test-timeout-sec` (default 1200s) now overrides it.

The network was measured before blaming the VM: 603 kB/s inside a container against 280 kB/s on
the host, so colima is not the bottleneck and there is nothing local to fix. The durable lesson
is a selection rule rather than a timeout: **pick tasks whose `run-tests.sh` installs nothing.**
`chess-best-move` and `intrusion-detection` install nothing; `fix-git` pulls boto3;
`swe-bench-fsspec` pulls a compiler. The probe was re-pointed at `intrusion-detection`, the sole
`hard`-tier task in the subset, which is both the strongest long-horizon test available and free
in its test phase.

**Known limitation of every terminal-bench figure here.** `AbstractInstalledAgent.perform_task`
returns `AgentResult(total_input_tokens=0, total_output_tokens=0)` hardcoded upstream, so no
installed-agent adapter reports usage — the shipped Codex and Claude adapters included. The
length-control gate of §5 and the mean-`tokens_in` requirement of §7 therefore **cannot be
satisfied on this benchmark** without overriding `perform_task` to recover usage from the
container. Any claim made from terminal-bench data must state that its arms were not
token-verified; the aider-polyglot arms remain the only token-controlled comparison in this
repository.
