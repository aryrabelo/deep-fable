# Resume here — the sweep is fixed but unverified and uncommitted

Updated 2026-08-19 after the first sweep attempt was aborted. Everything needed to continue is
in this file.

Resume with:

```bash
cd ~/Sites/deep-fable && omp
# then: "read bench/RESUME.md and continue"
```

## READ THIS FIRST — three things are in an unfinished state

1. **`bench/aider_polyglot/run.py` has uncommitted fixes that were never test-verified.** The
   session ended when the `bash` tool was denied by policy mid-task, so nothing could be run
   after the edits. Before anything else:
   `uv run --with pytest python -m pytest tests/ -q` (expect 78 passing) and re-read the diff.
2. **`bench/results/aider_polyglot-ds-arms.jsonl` is CONTAMINATED — delete it, never
   `--resume` from it.** Its rows were produced by the broken harness described in §11 of
   `docs/BENCHMARKS.md`: every `tokens_in` is 0 and every C++ exercise was unwinnable.
   `rm bench/results/aider_polyglot-ds-arms.jsonl`
3. **`kimi-code` is not authenticated**, so the registered `kimi-max` arm cannot run:
   `omp --model kimi-code/k3 -p "..."` returns *"Use /login, set an API key..."*. `omp models`
   lists `kimi-code/k3` with `max` support, so this is auth, not availability. Only the human
   can fix it. If it stays unfixed, the plan already says the arm is reported as **not run**.

## State at handoff

| | |
|---|---|
| Tests | 78 passing as of the last run, BEFORE the three run.py fixes — re-run them |
| Money spent | ~$0.02 (Q1 probes) + a handful of aborted-sweep invocations, roughly $0.05 total |
| Anthropic quota spent | none |
| Arm data | **none usable.** The one aborted sweep file must be deleted |

### What the aborted sweep taught, and what it now costs

Three silent harness bugs, all fixed, all written up in §11 of `docs/BENCHMARKS.md`: the work
directory was named `work` (which makes CMake demand `work_test.cpp` and fails all 29 C++
exercises regardless of model); the session-transcript glob matched nothing (every `tokens_in`
and `cost_usd` recorded as 0, silently voiding the length-control gate); and nothing raised on
either. `run.py` now aborts on the first real invocation reporting `tokens_in == 0`.

**Corrected cost: ~$4.3 for the three deepseek arms, not ~$2.** Measured per-invocation cost
from the aborted run's own transcripts is ~$0.007–0.009 × 534 invocations. Also measured:
~250s per invocation, so at `--jobs 4` the deepseek sweep is roughly 9 hours of wall clock.

Built earlier: `bench/arms/` (skill conditions incl. the token-matched placebo skill),
`bench/aider_polyglot/` (driver + McNemar/Wilcoxon analysis + length-control gate),
`bench/terminal_bench/` (omp adapter + 12-task subset), `bench/PREREGISTRATION.md` (locked,
untouched), `docs/BENCHMARKS.md`.

Done since: arms are now `(model, thinking, skill)` triples (`ARM_SPECS`, `ALL_ARMS`,
`arm_spec()`), with `ds-jspace` / `ds-plain` / `ds-placebo` / `opus-med` / `sonnet-med` wired
through `run.py` (per-arm model+thinking, recorded in every JSONL row — dry-run verified);
`analyze.py` gained Wilson CIs, paired TOST, the power/margin calculator, `--descriptives`
and `--equivalence`; `bench/PREREGISTRATION-MODELS.md` is written and locked;
`docs/BENCHMARKS.md` §9 records the margin reality.

**Registered margin: 15.0pp at α = 0.025.** 5pp is unreachable at n=178 (needs 8.50pp at
discordance 0.15, 12.98pp at 0.35). Above discordance 0.35 the plan is underpowered and
`report_equivalence()` refuses the verdict mechanically.

**The only thing left before spend is Q1 — and it needs authorisation** (see below).

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

## Q1 — ANSWERED 2026-08-19 (~$0.02)

**The profile applies both keys.** Verified for free with `omp --profile jspace config get`,
which reads effective settings: `defaultThinkingLevel` = `max` (the default profile reads
`auto`), `modelRoles` = `{"default":"openrouter/deepseek/deepseek-v4-flash-0731"}`.
`profile/config.yml` stays byte-locked; nothing was edited.

