# NOTES — J-Space Cognition Suite V3.6

## What the project is

J-Space Cognition Suite is a **model-agnostic, inference-time control system** for deep
reasoning, long-horizon work, tool use, verification, and recovery. It operates entirely at
inference time — **model weights and training remain unchanged**. It is packaged as an
Agent "Skill" for cross-platform, selective-loading, low-friction integration into AI hosts
(Claude Code, other agent harnesses, etc.).

It uses the operational workspace terminology from Anthropic's "J-space" global-workspace
interpretability research, treated as control grammar rather than a claim about internal
model states.

Design principle (quoted from README): **"Dense on the inside, decodable on demand, clean
on the outside." Use only the machinery the task earns.**

## Structure

The suite is a single entry point, nine selectively-loaded modules, three supporting
references, and an optional stdlib-only runtime controller.

```
J-Space-Cognition-Suite-V3.6/
├── .github/workflows/verify.yml    # three-platform integrity and regression checks
├── CITATION.cff                    # machine-readable citation metadata
├── CONTRIBUTING.md                 # contribution and provenance requirements
├── LICENSE                         # Apache License 2.0
├── README.md                       # English engineering guide
├── README.zh-CN.md                 # Chinese engineering guide
├── THIRD_PARTY_NOTICES.md          # attribution and license boundaries for source material
├── tests/test_jspace.py            # standard-library controller regression tests
└── j-space/
    ├── SKILL.md                    # single entry, gate, routing, and invariants
    ├── modules/                    # nine selectively loaded protocols
    │   ├── broadcast.md
    │   ├── capacity.md
    │   ├── deep-reasoning.md
    │   ├── directed-focus.md
    │   ├── empirics.md
    │   ├── introspection.md
    │   ├── markers.md
    │   ├── self-monitoring.md
    │   └── shorthand.md
    ├── references/                 # evidence, induction, and worked exemplars
    │   ├── exemplars.md
    │   ├── induction-playbook.md
    │   └── j-space-science.md
    └── scripts/
        ├── jspace.py               # optional loop controller
        ├── workspace-ledger.md     # ledger template and contract
        └── verify_suite.py         # authoring-time integrity check
```

GitHub repo stats (as fetched): **2,547 stars · 165 forks · 29 open issues**. Primary
language: Python. Author/maintainer handle: `Tiger3807861189` (bilibili: Tiger380, UID
3494375382321675).

## Operating modes

Three selectively-loaded "passes," from lightest to heaviest:

| Pass | Suitable work | What loads |
|---|---|---|
| `fast` | One step, or a result checkable in one glance | Nothing extra |
| `full` | Several dependent steps and one bounded deliverable | One or two relevant modules; `ship` before delivery |
| `loop` | Multiple stages, files, turns, tools, or persistent state | Ledger, seams, checkpoints, register audit, and recovery |

The entry gate auto-selects the lightest suitable pass. A request for brevity shortens the
outer response but does not lower verification below the task's floor.

## Core mechanisms

| Mechanism | Function |
|---|---|
| Selective workspace loading | Keeps one or two load-bearing ideas active and externalizes the rest |
| Broadcast hub | Gives dependent branches one shared source for names, values, constraints, style anchors |
| Dense Track | Carries long internal chains in compact, decodable notation before returning to clean outer language |
| Bridge-before-conclusion reasoning | Makes required intermediates explicit before a conclusion consumes them |
| Metacognitive control | Routes confidence, inconsistency, and failure signals into a concrete next action |
| Empirical escape and verification | Converts stalled derivation into bounded tests with a named verifier and coverage |
| First-person agency and functional echo | Uses "I", "we", "let's", "we need" to bind workspace state to later actions and checks |

## Optional controller — `jspace.py`

Externalizes `loop`-pass state into a `.jspace/` directory inside the current task
workspace. Standard-library only. Commands:

