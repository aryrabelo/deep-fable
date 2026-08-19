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

Cost, stated before authorisation: ~$2 cash for all three deepseek arms; 178 Opus and 178
Sonnet invocations of subscription quota. Quota, not dollars, is the binding constraint, and
it is why `runs_per_exercise` is 1 here rather than §8's 3.
