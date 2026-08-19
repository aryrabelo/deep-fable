# RESUME — Round 3: opus:medium vs deepseek:max landing-page shootout

Restart-proof state file. Everything needed to finish this benchmark after a reboot is in
this file plus the committed repo. Written 2026-08-18; session context is gone after reboot,
so this file is the handoff.

## Where things stand

- DONE: benchmark design, fairness methodology, R3 task pack (this directory).
- DONE: git history committed locally (run `git log --oneline` — expect a
  "model-eval: 234-run 5-model benchmark results" commit and a rebuild commit).
- TODO: run the two R3 waves, score, blind-judge, write `REPORT.md`.

## Prior results (context)

- Round 1 (`model-eval/REPORT.md`): 5 models × 6 single-file tasks × 3 runs = 234/234
  PASS ceiling. Conclusion: routine single-file coding does not discriminate these models.
- Round 2 (ambiguous/multi-file) was designed but SUPERSEDED by this round-3 landing-page
  task per user decision.
- Incident: an external process wiped all untracked files in this repo mid-run (~19:43);
  infra was rebuilt and committed. If files vanish again, restore with
  `git checkout -- .` and re-check what automation touched the repo.

## The task (what each model must do)

`BRIEF.md` in this directory: a five-stage landing-page build from a live URL
(https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6) — READ (save NOTES.md),
RESEARCH (>= 2 more sources), PLAN (PLAN.md), BUILD (site/ with animated WebGL/three.js
hero, dark premium responsive design, real facts only), VERIFY (browser check + VERIFY.md).

## Cells

| cell | model id |
|---|---|
| opus-medium | `anthropic/claude-opus-5:medium` |
| deepseek-max | `openrouter/deepseek/deepseek-v4-flash-0731:max` |

1 run per cell (creative multistep task; variance caveat noted in the final report).
Workdirs: `model-eval/round3/work/<cell>/run-1/` — each already contains BRIEF.md.
If missing, recreate: `mkdir -p model-eval/round3/work/<cell>/run-1 && cp model-eval/round3/BRIEF.md model-eval/round3/work/<cell>/run-1/`

## How to run (in an OMP session, from this repo)

Dispatch each run as a subagent with the model pinned — in the JS eval kernel:

```js
const runR3 = async (cell, model) => {
  const dir = `/Users/aryrabelo/Sites/deep-fable/model-eval/round3/work/${cell}/run-1`;
  const t0 = Date.now();
  try {
    const r = await agent(`Read the file BRIEF.md in the directory ${dir} and do exactly what it says — all five stages, each with its artifact. Work only inside ${dir}. Do not use or read any skills (nothing under .omp/skills). Reply with one line: DONE.`, { model });
    write(`${dir}/_meta.json`, JSON.stringify({ ms: Date.now() - t0, reply: String(typeof r === "string" ? r : JSON.stringify(r)).slice(0, 300) }));
  } catch (e) {
    write(`${dir}/_meta.json`, JSON.stringify({ ms: Date.now() - t0, error: String(e).slice(0, 300) }));
  }
};
await parallel([() => runR3("opus-medium", "anthropic/claude-opus-5:medium"),
                () => runR3("deepseek-max", "openrouter/deepseek/deepseek-v4-flash-0731:max")]);
```

Expect 10-40 min per run (web fetches + a full site build + browser verify).

## How to score

1. Objective: `python3 model-eval/round3/acceptance/check_page.py model-eval/round3/work/<cell>/run-1`
   for each cell — 11 checks (artifacts exist, 3D present, facts from source, no lorem/placeholders).
2. Render check: open each `site/index.html` in the OMP browser tool; record console
   errors and whether the 3D hero actually renders; screenshot both.
3. Blind A/B: show the user both screenshots labeled only X and Y (random assignment,
   recorded in the report so the labels can be revealed after the user picks).

## Fairness controls in force

Identical brief and workdir shape for both cells; no skills; held-out objective checker;
blind human judgment for the subjective part; model ids verified dispatchable (probes
passed 2026-08-18). DeepSeek is the only metered model (~$0.07-0.14/Mtok — this task
costs cents).