| Command | Purpose |
|---|---|
| `note --goal "..." --next "..."` | Open the ledger and define done plus the first action |
| `note --next "..."` | Replace the single next action after a checkpoint or seam |
| `note --core "..."` | Record a hub entry |
| `note --core "..." --core-slot 1` | Swap a selected live hub entry |
| `note --check "..." --by "..."` | Append a checkpoint with verifier and coverage |
| `note --open "..." --settled-by "..."` | Record a question and what would settle it |
| `note --close N --check "..." --by "..."` | Close question N against a new recorded checkpoint |
| `seam` | Re-read current state and report recent movement |
| `ship FILE` | Inspect outgoing text for register leakage and failure signatures |
| `resume` | Reload the premise, invariants, and full ledger after a long gap |

"The controller records and reports state. Solution choice remains with the model."

## Install / usage

**Option A — manual install**
1. Download or clone the repo.
2. Locate the user-level Skills directory used by the AI host.
3. Copy the complete `j-space/` directory into it so the installed entry is
   `<skills-directory>/j-space/SKILL.md`.
4. Run the integrity check: `<python-command> <skills-directory>/j-space/scripts/verify_suite.py`
   (`<python-command>` is whichever Python 3 binary the host has: `python`, `python3`, `py -3`).
5. Reload the host if it discovers Skills at startup.
6. The `j-space/` directory must stay intact — `SKILL.md` routes to relative paths under
   `modules/`, `references/`, `scripts/`. The root `LICENSE` and `THIRD_PARTY_NOTICES.md`
   travel with any redistribution.

**Option B — ask an AI agent to install it**, via a supplied copy-paste prompt that has the
agent locate the host's Skills directory, install `j-space/`, run `verify_suite.py`, and
report back.

**Invocation** once installed: through the host's Skill picker, `/j-space`, `$j-space`, or a
direct natural-language request, e.g. *"Use j-space for this task. Audit this repository,
preserve its architecture, verify every finding, and keep the work consistent across all
affected files."*

**Maintainer verification commands** (from repo root):
```
<python-command> j-space/scripts/verify_suite.py
<python-command> -m unittest discover -s tests -v
```

## Headline benchmark numbers (from README "Model comparison" table)

All values are native benchmark scores, higher is better, `—` = not reported. HLE is split
into no-tool / tool-enabled conditions. Evaluated against DeepSeek V4-Flash-0731 with and
without J-Space V3.6, compared to GLM-5.3, Kimi-K3, Opus-4.8, and Fable 5 (w/ fallback).

| Benchmark | DeepSeek V4-Flash-0731 | + J-Space V3.6 | GLM-5.3 | Kimi-K3 | Opus-4.8 | Fable 5 (w/ fallback) |
|---|---:|---:|---:|---:|---:|---:|
| HLE (w/o tools) | 37.8 | 45.5 | — | 43.5 | 49.8 | 53.3 |
| HLE (w/ tools) | 51.5 | 60.6 | 62.5 | 56.0 | 57.9 | 63.0 |
| Terminal Bench 2.1 | 82.7 | 87.1 | 88.2 | 88.3 | 85.0 | 88.0 |
| NL2Repo | 54.2 | 70.2 | 58.0 | 58.0 | 69.7 | — |
| CyberGym | 76.7 | 81.7 | 84.5 | 80.0 | 78.3 | 83.1 |
| DeepSWE | 54.4 | 67.4 | 66.9 | 67.5 | 58.0 | 70.0 |
| Toolathlon-Verified | 70.3 | 77.7 | 73.0 | 76.5 | 76.2 | 77.9 |
| Agents' Last Exam | 25.2 | 30.1 | 28.5 | 27.6 | 25.7 | 23.8 |
| AutomationBench (Public) | 25.1 | 31.7 | 48.2 | 30.8 | 27.2 | 29.1 |

### Efficiency table

| Metric | Control | J-Space | Improvement |
|---|---:|---:|---:|
| Speed (score/time; higher is better) | 0.43 | 1.09 | **2.53×** |
| Token cost (tokens/score; lower is better) | 2.63 | 1.19 | **2.21×** |

