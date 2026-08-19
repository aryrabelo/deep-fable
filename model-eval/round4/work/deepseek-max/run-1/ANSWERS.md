## Q1 — Gemini CLI skills outside an extension
**Verdict:** YES
**Confidence:** high
**Checked:** google-gemini/gemini-cli `main` branch docs and source, fetched 2026-08-19
**Evidence:**
- https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills.md — documents four discovery tiers (built-in < extension < user < workspace); user skills load from `~/.gemini/skills/` or the `~/.agents/skills/` alias and workspace skills from `.gemini/skills/` or `.agents/skills/`, with "no extension" implied and precedence rules spelled out (`.agents/skills` alias wins within a tier).
- https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/creating-skills.md — "While a `SKILL.md` file is the only required component", the skill is a plain directory with `SKILL.md` carrying `name`/`description` YAML frontmatter; "Gemini CLI automatically discovers skills in the `.gemini/skills` directory" — no manifest or extension packaging.
- https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/extensions/reference.md — the extension route exists but is optional: extensions live in `<home>/.gemini/extensions`, require a `gemini-extension.json` manifest at their root, and bundle skills under `skills/<skill-name>/SKILL.md`; needed only if the skill must ship alongside MCP servers/commands/hooks.
**Impact on adapter:** The installer can place a skill directory (`skills/<name>/SKILL.md`) directly into `~/.agents/skills/<name>/` (portable alias) or the project's `.agents/skills/<name>/` — no extension bundle required; extension packaging is only needed to co-ship MCP servers/custom commands.

## Q2 — Cursor per-project model override
**Verdict:** NO
**Confidence:** high
**Checked:** Cursor official docs (cursor.com/docs), live pages fetched 2026-08-19
**Evidence:**
- https://cursor.com/docs/cli/reference/configuration.md — CLI config file-location table separates Global `~/.cursor/cli-config.json` from Project `<project>/.cursor/cli.json`, then states: "Only permissions can be configured at the project level. All other CLI settings must be set globally."; `model` appears only as an optional field of the (global) config schema, and the docs tell users to select CLI models interactively with `/model` (e.g. `/model gpt-5`).
- https://cursor.com/docs/rules.md — the only repo-committed AI-behavior files, `.cursor/rules/*.mdc`, support exactly three frontmatter fields (`description`, `globs`, `alwaysApply`) and AGENTS.md is described as a "simple alternative" — no `model` field exists in the rule schema, so no version-controlled file can select the model.
**Impact on adapter:** No repo-committed file can pin the model; to set a model reproducibly the installer must write the user-level `~/.cursor/cli-config.json` (`model` field) or rely on the interactive model picker/`/model` command.

## Q3 — Codex CLI legacy skills path
**Verdict:** YES
**Confidence:** high
**Checked:** openai/codex source at tag rust-v0.148.0 plus official Codex skills doc, fetched 2026-08-19
**Evidence:**
- https://raw.githubusercontent.com/openai/codex/rust-v0.148.0/codex-rs/ext/skills/src/host_roots.rs — the User-config-layer root resolver pushes both `config_folder.join("skills")` (with the source comment "Deprecated user skills location (`$CODEX_HOME/skills`), kept for backward compatibility") and `home_dir/.agents/skills` as separate `SkillScope::User` roots on every run — the legacy path is still read.
- https://raw.githubusercontent.com/openai/codex/rust-v0.148.0/codex-rs/utils/home-dir/src/lib.rs — confirms `CODEX_HOME` defaults to `~/.codex`, so the deprecated path is literally `~/.codex/skills` on default installs.
- https://raw.githubusercontent.com/openai/codex/rust-v0.148.0/codex-rs/skills/src/selection.rs — plain `$skill-name` mention resolution skips any name whose count is not exactly 1 (`if skill_count != 1 … continue`), so a skill present in both `~/.codex/skills` and `~/.agents/skills` is NOT resolved by directory precedence — the bare mention resolves to neither.
- https://learn.chatgpt.com/docs/build-skills — official Codex/ChatGPT skills doc (canonical at developers.openai.com/codex/skills) lists only `$HOME/.agents/skills` for the USER scope; it is silent on `~/.codex/skills`, which is exactly the source/doc divergence that makes the source decisive.
**Impact on adapter:** `~/.codex/skills` still works (backward-compat path), but the installer should target `~/.agents/skills` as canonical and never place same-named skills in both directories — duplicate names make plain-name activation fail to resolve.

## Q4 — OpenCode config directory relocation
**Verdict:** YES
**Confidence:** high
**Checked:** opencode.ai docs plus anomalyco/opencode `dev` branch source (packages/core, packages/opencode), fetched 2026-08-19
**Evidence:**
- https://opencode.ai/docs/config/ — documents two exact mechanisms: `OPENCODE_CONFIG` env var points at a custom config *file* (loaded between global and project config in precedence), and `OPENCODE_CONFIG_DIR` env var points at a custom config *directory* "searched for agents, commands, modes, and plugins just like the standard `.opencode` directory"; the default global config root is `~/.config/opencode/`.
- https://opencode.ai/docs/skills/ — global (OpenCode-native) skills live at `~/.config/opencode/skills/<name>/SKILL.md`, i.e. inside the global config directory, so relocating that root relocates native skills with it.
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/core/src/global.ts — `const config = path.join(xdgConfig!, "opencode")` via `xdg-basedir`, so `XDG_CONFIG_HOME` (a general env var, not opencode-specific) relocates the computed default global config root and therefore the `skills/` subfolder.
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/core/src/flag/flag.ts — confirms `OPENCODE_CONFIG`, `OPENCODE_CONFIG_DIR`, and `OPENCODE_CONFIG_CONTENT` are the only path-related env vars (plus `OPENCODE_TUI_CONFIG`); there is no dedicated `OPENCODE_SKILLS_DIR`.
- https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/opencode/src/config/paths.ts — `ConfigPaths.directories()` returns `Global.Path.config` + project/home `.opencode` dirs + `OPENCODE_CONFIG_DIR` *appended* — so `OPENCODE_CONFIG_DIR` is additive (extras searched on top of the default), not a full substitution.
**Impact on adapter:** To relocate config/skills the installer can set `OPENCODE_CONFIG` (file), `OPENCODE_CONFIG_DIR` (additive extra directory for agents/commands/modes/plugins/skills), or `XDG_CONFIG_HOME` (moves the default `$XDG_CONFIG_HOME/opencode` root that nests `skills/`); no dedicated skills-only env var or CLI flag exists.