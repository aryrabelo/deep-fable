# 5-model coding benchmark — deep-fable — 2026-08-18

Fair-comparison run per `PLAN.md`: identical scaffolds and briefs, deterministic held-out
acceptance (no LLM judge), 3 runs per cell, isolated workdir per run.

## Matrix

5 models × effort levels × 6 tasks × 3 runs = **234 runs, 0 dispatch errors**.

- `anthropic/claude-opus-5` — low, medium
- `anthropic/claude-sonnet-5` — low, medium
- `zhipu-coding-plan/glm-5.3` — low, high, max
- `kimi-code/k3` — low, high, max
- `openrouter/deepseek/deepseek-v4-flash-0731` — low, high, max

(`:medium` does not exist for k3/deepseek; parity levels are low and high. Anthropic ran
low+medium per user choice.)

## Tasks (all machine-checkable, all real maintenance shapes of this repo)

| # | Task | Acceptance |
|---|---|---|
| T2-01 | Fix 2 planted bugs (discount threshold, shipping basis) in cart module | `test_cart.py` green |
| T2-02 | Fix 3 subtler planted bugs (tax-before-discount, missing promo cap, shipping tier order) | `test_invoice.py` green |
| C | Fix alpha-reject substring bug in `verify.py` | held-out trio: `north`/`no` PASS, `100` TRAP, `1100` FAIL |
| D | Add duplicate-`**Pass:**`-line check #7 to `verify_suite.py` | pristine exits 0; injected duplicate exits 1 naming both modules |
| E | Add `stats` subcommand to `jspace.py` | stdout regex + empty-dir exit 0 |
| F | Harden `score_tier2` vs `TimeoutExpired`/`OSError` | mocked timeout/OSError/normal trio |

## Result: ceiling

**234/234 PASS.** Every model, every effort level, every task, every run.
Wilson 95% CI per cell: [0.82, 1.00] — indistinguishable.

Spot-checks confirmed genuine work (not scorer laxity): `stats` subcommand present in E
workdirs, word-boundary regex fix in C workdirs, `TIMEOUT` handling in F workdirs,
check #7 in D workdirs. Negative controls (unfixed code) fail the acceptance scripts.

## Latency (wall-clock per run, 18 parallel per wave — contention noise included)

| cell | mean | median |
|---|---|---|
| opus:low | 149s | 148s |
| opus:medium | 132s | 139s |
| sonnet:low | 133s | 141s |
| sonnet:medium | 114s | 117s |
| glm:low | 130s | 133s |
| glm:high | 140s | 149s |
| glm:max | 122s | 122s |
| kimi:low | 125s | 131s |
| kimi:high | 120s | 126s |
| kimi:max | 111s | 114s |
| deepseek:low | 140s | 148s |
| deepseek:high | 136s | 144s |
| deepseek:max | 121s | 122s |

## Conclusions

1. **For this repo's routine coding work, all five models are interchangeable on
   correctness** — even at `:low`. Effort level produced no measurable difference on
   tasks of this size. Choose on cost and quota: glm/kimi (subscription, marginal $0),
   deepseek (cheap metered), Anthropic pair reserved for work that actually needs them.
2. The discriminative question — which model is better on *hard* tasks (multi-file
   features, ambiguous specs, long-horizon refactors) — is **not answered** by this
   suite; every task here is single-file and fully specified. A discriminating round
   needs harder, less-specified tasks and remains available: the harness
   (`briefs/`, `acceptance/`, `score.py`, workdir materializer) is task-agnostic.
3. Reproduce: `python3 model-eval/score.py` (reads `model-eval/work/`, runs held-out
   acceptance, prints the tables above).

## Incident note

A first run of this benchmark was destroyed mid-flight by an external process that wiped
all untracked content in this repo (~19:43). Infrastructure was rebuilt from session
context, committed (git), and re-run without recurrence. See session log for forensics.
