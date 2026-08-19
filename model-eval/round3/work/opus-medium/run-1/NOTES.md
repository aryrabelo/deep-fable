# NOTES — J-Space Cognition Suite V3.6

Source repo: https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6
Fetched via GitHub API (README.md), 2026-08-19.

## What it is

J-Space Cognition Suite is a **model-agnostic, inference-time control system** for deep
reasoning, long-horizon work, tool use, verification, and recovery. It changes nothing
about model weights — it operates purely at inference time, packaged as an installable
"Skill" for cross-platform AI hosts (selective loading, low-friction integration).

It organizes an agent's accessible working representations into a deliberately managed
workspace: a single entry point, nine selectively-loaded modules, three supporting
reference documents, and an optional standard-library controller for durable task state.

Design principle quoted from the README: **"Dense on the inside, decodable on demand,
clean on the outside." Use only the machinery the task earns.**

Cross-model compatibility: the operating effects have reportedly been reproduced across
the **DeepSeek, Qwen, GLM, GPT, and Claude** model families (effect size varies with base
capability, context policy, tool harness, sampling configuration, benchmark implementation).

## Repo facts

- Full name: `Tiger3807861189/J-Space-Cognition-Suite-V3.6`
- Description: "J-Space Cognition Suite V3.6 - AI cognitive-enhancement Skills based on
  Anthropic's J-space global workspace research."
- Stars: **2,547** · Forks: **165** · Open issues: **29**
- Primary language: **Python**
- License: **Apache License 2.0**
- DOI (Zenodo): **10.5281/zenodo.21977271** (badge: `zenodo.org/badge/1308234922.svg`)
- Release history: V1 → V1.5 → V1.8 → V2 → V2.5 → V2.6 → V3 → V3.1 → V3.2 → V3.5 →
  V3.5Turbo → **V3.6** (current)

## Structure

```text
J-Space-Cognition-Suite-V3.6/
├── .github/workflows/verify.yml    # three-platform integrity and regression checks
├── CITATION.cff                    # machine-readable citation metadata
├── CONTRIBUTING.md                 # contribution and provenance requirements
├── LICENSE                         # Apache License 2.0
├── README.md / README.zh-CN.md     # English / Chinese engineering guides
├── THIRD_PARTY_NOTICES.md          # attribution and license boundaries
├── tests/test_jspace.py            # standard-library controller regression tests
└── j-space/
    ├── SKILL.md                    # single entry, gate, routing, and invariants
    ├── modules/                    # nine selectively loaded protocols
    ├── references/                 # evidence, induction, and worked exemplars
    └── scripts/
        ├── jspace.py                # optional loop controller
        ├── workspace-ledger.md      # ledger template and contract
        └── verify_suite.py          # authoring-time integrity check
```

Nine modules (`j-space/modules/`): `broadcast.md`, `capacity.md`, `deep-reasoning.md`,
`directed-focus.md`, `empirics.md`, `introspection.md`, `markers.md`,
`self-monitoring.md`, `shorthand.md`.

Three references (`j-space/references/`): `exemplars.md`, `induction-playbook.md`,
`j-space-science.md`.

`SKILL.md` is the only registered entry — modules/references load on demand so the
control system doesn't become its own source of context pressure.

## Operating modes

| Pass | Suitable work | What loads |
|---|---|---|
| `fast` | One step, or a result checkable in one glance | Nothing extra |
| `full` | Several dependent steps and one bounded deliverable | One or two relevant modules; `ship` before delivery |
| `loop` | Multiple stages, files, turns, tools, or persistent state | Ledger, seams, checkpoints, register audit, and recovery |

The entry gate selects the lightest suitable pass automatically.

## Core mechanisms

| Mechanism | Function |
|---|---|
| Selective workspace loading | Keeps one or two load-bearing ideas active and externalizes the rest |
| Broadcast hub | One shared source for names, values, constraints, and style anchors |
| Dense Track | Carries long internal chains in compact, decodable notation |
| Bridge-before-conclusion reasoning | Makes required intermediates explicit before a conclusion consumes them |
| Metacognitive control | Routes confidence, inconsistency, and failure signals into a concrete next action |
| Empirical escape and verification | Converts stalled derivation into bounded tests with a named verifier and coverage |
| First-person agency and functional echo | Uses `I`, `we`, `let's`, `we need` to bind workspace state to later actions and checks |

## Optional controller (`j-space/scripts/jspace.py`)

Externalizes `loop`-mode state into a `.jspace/` directory in the current task workspace,
using only the Python standard library.

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

The controller only records and reports state — solution choice remains with the model.

