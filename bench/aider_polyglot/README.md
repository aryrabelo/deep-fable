# aider_polyglot driver

Three-arm (`jspace` / `none` / `placebo`) driver over the [Aider polyglot
benchmark](https://github.com/Aider-AI/polyglot-benchmark): 225
Exercism-derived exercises across C++, Go, Java, JavaScript, Python, Rust.
This is the statistical-power vehicle for the J-Space efficacy question —
see "Power" below for why the 15-task-pilot instinct is wrong here.

## Ground truth (verified against the real repo, not guessed)

- Repo: `Aider-AI/polyglot-benchmark`, MIT-licensed per exercise (Exercism
  copyright; see e.g. `javascript/exercises/practice/triangle/LICENSE`). No
  single repo-root LICENSE file — the grant lives per-exercise and the repo
  README points back to the upstream Exercism track repos.
- Layout: `<lang>/exercises/practice/<name>/` with `.docs/instructions.md`
  (the task statement), `.meta/config.json` (`files.solution` /
  `files.test` / `files.example`) and a reference solution under `.meta/`
  that we never expose to the agent, stub solution file(s) to edit, test
  file(s) already sitting next to the stub, and per-language build plumbing
  (`CMakeLists.txt` + vendored Catch2 for C++, `Cargo.toml` for Rust,
  `go.mod` for Go, `package.json` for JS, `gradlew`/`build.gradle` for Java).
- Native test commands (no Docker; Aider's own harness at
  `aider/benchmark/benchmark.py` runs these inside a container we don't
  have — we run them directly on the host):

  | language   | command |
  |------------|---------|
  | python     | `uv run --with pytest pytest -q` |
  | rust       | `cargo test -- --include-ignored` |
  | go         | `go test ./...` |
  | javascript | `npm install && npm test` (also un-`xtest()`s disabled specs) |
  | java       | `./gradlew test --console=plain` |
  | cpp        | `cmake -DEXERCISM_RUN_ALL_TESTS=1 -G "Unix Makefiles" .. && make` in a `build/` dir — the generated `CMakeLists.txt` wires an `ALL` target that builds *and* runs the Catch2 binary, so `make`'s exit code is pass/fail |

## Reproduce

```bash
# Dry run: clones the repo, assembles prompts, checks toolchains, writes
# schema-valid JSONL with notes:"dry-run" — calls no model, spends nothing.
uv run bench/aider_polyglot/run.py --dry-run --exercises 5

# Real sweep (spends money — orchestrator decision, not this script's):
uv run bench/aider_polyglot/run.py \
  --exercises 0 \
  --arms jspace,none,placebo \
  --runs 1 \
  --model openrouter/deepseek/deepseek-v4-flash-0731 \
  --thinking max

# Analyze one or more result files:
uv run bench/aider_polyglot/analyze.py bench/results/aider_polyglot-*.jsonl
```

`--model`/`--thinking` also read from `BENCH_MODEL`/`BENCH_THINKING` env
vars; defaults match `profile/config.yml`
(`openrouter/deepseek/deepseek-v4-flash-0731`, `max`).

Every `(exercise, arm, run)` triple gets its own scratch copy under
`bench/aider_polyglot/.scratch/` (gitignored, deleted after each task) with
`.meta/.docs/.approaches` stripped out, so arms never contaminate each other
and the agent can never read the reference solution. Test files are
re-copied fresh from the clone before grading, so an agent that edits the
test file to force a pass gets no credit.

## Toolchain requirements

The driver *functionally* probes each toolchain (runs `--version`/`-version`
and checks the exit code) rather than trusting `which` — macOS ships a
`/usr/bin/java` stub that resolves fine but exits 1 with no JDK installed,
and a `which`-only check would have silently misclassified every Java
exercise as runnable.

| toolchain | binaries checked | on this machine |
|-----------|-------------------|------------------|
| cpp       | one of `c++`/`g++`/`clang++`, plus `cmake` | **OK** |
| go        | `go` | **OK** |
| java      | `java` | **MISSING** — `/usr/bin/java` is a stub; `java -version` exits 1 with "Unable to locate a Java Runtime" |
| javascript| `node`, `npm` | **OK** |
| python    | `python3`, `uv` (runs pytest ephemerally, no repo dependency file) | **OK** |
| rust      | `rustc`, `cargo` | **OK** |

Exercise counts by language in the real repo: cpp 26, go 39, java 47,
javascript 49, python 34, rust 30 — **225 total**. With Java unavailable on
this machine, **178 exercises are usable**; a missing toolchain produces a
`notes: "skip: <reason>"` record instead of a scored failure, so it never
biases a pass-rate. Install a real JDK (`brew install openjdk`, then link it
so `/usr/bin/java` resolves to it) to unlock the remaining 47.

## Usage capture (tokens_in / tokens_out / cost_usd)

Each real (non-dry-run, non-skip) invocation runs `omp` with a fresh,
per-invocation `--session-dir` — an empty scratch directory nothing else
ever writes to. That makes the resulting session transcript deterministic
to locate: whatever `sessions/<project-slug>/<timestamp>_<uuid>.jsonl` file
shows up under it afterward is unambiguously this invocation's, no
"newest file" guess or before/after directory diff required. The driver
sums every assistant record's `message.usage` across that transcript:
`tokens_in = input + cacheRead + cacheWrite` (cached input is still input
the model conditioned on — dropping it would understate exactly the jspace
arm, where the skill payload is what gets cached across turns),
`tokens_out = output`, `cost_usd = usage.cost.total` (not a sum over every
key in the `cost` dict — that dict already contains a `total` alongside the
per-category breakdown, so summing everything double-counts; verified
concretely below).

This parser is verified against a real historical session file (this
session's own transcript, `~/.omp/agent/sessions/.../AiderPolyglotDriver.jsonl`
— free, already happened, zero additional cost):

- 75 assistant usage records; for every single one,
  `input + cacheRead + cacheWrite + output == totalTokens` exactly (checked
  programmatically, not sampled).
- The parser's summed totals (`tokens_in=13,856,232`, `tokens_out=98,712`,
  `cost_usd=4.9618086`) matched an independently written, separate
  hand-rolled aggregation over the same file bit-for-bit.
