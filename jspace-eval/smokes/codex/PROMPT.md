# Codex CLI discovery smoke — prompt and command

## Prompt sent (verbatim, single string, no skill/file names)

```
Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines.
```

## Setup (hermetic)

```bash
# Codex CLI: 0.146.0 (npm install, via mise shim)
codex --version   # codex-cli 0.146.0

SCRATCH=~/Sites/temp-files/20260819-130002-codex-jspace-smoke
mkdir -p "$SCRATCH/codex-home" "$SCRATCH/workdir"

# Install the skill via this repo's own adapter, honoring its env override.
# AGENTS_SKILLS_DIR is redirected so DEST lands inside the scratch CODEX_HOME,
# not the user's real ~/.agents/skills.
cd /Users/aryrabelo/Sites/deep-fable
CODEX_HOME="$SCRATCH/codex-home" \
AGENTS_SKILLS_DIR="$SCRATCH/codex-home/skills" \
  ./install.sh codex
# -> Installed the J-Space skill at $SCRATCH/codex-home/skills/j-space

# A fresh CODEX_HOME has no config.toml, so codex exec falls back to the
# built-in "openai" provider, which 401'd against $OPENAI_API_KEY (that key
# is scoped to a different gateway in this environment, not api.openai.com).
# To get an actual model turn without touching the real ~/.codex/config.toml,
# a minimal config.toml was written *inside the scratch CODEX_HOME only*,
# reusing the already-exported BORABOT_GATEWAY_KEY env var (no secret value
# written to disk) and a valid cheap model id from that gateway's /v1/models:
cat > "$SCRATCH/codex-home/config.toml" <<'EOF'
model = "deepseek-v4-flash-0731-bora-bot"
model_provider = "bora-bot"

[model_providers.bora-bot]
base_url = "https://models.bora.bot/v1"
env_key = "BORABOT_GATEWAY_KEY"
wire_api = "responses"
name = "bora-bot"
EOF
```

## Command actually run (produced transcript.txt)

```bash
export CODEX_HOME="$SCRATCH/codex-home"
cd "$SCRATCH/workdir"
codex exec --skip-git-repo-check -s workspace-write -C "$SCRATCH/workdir" \
  "Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines." \
  > transcript.txt 2>&1
```

Flags explained (headless requirements for `codex exec`):
- `--skip-git-repo-check` — the scratch workdir is not a git repo.
- `-s workspace-write` — sandbox policy; lets the agent read/write inside the scratch workdir (it used this to `cat` the skill file). No approval-prompt flag was needed: `codex exec` runs with `approval: never` by default (confirmed in the transcript banner, line 7), unlike the interactive TUI.
- `-C "$SCRATCH/workdir"` — sets the agent's working root to the scratch dir.
- No `--dangerously-bypass-approvals-and-sandbox` was needed or used.

## Skills path actually read

`$CODEX_HOME/skills` (here: `$SCRATCH/codex-home/skills`) — confirmed by `strings`
on the installed codex binary
(`.../node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex`):
every skills-related string references `$CODEX_HOME/skills` (or `~/.codex/skills`
when `CODEX_HOME` is unset); the binary contains **zero** occurrences of
`.agents/skills` or `AGENTS_SKILLS_DIR`. So for this installed Codex CLI version
(0.146.0), `$CODEX_HOME/skills` is not a deprecated fallback — it is the only
skills path this build reads. This makes the run fully hermetic: relocating
`CODEX_HOME` fully relocates skill discovery, no real user directory was touched.
