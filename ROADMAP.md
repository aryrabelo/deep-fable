# Roadmap

Where each remaining piece goes. Shipped rows are verified by `tests/`; `🔜` rows are
scoped, researched, and unblocked — every question that was gating them is answered under
"Verified items" below, with the install path each answer implies.

## Support matrix

| Agent | Skill path | Always-on instruction | Model config | Status |
|---|---|---|---|---|
| OMP | `~/.omp/profiles/jspace/agent/skills/j-space` (copy) | `profile/APPEND_SYSTEM.md` | `profile/config.yml` | ✅ shipped — `./install.sh` |
| Claude Code | `~/.claude/skills/j-space` | optional snippet for `~/.claude/CLAUDE.md` (printed, never written) | `~/.claude/settings.json` → `model` | ✅ adapter — `./install.sh claude` |
| Codex CLI | `~/.agents/skills/j-space` | optional snippet for `~/.codex/AGENTS.md` (printed) | `~/.codex/config.toml` → `model` | ✅ adapter — `./install.sh codex` |
| OpenCode | `~/.config/opencode/skills/j-space`, relocatable via `OPENCODE_CONFIG_DIR` | `AGENTS.md` snippet | `opencode.json` | 🔜 adapter — unblocked |
| Cursor | `.cursor/skills/j-space` | rule file `.cursor/rules/j-space.mdc` with `alwaysApply: true` | global `~/.cursor/cli-config.json` only (never repo) | 🔜 adapter + rule file — unblocked |
| Gemini CLI | `~/.agents/skills/j-space` or `~/.gemini/skills/j-space` — **no extension needed** | `GEMINI.md` / context file snippet | CLI settings | 🔜 plain adapter — unblocked |

In-repo, the skill lives once at `.omp/skills/j-space` (canonical). `.agents/skills/j-space`
is a committed relative symlink to it — read natively by OMP, Codex CLI, and the
OpenCode/Cursor compat paths, with no duplicated content and no second copy in a session
(OMP dedups skills by realpath). Adapters copy from the canonical path, never the symlink.

## Verified items (closed 2026-08-19)

All four were answered by Round 4 of the model benchmark
([`model-eval/round4/REPORT.md`](model-eval/round4/REPORT.md)) plus dedicated
source-verification passes. Every adapter below is now unblocked.

**Gemini CLI — skills load without an extension. ✅ YES.** Its docs list four discovery
tiers and read user skills from `~/.gemini/skills/` or the `~/.agents/skills/` alias, and
workspace skills from `.gemini/skills/` or `.agents/skills/`; extension-bundled skills are
merely a lower-precedence tier. The Gemini CLI repo dogfoods this, shipping
`.gemini/skills/<name>/SKILL.md` with no `gemini-extension.json`.
*Impact:* the plain copy-a-skill-directory adapter works. Extension packaging drops from a
requirement to an optional distribution nicety.

**Cursor — no repo-committed model override for the primary session. ✅ NO (with a real
exception).** `<project>/.cursor/cli.json` is permissions-only: "Only permissions can be
configured at the project level. All other CLI settings must be set globally." Rule
frontmatter is exactly `description`, `globs`, `alwaysApply` — no model field. **But**
repo-committed `.cursor/agents/<name>.md` subagent files do take `model: <id>`, including
bracket parameters like `claude-opus-5[effort=high,context=300k]`, project scope winning
over `~/.cursor/agents/`.
*Impact:* the adapter installs the skill and prints the rule; it must never claim a global
model override. Pinning a model from the repo is possible only by routing work through a
committed subagent file.

**Codex CLI — the legacy `~/.codex/skills` path is still read, with no name-based
precedence. ✅ YES.** The resolver pushes `$CODEX_HOME/skills` ("Deprecated user skills
location … kept for backward compatibility") immediately before `~/.agents/skills`, both as
user scope. Roots dedupe by path, skill files dedupe by `SKILL.md` path, and catalog
`push_entry` keys on the full path — so a same-*name* collision never shadows: both copies
load. In the canonical CLI path, an ambiguous `$name` mention then silently selects
nothing.
*Impact:* install only to `~/.agents/skills`. Never write the same skill name to both
locations, and treat a pre-existing legacy copy as something to remove, not something that
overrides.

**OpenCode — the config directory is relocatable. ✅ YES, `OPENCODE_CONFIG_DIR`.** Docs
document it as a custom config directory "searched for agents, commands, modes, and plugins
just like the standard `.opencode` directory", loaded after global config so it can
override; source resolves `Flag.OPENCODE_CONFIG_DIR ?? Path.config`, with `XDG_CONFIG_HOME`
relocating the default `~/.config/opencode` root. Global native skills live at
`~/.config/opencode/skills/<name>/SKILL.md`.
*Impact:* `OPENCODE_CONFIG_DIR` is the env-override the adapter test needs, matching the
`CLAUDE_SKILLS_DIR` / `AGENTS_SKILLS_DIR` pattern already in `tests/test_adapters.py`.

## Any-model story

Per agent the model is a single key: `config.yml` (OMP), `config.toml` (Codex),
`settings.json` (Claude Code), `cli-config.json` (Cursor), `opencode.json` (OpenCode).
That part is trivial. The real gap is **provider registration** — DeepSeek-via-OpenRouter
has a different model id and auth path in each tool. Until that is mapped per tool, no
adapter here writes a model setting; each one prints the key and leaves it to the user.
Mapping it is a separate research scope, not a code change.

## Acceptance test per harness

One smoke test per adapter, same shape for all: a scripted prompt that must trigger the
skill before any code is produced, run in the real harness, transcript captured and
committed under `jspace-eval/`. Passing = the skill fired unprompted; failing = discovery
is broken for that harness regardless of the files being in place.

## Distribution

- `.claude-plugin/plugin.json` + `marketplace.json` — near-zero marginal cost once the
  Claude Code adapter exists.
- `VERSION` + `CHANGELOG.md` + an `--update` path in `install.sh` for reinstall-in-place.

## Windows

The `.agents/` symlink requires `core.symlinks=true` on clone. Fallback if that proves
painful: drop the committed symlink and have the installers copy into `.agents/skills`
at install time instead. Nothing but `test_shared_skills_symlink` depends on the symlink.