- Summing every value in `usage.cost` (including `total`) instead of using
  `total` alone gives `10.0718128` on that file — exactly 2x the correct
  `5.0359064` — confirming the double-count gotcha is real, not
  theoretical, and that the parser avoids it.

What's *not* independently confirmed: `--session-dir`'s exact path prefix
relative to the default `~/.omp/agent` root [INFERENCE — the CLI help text
documents the flag's purpose ("Directory for session storage and lookup")
but I could not exercise a live write into an isolated `--session-dir`
without either spending money on a real model call or risking an
indefinitely-hanging process on a garbage model name, both out of scope
here]. `_find_session_file()` hedges this by globbing for the
`sessions/<slug>/<file>.jsonl` shape at any depth under the isolated
directory rather than hard-coding one prefix, so it resolves correctly
whichever prefix the real CLI uses. If a real sweep's records come back
with `tokens_in=0` throughout, that means this hedge didn't find the file
— `analyze.py`'s length-control gate below turns that into a loud
UNVERIFIED rather than a silently-passing 0/0, so this failure mode cannot
hide.

## Cost estimate per full sweep

**Assumptions** (labeled as such — recalibrate against a real 5-exercise
pilot before trusting this for budgeting):

- Pricing: DeepSeek V4 Flash 0731 on OpenRouter, $0.0765 / 1M input tokens,
  $0.153 / 1M output tokens (checked against current OpenRouter listing).
- ~40,000 input tokens and ~4,000 output tokens per agent invocation — an
  agentic coding session on a small Exercism exercise typically re-sends
  growing conversation context across several tool-call turns (read stub,
  edit, run tests, read failure, edit again), which dominates the token
  count far more than the ~1-3k token instructions.md itself.
- One full sweep = 178 usable exercises × 3 arms × 1 run = **534 agent
  invocations**.

Per-invocation cost ≈ 40,000 × $0.0765/1e6 + 4,000 × $0.153/1e6 ≈ $0.00367.
Full sweep ≈ 534 × $0.00367 ≈ **$2** at `--runs 1`. Each additional
`--runs` multiplies this linearly (534 invocations per run).