**Asking the model was worthless and nearly produced the opposite finding.** The same probe
self-reported `fast` under the profile, `minimum` under an explicit `--thinking max`, and
`default` under `--thinking off` — three runs, three wrong answers, uncorrelated with the
flag. The model id came back right every time; the thinking level is not something the model
can see. Verify harness config by querying the harness, never by asking the model — the same
failure mode that voided Round 3.

Fragility noted: `~/.omp/profiles/jspace/agent/config.yml` is a **copy**, not a symlink to
`profile/config.yml`. They agree today. A repo edit will not reach a live profile without a
reinstall, so re-run the `config get` query rather than citing the repo file.

Full write-up: §10 of `docs/BENCHMARKS.md`.

## Design change needed for Q2 and Q3 — DONE

Implemented: `ArmSpec` / `ARM_SPECS` / `ALL_ARMS` / `arm_spec()` in `bench/arms/arms.py`,
threaded through `run.py`. Table below is the spec, now also asserted by `tests/test_arms.py`:

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

Dollars are not the constraint; Anthropic quota is. **Decided:** all 178 exercises for every
arm, 1 run each — no subsample. Subsampling only loses power (n=120 needs ~13.4pp where n=178
needs ~11.0pp at discordance 0.25) and cash was never the binding constraint.

## Statistics that must be added before Q3 can be answered — DONE

All of it is in `analyze.py` (`wilson_ci`, `paired_diff_ci`, `tost_paired_binary`,
`power_paired_tost`, `smallest_margin_for_power`, `report_equivalence`,
`report_descriptives`), with `--equivalence` and `--descriptives` CLI modes and 15 tests in
`tests/test_analyze_equivalence.py`. The margin was computed, not chosen by taste: 5pp is
unreachable at n=178, so **16.0pp at α = 0.0167** is registered (three Q3 comparisons after
Amendment 1 added `kimi-max`). See §9 of `docs/BENCHMARKS.md` for the full table.
Every existing guard is retained: the discordant-pair floor, the length-control gate (which
applies to the `ds-jspace` vs `ds-placebo` pair only), the refusal to analyze without a
parseable plan, and — new — the plan's discordance ceiling, enforced mechanically rather than
left to a reader.

## Order of work when resuming

Q1 and all harness work are done. What remains, in order:

0. **Free, and mandatory before anything paid.** Run the suite (`uv run --with pytest python -m
   pytest tests/ -q`, expect 78), delete the contaminated results file, and commit the three
   uncommitted `run.py` fixes.
1. **Free.** Prove the C++ fix and the usage fix on real invocations — 2 exercises, one arm:
   ```bash
   python3 bench/aider_polyglot/run.py --arms ds-plain --runs 1 --exercises 2 --jobs 2 \
     --out ~/Sites/temp-files/cpp-check.jsonl
   ```
   Costs ~$0.02. **Acceptance: `tokens_in` > 0 and `cost_usd` > 0 on every row, and no
   `work_test.cpp` error in `notes`.** Do not proceed if either fails.
2. **~$4.3 cash, no Anthropic quota.** The deepseek arms, ~9h at `--jobs 4`:
   ```bash
   python3 bench/aider_polyglot/run.py --arms ds-jspace,ds-plain,ds-placebo --runs 1 \
     --jobs 4 --resume --out bench/results/aider_polyglot-ds-arms.jsonl
   ```
   **Read the first completed record before letting it run to the end** — that single habit is
   what caught all three bugs in §11.
3. **Quota.** `opus-med`, `sonnet-med`, and `kimi-max` if auth is fixed — 178 invocations each,
   same 178 `task_id`s as the deepseek run or pairing breaks.
4. Analyze against `bench/PREREGISTRATION-MODELS.md`: `--descriptives`, then
   `--equivalence ds-jspace opus-med --margin 16.0 --alpha 0.0167`, and again for `sonnet-med`
   and `kimi-max`.

## Standing constraint

No paid model call, and no Anthropic quota consumption, without explicit authorisation for
that specific run. Dry-run everything first. A published claim must cite the pre-registration
hash `analyze.py` prints, the discordant-pair count, and mean `tokens_in` per arm, or it does
not count under §7 of `docs/BENCHMARKS.md`.
