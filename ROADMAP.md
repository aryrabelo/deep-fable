# Roadmap

Where each remaining piece goes. Shipped rows are verified by `tests/`; `🔜` rows are
scoped but deliberately not implemented until their unverified items below are closed.

## Support matrix

| Agent | Skill path | Always-on instruction | Model config | Status |
|---|---|---|---|---|
| OMP | `~/.omp/profiles/jspace/agent/skills/j-space` (copy) | `profile/APPEND_SYSTEM.md` | `profile/config.yml` | ✅ shipped — `./install.sh` |
| Claude Code | `~/.claude/skills/j-space` | optional snippet for `~/.claude/CLAUDE.md` (printed, never written) | `~/.claude/settings.json` → `model` | ✅ adapter — `./install.sh claude` |
| Codex CLI | `~/.agents/skills/j-space` | optional snippet for `~/.codex/AGENTS.md` (printed) | `~/.codex/config.toml` → `model` | ✅ adapter — `./install.sh codex` |
| OpenCode | `.opencode/skills/` or the `.agents/skills` compat path | `AGENTS.md` snippet | `opencode.json` | 🔜 adapter + snippet only |
| Cursor | `.cursor/skills/j-space` | rule file `.cursor/rules/j-space.mdc` with `alwaysApply: true` | `cli-config.json` | 🔜 adapter + rule file |
| Gemini CLI | packaged as an extension: `gemini-extension.json` + `skills/j-space/` + context file | extension context file | extension / CLI settings | 🔜 install via `gemini extensions install` |

In-repo, the skill lives once at `.omp/skills/j-space` (canonical). `.agents/skills/j-space`
is a committed relative symlink to it — read natively by OMP, Codex CLI, and the
OpenCode/Cursor compat paths, with no duplicated content and no second copy in a session
(OMP dedups skills by realpath). Adapters copy from the canonical path, never the symlink.

## Unverified items

Close these before implementing the corresponding adapter — each one changes the install
target:

- Gemini CLI: whether skills load outside an extension bundle at all.
- Cursor: whether a per-project model override exists, or only the global picker.
- Codex CLI: whether the legacy `.codex/skills` path is still read (affects fallback).
- OpenCode: whether the config directory can be relocated (affects env-override testing).

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
