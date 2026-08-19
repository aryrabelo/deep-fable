# How to run a benchmark round that actually means something

Written after three rounds, two of which proved nothing. This is the protocol for round 5+,
and the reason each rule exists. Sources are linked because the rules are not obvious.

## What went wrong, precisely

| round | result | why it was uninformative |
|---|---|---|
| 1 | 234/234 PASS | **Ceiling effect.** 6 hand-written, short, fully-specified single-file tasks. Every model passed everything at every effort level. |
| 3 | 12/12 both cells | Non-discriminating task *and* the model pin was silently ignored — both cells were probably the same model. |
| 4 | 28/30 vs 30/30 | Discriminated, but a 2-point gap on 30 items with no paired test attached is not a reliability claim. |

Two distinct failures: **task difficulty was never calibrated**, and **no round ever ran a
statistical test**. Both are solved below.

## Rule 1 — Stop writing tasks. Use a calibrated public benchmark.

A hand-written suite has no mechanism to guarantee difficulty spread. An item everyone
passes carries no information about ability differences — that is the definition of a
ceiling effect, and it is what Item Response Theory exists to detect. tinyBenchmarks
([Polo et al., ICML 2024](https://arxiv.org/abs/2402.14992)) proves the converse: because
MMLU's ~14K items have IRT-calibrated difficulty, a curated ~100-item subset reproduces
full-benchmark rankings. Most items in any large pool are redundant; a small
difficulty-spread set carries the signal. A home-made 6-task suite is neither.

If a task list must ever be hand-picked: run every candidate model against every candidate
task first, then **discard every task where all cells agree** (100% or 0%). Those tasks
carry zero bits of comparative information by construction.

### Benchmark shortlist (verified against the repos, not blog posts)

**1. Terminal-Bench — best fit, zero glue code.**
[laude-institute/terminal-bench](https://github.com/laude-institute/terminal-bench).
End-to-end terminal tasks in a sandboxed tmux/Docker environment, binary pass/fail per
task. The decisive fact: it ships an `AbstractInstalledAgent` base class whose contract is
literally "install this CLI in the container, then run one non-interactive shell command
with the instruction" — and it already has maintained adapters for **claude_code, codex,
cursor_cli, gemini_cli, opencode**, plus aider, goose, openhands and others. Five of our six
targets run with no code at all. Adding `omp` is a ~50-line copy of `opencode_agent.py`.
Docker required, ~40GB of task images, 89 tasks in 2.0, roughly \$1–\$100 per full run
depending on model. Tasks are hand-authored rather than scraped, so contamination risk is
lower than SWE-bench. Caveat: top agents cluster at 80–85%, so comparing five near-frontier
models will brush a ceiling again — use a mixed-strength roster.

```bash
uv tool install terminal-bench
tb run --dataset-name terminal-bench-core --dataset-version 2.0 \
  --task-id "*" --n-tasks 15 --agent claude-code --model <model>
```

**2. SWE-bench Verified — best for real repo work.**
[SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench), 500 instances (Lite: 300).
Inference and grading are decoupled: the harness consumes a `predictions.json` of
`{instance_id, model_name_or_path, model_patch}` where `model_patch` is a plain unified
diff. **Any** agent can produce it — run the CLI in a checkout at `base_commit`, capture
`git diff`, submit. That makes it agent-agnostic despite having no agent runner. Docker,
~120GB, x86_64 recommended (ARM experimental — build locally with `--namespace ''`).
Not saturated for agent-driven runs: the project's own 100-line mini-SWE-agent scores 65%.
Contamination is a real, acknowledged limitation — these are historical GitHub issues.

**3. Aider polyglot — cheapest pilot, needs a driver.**
[Aider-AI/aider](https://github.com/Aider-AI/aider) `benchmark/benchmark.py` +
[polyglot-benchmark](https://github.com/Aider-AI/polyglot-benchmark). 225 Exercism
exercises, 6 languages, one shared Docker image, seconds per exercise. The catch: the
harness drives Aider as a library, so another CLI needs a custom per-exercise driver (a few
hours, not a new harness). Exercises are old and public — near-certainly in pretraining.

**Do not use:** BigCodeBench and LiveCodeBench (single-function pass@1 harnesses, no agent
seam — LiveCodeBench's date-tagged releases are excellent against contamination but the
framing is wrong for agents); RepoBench (fill-in-the-middle, not agentic, leaderboard
effectively dead); Commit0 (right shape, hard-wired to Aider, heavy per-library images);
SWE-bench Multimodal (private cloud grading); SWE-smith (task *synthesis* toolkit — worth
revisiting only if contamination proves fatal, since it can mint fresh instances).

## Rule 2 — n ≥ 5 runs per cell, because temperature 0 is not deterministic

Batch-size-dependent floating-point reduction order in matmul/attention kernels makes a
single request's output depend on concurrent server load
([Thinking Machines Lab, 2025](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)).
This is not noise-floor small: independent audits of SWE-bench Verified found single-run
pass@1 varying **2.2–6.0 percentage points** across ten repeated evaluations of the same
model and scaffold, with run-to-run SD above 1.5 points at temperature 0. **A 2–3 point
"improvement" is inside the noise band, not a result** — which is exactly what Round 4's
28/30 vs 30/30 is.

Report **pass@k with the unbiased estimator** — `1 - C(n-c,k)/C(n,k)` averaged over tasks
([Chen et al., 2021](https://arxiv.org/abs/2107.03374)) — not the biased naive form. For
agentic work also report **pass^k** (success on *all* k trials), introduced by
[τ-bench](https://arxiv.org/abs/2406.12045), which found GPT-4o-class agents at pass@1 ≈ 60%
but pass^8 < 25% on retail: single-run success overstates reliability enormously.

## Rule 3 — Run the paired test, or don't make the claim

Two models on the *same* task set produce **paired binary outcomes**. Comparing them as two
independent proportions throws away the pairing and is the wrong test.

- **Paired pass/fail → McNemar's test.** Build the 2×2 of discordant pairs
  (`b` = A-only-correct, `c` = B-only-correct); χ² = (b−c)²/(b+c), or the exact binomial
  form when `b+c` is small. Concordant pairs are ignored by design. Standard for NLP-style
  paired system comparison ([Dror et al., ACL 2018](https://aclanthology.org/P18-1128/)).
  At 6–10 tasks you will typically have `b+c ≤ 3` and the test will be uninformative —
  **say that plainly** instead of reporting a p-value that implies more certainty than
  exists.
- **Aggregate metrics (score, cost, latency) → paired bootstrap.** Resample task indices
  with replacement, apply the same indices to both models, recompute the delta, report the
  CI (Dror et al., after Berg-Kirkpatrick et al. 2012).
- **A single model's pass rate → Wilson score interval**, never the Wald/normal
  approximation: Wilson is asymmetric, stays in [0,1], and has far better coverage at small
  n or near 0/1 — precisely this repo's regime.

Deliverable for a model-vs-model round: McNemar (exact, small n) on paired pass/fail, plus a
Wilson interval per model's raw rate. Not two side-by-side percentages.

## Rule 4 — Fairness controls, fixed before the first run

- Identical scaffold and tool access. A harness difference confounds model capability —
  presumptively what happened in Round 3.
- Identical prompt, same injection point, same role split.
- Held-out deterministic grader (tests, exact match, checksum) over any LLM judge.
- If an LLM judge is unavoidable: disclose its human-agreement rate and randomize response
  order. GPT-4-class judges reach >80% agreement with humans — matching human-human
  agreement — but exhibit documented **position, verbosity, and self-enhancement bias**
  ([Zheng et al., 2023](https://arxiv.org/abs/2306.05685)). Never let a model judge its own
  output.
- Sealed/blind assignment for anything subjective.
- Cost and latency reported per cell, always.
- **Pre-register** tasks, metric, test, and what counts as "different" *before* running.
  [Card et al., EMNLP 2020](https://arxiv.org/abs/2010.06595) is the canonical argument:
  underpowered post-hoc NLP comparisons routinely overclaim. Their calibration: a 2000
  sentence MT test set has only ~75% power to detect a 1 BLEU difference.

## Rule 5 — Testing whether the skill helps is a different experiment

The repo ships J-Space and has never measured it. That question is **not** a model
comparison and must not be answered by one.

**Design: paired, within-model, three arms.**

| arm | condition |
|---|---|
| A | model + task, no skill |
| B | model + task, J-Space loaded |
| C | model + task, **length-matched placebo** — filler of the same token count, stripped of reasoning-discipline content |

Arm C is not optional. [Pfau et al., 2024](https://arxiv.org/abs/2404.15758) show
transformers solving algorithmic tasks with **meaningless filler tokens** (`......`) in
place of real reasoning — extra token budget alone, zero semantic content, can produce a
gain. So "skill has a real content-driven effect" is supported **only if B beats both A and
C**. If B beats A but not C, the effect is prompt length and thinking budget, not J-Space.
Hold injection position fixed across arms so primacy isn't a confound.

**Task class matters more than sample size.** Reasoning scaffolds are not uniformly
helpful, and the null results cluster exactly where Round 1 lived:

- [Sprague et al., ICLR 2025](https://arxiv.org/abs/2409.12183) — meta-analysis of 100+ CoT
  papers plus new evals: gains concentrate in symbolic/math/formal logic (+14.2, +12.3, +6.9
  points); on commonsense, reading comprehension and other "soft" reasoning the gain is near
  zero.
- [Liu et al., 2024](https://arxiv.org/abs/2410.21333) — on 3 of 6 tasks where human
  deliberation hurts, CoT hurt frontier models too, up to **−36.3 points**. Scaffolds can
  actively harm.
- [Stechly et al., NeurIPS 2024](https://arxiv.org/abs/2405.04776) — in planning, CoT gains
  come from examples matched to the query distribution and don't generalize to larger
  instances.
- Where scaffolds plausibly *do* matter: long-horizon, multi-file, ambiguous-spec,
  error-recovery work, where the bottleneck is staying on track.
  [METR, 2025](https://arxiv.org/abs/2503.14499) attributes agent capability gains primarily
  to "greater reliability and ability to adapt to mistakes" on long tasks — the mechanism
  J-Space claims to target.

So Round 1's task class was close to the worst possible place to detect a J-Space effect,
independent of the ceiling. The ablation needs long-horizon tasks or it is null by
construction.

**Stopping rule and resolution.** Fix n and runs-per-cell before starting. At ~10–20 paired
tasks, only *large* effects are detectable — think 30–40 percentage points, not 5–10. With
McNemar at ~15 tasks you would need nearly all discordant pairs to favor one arm. Report
**"no measurable effect"** — neither win nor loss — when the p-value is non-significant and
the observed gap is comparable to the nondeterminism band from Rule 2. That is a legitimate
finding: the effect is smaller than the study's resolution.

## What cannot be concluded (so the next report doesn't overclaim)

- n ≈ 6 tasks supports **no** paired statistical claim about which model is better.
- "28/30 vs 30/30" without a paired test means only "on this sample, one model made 2 fewer
  observed errors" — not that it is more reliable.
- A skill ablation on short fully-specified tasks cannot conclude "the skill doesn't help"
  in general; that task class is where scaffolds least show effects.
- Without arm C, even a clean significant B > A cannot be attributed to the skill's
  *content*.
- At tens of runs, a null is "no effect detectable at this resolution," never proof of zero
  value.

## Recommended next round

Pilot all three benchmarks small before spending: **Terminal-Bench 10–15 tasks first** (no
glue code for 5 of 6 agents, validates Docker and keys), then SWE-bench Verified with 15–20
hand-picked `--instance_ids`, then Aider polyglot at `--num-tests 20` once a driver exists.
Only then commit to a full round — and pre-register it.
