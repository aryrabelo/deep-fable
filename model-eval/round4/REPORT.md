# Round 4 — opus:medium vs deepseek:max on real research work — 2026-08-19

First round in this series that **discriminates**. Rounds 1 and 3 hit ceilings (234/234;
12/12 both cells) because every task was fully specified and machine-checkable. Round 4
used a task class where models actually diverge — factual research with sourcing
discipline, where the failure mode is a confident wrong answer rather than a failing test.

The workload was real work: the four unverified items blocking the OpenCode / Cursor /
Gemini CLI adapters in `ROADMAP.md` (see `BRIEF.md`).

## Methodology correction (affects Round 3)

Round 3 pinned models with `agent(prompt, { model })` in the JS eval kernel. **That option
is ignored.** Probes on 2026-08-19:

1. `agent("...", { model: "definitely-not/a-real-model-xyz:max" })` returned a normal
   answer instead of erroring.
2. Dispatches pinned to opus and to deepseek, asked to self-report their model id, both
   answered `claude-sonnet-5` — the default subagent model.

So Round 3's two cells were probably the same model and its narrow blind-A/B verdict
should be treated as **unreproduced**. Round 4 dispatches each cell as a separate `omp`
CLI process with `--model`/`--thinking`, which is falsifiable and was verified: a bogus id
gives `Model "..." not found`, and each real id self-reports itself.

## Cells

| cell | dispatch | wall time |
|---|---|---|
| `opus-medium` | `--model anthropic/claude-opus-5 --thinking medium` | **570s** |
| `deepseek-max` | `--model openrouter/deepseek/deepseek-v4-flash-0731 --thinking max` | **1281s** |
| `reference-librarian` | `librarian` subagent, session default model | grading baseline, not a cell |

Identical brief and workdir, `--no-skills`, no git, web tools for all, checker written
before any cell ran. n=1 per cell — directional, not statistical.

## Objective checker (`acceptance/check_answers.py`, held out, negative-controlled)

| cell | score |
|---|---|
| opus-medium | **28/30** |
| deepseek-max | **30/30** |
| reference-librarian | 30/30 |

Both opus failures were the same defect: it wrote prose into the `**Verdict:**` field
(`YES (subagent scope only; no repo-committed override for the main agent)` and
`YES — \`~/.codex/skills\` is still read`) instead of the required bare
`YES|NO|INCONCLUSIVE` token. Substantively richer, formally non-compliant.

## Correctness (the discriminating axis)

Verdicts were graded against the reference cell, then every disputed claim was closed by
a dedicated source-verification pass reading vendor docs and source code.

| Q | opus-medium | deepseek-max | reference | truth after verification |
|---|---|---|---|---|
| Q1 Gemini skills outside extension | YES | YES | YES | **YES** — all correct |
| Q2 Cursor per-project model | YES, subagent scope only | NO | NO | **both right, different scopes** |
| Q3 Codex legacy path precedence | no name shadowing | `$name` activation breaks | legacy shadows | **opus right; reference wrong** |
| Q4 OpenCode config relocation | YES | YES | YES | **YES** — all correct |

Two findings worth naming:

1. **Q2 — opus found a real mechanism the other two missed.** Verification confirmed
   Cursor documents repo-committed `.cursor/agents/<name>.md` subagent files whose
   frontmatter takes `model: <id>`, including bracket parameters
   (`claude-opus-5[effort=high,context=300k]`). Neither run fabricated anything: opus is
   right that a repo file can pin a model for a *subagent*; deepseek and the reference are
   right that nothing repo-committed can pin the *primary session's* model.
2. **Q3 — opus was right and the reference was wrong.** The reference claimed the legacy
   `~/.codex/skills` shadows `~/.agents/skills` via `push_entry`'s authority+id dedup.
   Source reading (`openai/codex` @ `af70018`) shows `push_entry`'s id is the full file
   *path*, so it can never fire on a name collision; roots dedupe by path
   (`dedupe_skill_roots_by_path`), skill files dedupe by `SKILL.md` path
   (`merge_host_skill_root_snapshots`), and the official doc states both copies can appear
   in selectors. Opus's "no name-based precedence" is correct. Deepseek's narrower claim
   is also correct for the canonical CLI path: `$name` mention activation skips ambiguous
   names entirely (`collect_explicit_skill_mentions_skips_ambiguous_name` asserts an empty
   selection), so a duplicate name silently stops working.

## Verdict

Split, and the split is the useful result:

- **deepseek-max wins on instruction compliance** — 30/30 vs 28/30, zero format
  violations, and it was the only cell that both answered correctly and obeyed the output
  contract on every question.
- **opus-medium wins on depth** — the only cell right on Q3's precedence question, and the
  only one to surface Cursor's subagent-level model override. Its two checker failures came
  from cramming that extra nuance into a field the format reserved for one token.
- **Latency reversed from Round 3:** opus 570s vs deepseek 1281s — opus was 2.2× faster
  here. Round 3's opposite finding was measured under an ineffective model pin and should
  not be cited.

Practical guidance, unchanged in spirit but now with a real boundary: deepseek is the
right default for specified work with a strict output contract. For research where being
*confidently wrong* is the expensive failure — exactly the case here, where a wrong answer
sends an installer to the wrong path — opus earned its cost on 2 of 4 questions.

A caveat that cuts both ways: the reference cell, running the session default model with a
research-specialist harness, was itself wrong on Q3. Reference baselines need verification
too; this round's conclusions rest on the source-verification passes, not on the reference.

## Reproduce

```bash
# dispatch (per cell)
cd model-eval/round4/work/<cell>/run-1
omp -p --no-session --no-skills --auto-approve --model "<id>" --thinking <level> \
  "Read the file BRIEF.md in this directory and do exactly what it says. Work only inside this directory. Do not run git."

# score
python3 model-eval/round4/acceptance/check_answers.py model-eval/round4/work/<cell>/run-1
```

Full mechanics and fairness controls: `RESUME.md`.
