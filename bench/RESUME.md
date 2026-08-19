# Resume here — the three questions that actually need answering

Written 2026-08-19 before a machine restart. Everything needed to continue is in this file.
Nothing paid has been run. No sweep exists.

Resume with:

```bash
cd ~/Sites/deep-fable && omp
# then: "read bench/RESUME.md and continue"
```

## State at handoff (updated 2026-08-19, after Q1 and steps 2–4)

| | |
|---|---|
| Tests | 68 passing (`uv run --with pytest python -m pytest tests/ -q`) |
| Money spent on benchmarks | ~$0.02 — three Q1 config probes. No arm has been run; every driver is still dry-run verified only |
| Anthropic quota spent | none |

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
unreachable at n=178, so **15.0pp at α = 0.025** is registered. See §9 of
`docs/BENCHMARKS.md` for the full table.
Every existing guard is retained: the discordant-pair floor, the length-control gate (which
applies to the `ds-jspace` vs `ds-placebo` pair only), the refusal to analyze without a
parseable plan, and — new — the plan's discordance ceiling, enforced mechanically rather than
left to a reader.

## Order of work when resuming

Q1 and steps 2–4 are done (see "State at handoff" and the Q1 section). What remains, in order,
both items gated on authorisation because each spends money or quota:

1. **deepseek arms** (`ds-jspace`, `ds-plain`, `ds-placebo`), 178 exercises × 1 run, ~$2 cash,
   no Anthropic quota. Dry-run first, confirm per-arm model/thinking in the JSONL.
2. **Anthropic arms** (`opus-med`, `sonnet-med`), 178 invocations each of subscription quota.
   Q3 needs both: Sonnet brackets where deepseek+J-Space lands. Same 178 `task_id`s as the
   deepseek run, or pairing breaks.
3. Analyze with `--descriptives` and `--equivalence ds-jspace opus-med --margin 15.0 --alpha
   0.025` (and again vs `sonnet-med`), against `bench/PREREGISTRATION-MODELS.md`.

## Standing constraint

No paid model call, and no Anthropic quota consumption, without explicit authorisation for
that specific run. Dry-run everything first. A published claim must cite the pre-registration
hash `analyze.py` prints, the discordant-pair count, and mean `tokens_in` per arm, or it does
not count under §7 of `docs/BENCHMARKS.md`.
