# Roadmap

Where each remaining piece goes. Every agent row below now ships an installer, verified by
`tests/`. The questions that used to gate the last three are answered under "Verified
items", with the install path each answer implies.

## Support matrix

| Agent | Skill path | Always-on instruction | Model config | Status |
|---|---|---|---|---|
| OMP | `~/.omp/profiles/jspace/agent/skills/j-space` (copy) | `profile/APPEND_SYSTEM.md` | `profile/config.yml` | ✅ shipped — `./install.sh` |
| Claude Code | `~/.claude/skills/j-space` | optional snippet for `~/.claude/CLAUDE.md` (printed, never written) | `~/.claude/settings.json` → `model` | ✅ adapter — `./install.sh claude` |
| Codex CLI | `~/.agents/skills/j-space` | optional snippet for `~/.codex/AGENTS.md` (printed) | `~/.codex/config.toml` → `model` | ✅ adapter — `./install.sh codex` |
| OpenCode | `~/.config/opencode/skills/j-space`, relocatable via `OPENCODE_CONFIG_DIR` | `AGENTS.md` snippet (printed) | `opencode.json` | ✅ adapter — `./install.sh opencode` |
| Cursor | `~/.cursor/skills/j-space` (also reads `~/.agents/skills/`) | rule `.cursor/rules/j-space.mdc` with `alwaysApply: true` (printed) | global `~/.cursor/cli-config.json` only, never repo | ✅ adapter — `./install.sh cursor` |
| Gemini CLI | `~/.gemini/skills/j-space` (also reads `~/.agents/skills/`) — **no extension needed** | `GEMINI.md` snippet (printed) | Gemini CLI settings | ✅ adapter — `./install.sh gemini` |

In-repo, the skill lives once at `.omp/skills/j-space` (canonical). `.agents/skills/j-space`
is a committed relative symlink to it — and that one path is read natively by OMP, Codex
CLI, Cursor, and Gemini CLI, with no duplicated content and no second copy in a session
(OMP dedups skills by realpath). Adapters copy from the canonical path, never the symlink.

Adapter contract, identical for all five: destination overridable by env var
(`CLAUDE_SKILLS_DIR`, `AGENTS_SKILLS_DIR`, `OPENCODE_CONFIG_DIR`, `CURSOR_SKILLS_DIR`,
`GEMINI_SKILLS_DIR`), copy from the canonical skill with `cp -RL`, idempotent, and the
always-on instruction is **printed for the user to paste — never written**. No adapter
touches a user config file or a model setting.

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

**Cursor — skills load natively. ✅ (bonus finding, closed while building the adapter.)**
This was the one path the research round never covered. `https://cursor.com/docs/skills`
documents a "Skill directories" list: project `.agents/skills/` and `.cursor/skills/`,
user-level `~/.agents/skills/` and `~/.cursor/skills/`, plus `.claude/skills/` and
`.codex/skills/` compatibility paths. Cursor reads `SKILL.md` directories itself — not only
through the Claude/Codex aliases.
*Impact:* the adapter installs a plain skill directory (default `~/.cursor/skills/j-space`),
and the committed `.agents/skills/` symlink in this repo is already on Cursor's project
search path.

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

## Acceptance test per harness — run 2026-08-19

Installation is proven by `tests/test_adapters.py`. Discovery is proven by running each real
CLI headless with a task matching the skill's description and never naming it. Results,
transcripts, and the two methodological limits found along the way:
[`jspace-eval/smokes/INDEX.md`](jspace-eval/smokes/INDEX.md).

| harness | discovery | note |
|---|---|---|
| Claude Code | ✅ PASS | `Skill {"skill": "j-space"}` fired before any other tool call |
| Codex CLI | ✅ PASS | read the real `SKILL.md` through its own shell tool |
| OMP | ✅ PASS | verified twice: invisible before `./install.sh agents`, visible after |
| Gemini CLI | ⚠️ INCONCLUSIVE | `gemini skills list` shows it Enabled; live turn blocked by API-key 429/403 |
| OpenCode | ⚠️ FAIL (selection) | loads fine (`opencode debug skill`); the model preferred a competing skill |
| Cursor | ⏸ not run | no Cursor CLI installed on this machine |

Two limits worth knowing before re-running these: OpenCode's global `~/.agents/skills` and
`~/.claude/skills` scan is relocated by neither `OPENCODE_CONFIG_DIR` nor `HOME`, so a fully
hermetic smoke is impossible on a machine with other skills installed; and Claude Code's
`CLAUDE_CONFIG_DIR` relocation cannot be used non-interactively on macOS, because Keychain
namespaces its OAuth credential per config path and the only bypass (`--bare`) disables skill
auto-discovery.

## Distribution

- `.claude-plugin/plugin.json` + `marketplace.json` — near-zero marginal cost once the
  Claude Code adapter exists.
- `VERSION` + `CHANGELOG.md` + an `--update` path in `install.sh` for reinstall-in-place.

## Windows

The `.agents/` symlink requires `core.symlinks=true` on clone. Fallback if that proves
painful: drop the committed symlink and have the installers copy into `.agents/skills`
at install time instead. Nothing but `test_shared_skills_symlink` depends on the symlink.
