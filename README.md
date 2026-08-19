# deep-fable

[![test](https://github.com/aryrabelo/deep-fable/actions/workflows/test.yml/badge.svg)](https://github.com/aryrabelo/deep-fable/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An OMP profile that boots every session into the J-Space inner-workspace discipline, running on DeepSeek — plus the benchmark that motivated putting DeepSeek in that seat.

No harness, no state machine. A profile: a system prompt append, a model default, and a vendored skill.

## Install

```bash
git clone https://github.com/aryrabelo/deep-fable.git
cd deep-fable
./install.sh
```

`install.sh` builds `~/.omp/profiles/jspace/agent/` from `profile/`, vendors `.omp/skills/j-space` into it, and registers the `deep-fable` alias. It **never bundles credentials** — no keys, no `.env`, no `agent.db` are copied. After install, authenticate OpenRouter yourself: set `OPENROUTER_API_KEY` in your shell, or run `omp` login and follow its prompts.

## Use

```bash
deep-fable
# or, without the alias:
omp --profile jspace
```

Every session starts by reading `skill://j-space` and operating under it, on `openrouter/deepseek/deepseek-v4-flash-0731` at `max` thinking.

## Other coding agents

The skill itself is agent-agnostic — no OMP-specific syntax anywhere in it. Every major
coding agent installs today:

```bash
./install.sh claude     # -> ~/.claude/skills/j-space
./install.sh codex      # -> ~/.agents/skills/j-space
./install.sh opencode   # -> ~/.config/opencode/skills/j-space
./install.sh cursor     # -> ~/.cursor/skills/j-space
./install.sh gemini     # -> ~/.gemini/skills/j-space   (no extension bundle needed)
```

No adapter edits your config. Each copies the skill and prints the optional always-on
snippet for you to paste — model choice stays with your agent's own settings.

| Agent | Status |
|---|---|
| OMP | ✅ `./install.sh` |
| Claude Code | ✅ `./install.sh claude` |
| Codex CLI | ✅ `./install.sh codex` |
| OpenCode | ✅ `./install.sh opencode` |
| Cursor | ✅ `./install.sh cursor` |
| Gemini CLI | ✅ `./install.sh gemini` |

In-repo the skill lives once at `.omp/skills/j-space`; `.agents/skills/j-space` is a symlink
to it, and that single path is read natively by OMP, Codex CLI, Cursor, and Gemini CLI. Full
support matrix and the verified sources behind each install path: [ROADMAP.md](ROADMAP.md).

## Why DeepSeek

Two rounds of fair-comparison benchmarking (`model-eval/`) before picking a default.

**Round 1 — 5 models × effort levels × 6 real maintenance tasks × 3 runs, deterministic held-out acceptance, no LLM judge.** 234/234 PASS. Every model, every effort level, every run — a ceiling. Effort level produced no measurable difference at this task size. Verdict: choose on cost, not correctness. Full report: [`model-eval/REPORT.md`](model-eval/REPORT.md).

**Round 3 — opus:medium vs deepseek:max, a five-stage creative landing-page build, blind human A/B.** Both cells 12/12 on the objective checker, clean render, zero console errors. The human judge broke the tie narrowly toward opus ("quase um empate mas a X tá melhor") — while deepseek finished ~3 minutes faster at a cost of cents. Full report: [`model-eval/round3/REPORT.md`](model-eval/round3/REPORT.md).

| | `claude-opus-5:medium` | `deepseek-v4-flash-0731:max` |
|---|---|---|
| Objective checks | 12/12 | 12/12 |
| Console errors | 0 | 0 |
| Wall time | ~18 min | ~15 min |
| Blind A/B | won, narrowly | lost, narrowly |
| Cost | reserve-tier | cents |

<p align="center">
  <img src="docs/images/opus-medium.png" width="48%" alt="claude-opus-5:medium landing page"/>
  <img src="docs/images/deepseek-max.png" width="48%" alt="deepseek-v4-flash-0731:max landing page"/>
</p>
<p align="center"><sub><b>Left:</b> claude-opus-5:medium &nbsp;·&nbsp; <b>Right:</b> deepseek-v4-flash-0731:max</sub></p>

DeepSeek doesn't clearly lose. It clearly costs less. That's the whole case for the default.

## Layout

```
deep-fable/
├── README.md
├── ROADMAP.md               # support matrix, verified install paths with sources
├── LICENSE
├── .gitignore
├── install.sh               # ./install.sh [omp|claude|codex|opencode|cursor|gemini]
├── profile/
│   ├── config.yml           # modelRoles.default: deepseek-v4-flash-0731, defaultThinkingLevel: max
│   └── APPEND_SYSTEM.md     # boot instruction: read skill://j-space, operate under it
├── .omp/skills/j-space/     # vendored J-Space Cognition Suite (Apache-2.0, see LICENSE)
├── .agents/skills/j-space   # symlink -> .omp/skills/j-space (OMP / Codex / Cursor / Gemini)
├── adapters/                # per-agent installers: claude, codex, opencode, cursor, gemini
├── .github/workflows/       # CI: pytest on push and pull_request
├── model-eval/              # benchmark harness, briefs, reports (rounds 1, 3, 4)
│   ├── round3/
│   └── round4/
├── jspace-eval/             # J-Space-specific eval tasks and verifier
├── tests/                   # pytest for install.sh / adapters / repo hygiene
└── docs/images/             # benchmark screenshots
```

## Credit

- **J-Space Cognition Suite V3.6** by [Tiger3807861189](https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6) — vendored under `.omp/skills/j-space`, Apache License 2.0.
- Repo shape inspired by [duolahypercho/gauntlet-loop](https://github.com/duolahypercho/gauntlet-loop).

## License

MIT for this repository's own code — see [LICENSE](LICENSE). `.omp/skills/j-space` remains Apache-2.0 under its upstream license.