## Power: why this benchmark, not a 15-task pilot

The comparison is paired (same exercise, same test, different system-prompt
arm), so the right test is McNemar's exact test on the discordant pairs —
tasks where the two arms disagree. Only discordant pairs carry information;
concordant pairs (both arms pass, or both fail) contribute nothing to the
test statistic. Coding-benchmark ablations at the prompt/scaffolding level
(not model swaps) typically produce a modest fraction of discordant pairs,
so detecting a real ~10 percentage-point pass-rate gap at conventional
significance (α=0.05, power=0.8) needs on the order of **~200 paired
tasks** — a 15-task pilot with even 5 discordant pairs has no chance of
reaching `analyze.py`'s `MIN_DISCORDANT = 10` floor, let alone real power.

This matters concretely for our current toolchain state: **178 usable
exercises at `--runs 1` is already short of the ~200 target.** Two ways to
close the gap, both cheap relative to the $2 estimate above: (a) fix the
Java toolchain to recover 47 more exercises (225 total, comfortably over
200), or (b) accept 178 and treat any verdict as provisional until Java is
fixed. `analyze.py` will refuse to print a verdict below 10 discordant
pairs regardless — it cannot be fooled into overclaiming on an underpowered
run, but "not obviously underpowered" is a much weaker claim than "well
powered," and 178 tasks sits closer to the former.

## Length control: is the placebo comparison still valid?

The placebo is length-matched to the ~60-token always-on snippet, not to
the skill it routes to — `SKILL.md` alone is 3,834 tokens, and the full
payload with modules + references is up to 42,675. Once `jspace` actually
reads `skill://j-space`, its real per-invocation token draw can diverge
from placebo's by far more than the two system-prompt addenda themselves
differ. `analyze.py` reports this explicitly, before any verdict: mean,
median, and n of `tokens_in` per arm, then the jspace/placebo mean-ratio
gated against a **1.0x–4.0x** band.

Why that band: a ratio near 1.0x means jspace never measurably read
anything beyond what placebo did — the routing instruction likely never
fired, making the two arms behaviorally indistinguishable regardless of
what their pass rates say. A ratio above 4.0x means jspace is pulling in
enough extra token volume that a pass-rate delta could just be "more
context/compute," not "these specific instructions" — the exact confound
placebo exists to rule out. 4.0x is chosen, not 2.0x, because a *working*
dynamic-routing skill should read `SKILL.md` plus roughly one relevant
module per task (a small fraction of a real multi-turn session's token
count), not the entire 42,675-token payload; 4.0x tolerates that intended
behavior on harder/longer exercises while still catching the pathology of
dumping the whole skill into every invocation.

If the ratio falls outside that band, `analyze.py` prints
`LENGTH CONTROL FAILED` and suppresses only the jspace-vs-placebo verdict
(jspace-vs-none and none-vs-placebo, if present, still print normally —
the gate is scoped to the one comparison it invalidates). If every
`tokens_in` is 0 for jspace and/or placebo (dry-run data, or a
`tokens_in`-capture bug), it prints `length control UNVERIFIED` and
suppresses the same way: a gate that silently passes on missing data is
worse than no gate at all.

Verified against three hand-built synthetic fixtures (`analyze.py` run
directly, not eyeballed):

- Ratio 1.02x (41,000 vs. 40,000 mean `tokens_in`, 20 paired tasks, 12
  discordant): gate passes, prints the normal `p=0.0386 SIGNIFICANT`
  verdict.
- Ratio 5.00x (200,000 vs. 40,000, same discordant structure across three
  arms): `LENGTH CONTROL FAILED`; jspace-vs-placebo verdict suppressed
  while jspace-vs-none (same discordant counts, not gated) still printed
  its own `p=0.0215 SIGNIFICANT` verdict — confirming the suppression is
  scoped to the one pair, not global.
- All `tokens_in == 0` (12 paired tasks): `length control UNVERIFIED`;
  jspace-vs-placebo verdict suppressed even though the underlying
  discordant count (6) would otherwise just be reported as underpowered —
  the length-control check runs and can veto *before* the power check.