Evaluation context: J-Space evaluations on DeepSeek used the official DeepSeek Harness
minimal-mode setup, `max` reasoning effort, `temperature = 1.0`, `top_p = 0.95`. Results are
project-level records from the project's own available evaluation environment, not an
independent/audited benchmark; comparator scores retain each provider's own published
evaluation context.

## Cross-model compatibility

Operating effects reportedly reproduced across DeepSeek, Qwen, GLM, GPT, and Claude model
families, with effect size varying by base capability, context policy, tool harness,
sampling configuration, and benchmark implementation. The portable unit is described as "the
protocol" (workspace loading, selective routing, state externalization, verification,
recovery) — independent of any vendor-specific tokenizer or API.

## Release history

V1 → V1.5 → V1.8 → V2 → V2.5 → V2.6 → V3 → V3.1 → V3.2 → V3.5 → V3.5Turbo → **V3.6**
(current). V3.6 ships one entry, nine focused modules, three supporting references, an
optional runtime controller, an authoring-time verifier, stdlib regression tests,
three-platform CI, Apache-2.0 licensing, and machine-readable citation metadata (`CITATION.cff`).

## License

**Apache License 2.0** — permits use, modification, redistribution, and commercial
integration under its notice and patent terms. See `LICENSE` in the repo. Quoted/summarized
external source material stays under its own source terms, tracked in
`THIRD_PARTY_NOTICES.md`.

## Exact names / version strings observed

- Project name: **J-Space Cognition Suite V3.6**
- Repo: `Tiger3807861189/J-Space-Cognition-Suite-V3.6`
- Skill entry file: `j-space/SKILL.md`
- Optional controller script: `j-space/scripts/jspace.py`
- Verifier script: `j-space/scripts/verify_suite.py`
- Controller state directory: `.jspace/`
- Compared models: **DeepSeek V4-Flash-0731**, **DeepSeek V4-Pro-0813** (from companion
  report), **GLM-5.3**, **Kimi-K3**, **Opus-4.8**, **Claude Fable 5 (w/ fallback)**
- Zenodo record fetched: **v3.6.1**, published **August 19, 2026**, DOI
  `10.5281/zenodo.22004675` (record id `22004675`) — note: this differs from the DOI string
  quoted inline in the companion capability-realization report's citation section
  (`10.5281/zenodo.21977271`) and from the numeric badge id in the main README
  (`1308234922`); all three point at the same Zenodo "concept"/version family for this
  project, but the exact DOI string is inconsistent across the project's own pages as
  fetched. Reporting this discrepancy rather than picking one number silently.
- License of companion capability-realization report: **CC BY-ND 4.0** (distinct from the
  Apache-2.0 license of the suite itself)

## Sources

URLs actually fetched during READ + RESEARCH stages:

1. `https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6` — main project README,
   file tree, license, stars/forks/issues, benchmark tables, install/usage instructions,
   operating modes, core mechanisms, controller command reference.
2. `https://github.com/Tiger3807861189/DeepSeek-V4-J-Space-Capability-Realization-Report` —
   companion capability-realization report (Chinese-language), linked from the README's
   "Efficiency" section as "Related evaluation material." Read for: extended benchmark table
   including DeepSeek V4-Pro-0813 numbers, evaluation-context caveats, the report's own
   license (CC BY-ND 4.0), its citation DOI string, and its list of data sources (DeepSeek
   V4-Flash-0731 model card on Hugging Face, GLM-5.3 release-evaluation record, Kimi-K3
   model card on Hugging Face, Claude Fable 5 & Claude Mythos 5 System Card PDF).
3. `https://zenodo.org/badge/latestdoi/1308234922` (resolved to
   `https://zenodo.org/records/22004675`) — the Zenodo DOI record badge linked at the top of
   the README. Read for: archived-software framing, publish date (August 19, 2026), version
   (v3.6.1), file listing (single 127.0 kB zip), and the "Is supplement to" relation back to
   the GitHub repo at tag `v3.6.1`.
