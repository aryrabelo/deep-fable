## Q1 — Gemini CLI skills outside an extension
**Verdict:** YES
**Confidence:** high
**Checked:** Gemini CLI official docs site (geminicli.com), "Agent Skills" page, footer "Last updated: Apr 30, 2026"; cross-checked against `google-gemini/gemini-cli` `main` on 2026-08-19 (root `package.json` version `0.56.0-nightly.20260806.g761f604c1`).
**Evidence:**
- https://geminicli.com/docs/cli/skills/ — Official Agent Skills page lists four discovery tiers and states user skills live in `~/.gemini/skills/` (alias `~/.agents/skills/`) and workspace skills in `.gemini/skills/` (alias `.agents/skills/`); extension-bundled skills are a separate, lower-precedence tier, not a requirement.
- https://raw.githubusercontent.com/google-gemini/gemini-cli/main/.gemini/skills/ci/SKILL.md — A standalone skill the CLI's own repo ships at `.gemini/skills/ci/SKILL.md`, with YAML frontmatter containing only `name: ci` and `description:`, and no extension manifest anywhere in its directory.
**Impact on adapter:** Installer drops `<skill-name>/SKILL.md` directly into `~/.gemini/skills/` (user scope) or `<repo>/.gemini/skills/` (workspace scope) — no `gemini-extension.json` or extension bundle needed; prefer the `.agents/skills/` alias if the same skill tree is shared with other agents, since it wins within a tier.

## Q2 — Cursor per-project model override
**Verdict:** YES (subagent scope only; no repo-committed override for the main agent)
**Confidence:** high
**Checked:** Cursor official docs at cursor.com/docs, fetched 2026-08-19 (docs are versionless/continuously published; the subagents page documents current model IDs such as `composer-2.5`, `claude-opus-5`, `gpt-5.6-sol`).
**Evidence:**
- https://cursor.com/docs/subagents.md — Documents repo-committed subagent files at `.cursor/agents/<name>.md` (project scope) with a YAML frontmatter `model` field whose value is `inherit` (default) or a specific model ID with optional parameters, e.g. `claude-opus-5[effort=high,context=300k]`; project locations take precedence over `~/.cursor/agents/`, and `.cursor/` beats `.claude/`/`.codex/` compatibility paths.
- https://cursor.com/docs/rules.md — Project rules in `.cursor/rules/*.mdc` recognize only `description`, `globs`, and `alwaysApply` frontmatter; there is no `model` field, and `AGENTS.md` is described as a plain-markdown alternative with no model selection either.
- https://cursor.com/docs/subagents.md — Same page, "When the configured model won't be used": Cursor honors the frontmatter `model` unless team admin restrictions, legacy Max Mode gating, or plan limits force a fallback — i.e. the repo-committed value is advisory, not guaranteed.
**Impact on adapter:** To pin a model from the repo, the installer must write a subagent file `.cursor/agents/<name>.md` with `model: <model-id>` frontmatter and route the work through that subagent; it cannot set the model for the primary/parent agent session from a committed file (that stays a UI picker / `--model` flag choice), so the adapter must not promise a global model override for Cursor.

## Q3 — Codex CLI legacy skills path
**Verdict:** YES — `~/.codex/skills` is still read
**Confidence:** high
**Checked:** `openai/codex` `master` branch source read on 2026-08-19 (`codex-rs/ext/skills/src/host_roots.rs`), plus the current official skills doc.
**Evidence:**
- https://raw.githubusercontent.com/openai/codex/master/codex-rs/ext/skills/src/host_roots.rs — For the `ConfigLayerSource::User` config layer the loader pushes `config_folder.join("skills")` with the comment "Deprecated user skills location (`$CODEX_HOME/skills`), kept for backward compatibility.", and immediately afterwards pushes `home_dir/.agents/skills`; both are `SkillScope::User` roots. Roots are only deduped by path (`dedupe_skill_roots_by_path`), never by skill name.
- https://learn.chatgpt.com/docs/build-skills — Canonical skills doc (served for developers.openai.com/codex/skills): documents only `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`, and bundled system skills — it omits `$CODEX_HOME/skills` — and states "If two skills share the same `name`, Codex doesn't merge them; both can appear in skill selectors."
- https://raw.githubusercontent.com/openai/codex/master/codex-rs/core/src/skills.rs — `SkillScope` has exactly four variants (`User`, `Repo`, `System`, `Admin`); the legacy `$CODEX_HOME/skills` root is classified as `User`, i.e. it is not a distinct scope.
**Impact on adapter:** Both roots work, so the installer should write to `~/.agents/skills/<name>/SKILL.md` (documented, shared with other agents) and must not also copy the same skill into `~/.codex/skills/` — there is no name-based precedence winner, so a duplicate name appears twice in the skill selector rather than being overridden. Within the USER layer the legacy `$CODEX_HOME/skills` root is enumerated *before* `~/.agents/skills`, but that ordering only affects listing order, not override behaviour.

## Q4 — OpenCode config directory relocation
**Verdict:** YES
**Confidence:** high
**Checked:** OpenCode official docs (opencode.ai/docs, fetched 2026-08-19) and `anomalyco/opencode` (the current repo behind opencode.ai, `dev` branch) source read the same day.
**Evidence:**
- https://opencode.ai/docs/config/ — Documents `OPENCODE_CONFIG` ("Specify a custom config file path", loaded between global and project config) and `OPENCODE_CONFIG_DIR` ("Specify a custom config directory … searched for agents, commands, modes, and plugins just like the standard `.opencode` directory", loaded after global config so it can override).
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/core/src/global.ts — Builds all roots from the `xdg-basedir` package (`const config = path.join(xdgConfig!, "opencode")`), so `XDG_CONFIG_HOME` relocates the whole `~/.config/opencode` root; `make()` then resolves the effective config dir as `Flag.OPENCODE_CONFIG_DIR ?? Path.config`.
- https://opencode.ai/docs/skills/ — Global skills are read from `~/.config/opencode/skills/<name>/SKILL.md` (i.e. under the XDG-derived config root), alongside hard-`$HOME` fallbacks `~/.claude/skills` and `~/.agents/skills` and cwd-relative project paths.
**Impact on adapter:** Two levers, different reach: set `XDG_CONFIG_HOME` to move the entire config root (and with it `<root>/opencode/skills`), or set `OPENCODE_CONFIG_DIR` to point at a directory that is searched for agents/commands/modes/plugins (and `OPENCODE_CONFIG` for a single config file). The installer must export the env var for every `opencode` invocation, and must not expect `~/.claude/skills`, `~/.agents/skills`, or project-local `.opencode/skills`/`.claude/skills`/`.agents/skills` to follow — those resolve from real `$HOME` or cwd regardless.