## Install / usage (as documented)

**Option A — manual installation**
1. Clone the repo.
2. Locate the host's user-level Skills directory.
3. Copy the complete `j-space/` directory into it, so the installed entry is
   `<skills-directory>/j-space/SKILL.md`.
4. Run the integrity check: `<python-command> <skills-directory>/j-space/scripts/verify_suite.py`
   (`python`, `python3`, or `py -3`).
5. Reload the host if it discovers Skills at startup.
6. The `j-space/` directory must stay intact (relative paths to `modules/`, `references/`,
   `scripts/`). Redistribute `LICENSE` and `THIRD_PARTY_NOTICES.md` alongside it.

**Invocation**: through the host's Skill picker, `/j-space`, `$j-space`, or a direct
natural-language request; the entry gate auto-selects the lightest suitable pass.

**Maintainer verification**:
```text
<python-command> j-space/scripts/verify_suite.py
<python-command> -m unittest discover -s tests -v
```

> Note: the README also offers an "Option B" prompt asking an AI agent to install the
> Skill into a host's environment automatically. That is a claim made by the README
> itself, not an action this landing page (or its author) performs.

## Headline benchmark numbers (from README "Benchmarks" section)

Evaluation context: DeepSeek runs configured per the official DeepSeek Harness minimal-mode
setup, `max` reasoning effort, `temperature = 1.0`, `top_p = 0.95`. Comparator values retain
each provider's own published evaluation context (scores vary across harness/environment).

### Model comparison (native benchmark scores, higher is better)

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

### Efficiency (task-level indices, same task/model conditions, single run each)

| Metric | Control | J-Space | Improvement |
|---|---:|---:|---:|
| Speed (score/time, higher is better) | 0.43 | 1.09 | **2.53×** |
| Token cost (tokens/score, lower is better) | 2.63 | 1.19 | **2.21×** |

Related evaluation material: [DeepSeek V4 × J-Space Capability Realization Report]
(https://github.com/Tiger3807861189/DeepSeek-V4-J-Space-Capability-Realization-Report).

## License

Released under the **Apache License 2.0** — permits use, modification, redistribution,
and commercial integration under its notice and patent terms. Quoted/summarized external
source material remains subject to its own source terms (tracked in
`THIRD_PARTY_NOTICES.md`). When redistributing only the `j-space/` runtime directory,
carry both `LICENSE` and `THIRD_PARTY_NOTICES.md` with it.

## Sources

URLs actually fetched during this research:

1. https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6 — primary README,
   repo file tree, stars/forks/issues/license metadata (Stage 1).
2. https://github.com/Tiger3807861189/DeepSeek-V4-J-Space-Capability-Realization-Report —
   companion report (Stage 2). CC BY-ND 4.0 licensed, separate repo (1,015 stars / 63
   forks / 12 issues). Introduces the "chain-of-thought diode" engineering term
   (short-intuition vs. long-reasoning trajectories that don't mix mid-session),
   references two related external projects (`dsh-anchored-standard`,
   `dsh-routing-suite`), and publishes an extended benchmark table adding a
   `V4-Pro-0813 (+ J-Space)` column (e.g. HLE w/ tools 67.7, Terminal Bench 2.1 90.1,
   NL2Repo 73.4). Explicitly states these are project-level engineering observations,
   not peer-reviewed causal claims, and that scores are not broken down per
   chain-of-thought state. Cites the Zenodo DOI `10.5281/zenodo.21977271` for citation.
2. Cross-reference sources listed inside the capability report itself, also opened:
   - https://doi.org/10.5281/zenodo.21977271 → resolves to
     https://zenodo.org/records/21977271 (Stage 2). Zenodo software record, "J-Space
     Cognition Suite V3.6", published **August 17, 2026**, version **v3.6**, author
     `Tiger3807861189`, single archive file `Tiger3807861189/J-Space-Cognition-Suite-V3.6-v3.6.zip`
     (121.9 kB), supplement-of link back to the GitHub repo at tag `v3.6`.
   - https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 (Stage 2). Official
     DeepSeek-V4-Flash-0731 model card, MIT license, arXiv technical report
     `2606.19348`. Its own published benchmark table (Terminal Bench 2.1 82.7,
     NL2Repo 54.2, Cybergym 76.7, DeepSWE 54.4, Toolathlon-Verified 70.3, Agents' Last
     Exam 25.2, AutomationBench Public 25.1) matches the "DeepSeek V4-Flash-0731"
     baseline column quoted in the J-Space README and capability report, corroborating
     that the baseline numbers J-Space compares against are the model's own reported
     scores, not invented figures.
