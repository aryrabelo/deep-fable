# RESUME — Round 4: opus:medium vs deepseek:max on real research work

Restart-proof state file. Everything needed to finish or reproduce this round is in this
file plus the committed repo.

## What this round tests

Rounds 1 and 3 both hit ceilings (234/234 PASS; 12/12 both cells) because every task was
fully specified and machine-checkable. Round 4 uses a task class where models actually
diverge: **factual research with sourcing discipline**, where the failure mode is a
confident wrong answer rather than a failing test.

The workload is real work, not a synthetic exercise: the four unverified items blocking
the OpenCode / Cursor / Gemini CLI adapters in `ROADMAP.md`. Whichever cell is right
also unblocks the repo.

## Methodology fix — read this before reusing the Round 3 rig

Round 3 dispatched cells with `agent(prompt, { model })` in the JS eval kernel. **That
option is ignored.** Two probes on 2026-08-19:

1. `agent("...", { model: "definitely-not/a-real-model-xyz:max" })` returned a normal
   answer instead of erroring.
2. Dispatches pinned to `anthropic/claude-opus-5:medium` and to
   `openrouter/deepseek/deepseek-v4-flash-0731:max`, asked to self-report their model id,
   both answered `claude-sonnet-5` — the default subagent model.

So Round 3's two cells were probably the same model, and its narrow blind-A/B verdict
should be treated as unreproduced. Round 4 therefore dispatches each cell as a separate
`omp` CLI process with `--model` / `--thinking`, which is falsifiable and was verified:

- `omp -p --model "definitely-not/a-real-model-xyz" "say ok"` → `Model "..." not found`.
- `omp -p --model "openrouter/deepseek/deepseek-v4-flash-0731" ...` → self-reports
  `openrouter/deepseek/deepseek-v4-flash-0731`.
- `omp -p --model "anthropic/claude-opus-5" ...` → self-reports `anthropic/claude-opus-5`.

## Cells

| cell | dispatch | role |
|---|---|---|
| `opus-medium` | `--model anthropic/claude-opus-5 --thinking medium` | benchmark cell |
| `deepseek-max` | `--model openrouter/deepseek/deepseek-v4-flash-0731 --thinking max` | benchmark cell |
| `reference-librarian` | `librarian` subagent, session default model | **reference, not a cell** — grading baseline |

1 run per cell (variance caveat: n=1; treat as directional).

## How to run

```bash
cd model-eval/round4/work/<cell>/run-1
omp -p --no-session --no-skills --auto-approve \
    --model "<model id>" --thinking <level> \
    "Read the file BRIEF.md in this directory and do exactly what it says. Work only inside this directory. Do not run git."
```

Fairness controls: identical `BRIEF.md` and workdir shape, `--no-skills` (no J-Space, no
repo skills), no git access, web tools allowed for all cells, held-out checker written
before any cell ran.

## How to score

1. **Format/sourcing (objective, held out):**
   `python3 model-eval/round4/acceptance/check_answers.py model-eval/round4/work/<cell>/run-1`
   — 30 checks: section structure, verdict vocabulary, confidence, what was checked,
   adapter impact, ≥2 distinct evidence URLs per question, ≥1 primary source per question.
   Negative-controlled: an empty cell scores 0/1 and exits 1.
2. **Correctness (the discriminating axis):** per question, compare each cell's verdict
   against `reference-librarian`, then spot-verify the cited URLs by hand. Score
   agreement, and record any case where a cell was confidently wrong — that is the
   failure this round is designed to catch.
3. **Cost/latency:** `_meta.json` per cell holds exit code and wall seconds.

## Then

Merge the verdicts that survive verification into the "Unverified items" section of
`ROADMAP.md`, and write `REPORT.md` here.
