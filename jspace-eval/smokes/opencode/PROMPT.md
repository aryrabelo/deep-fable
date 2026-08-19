# OpenCode discovery smoke — prompt and command

## Prompt sent (verbatim, does not name any skill)

```
Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines.
```

## Hermetic setup

```bash
SCRATCH=/Users/aryrabelo/Sites/temp-files/opencode-smoke-20260819-125914
CFG="$SCRATCH/config"          # OPENCODE_CONFIG_DIR target, never the real ~/.config/opencode
WORKDIR="$SCRATCH/work2"       # scratch project dir opencode ran in
mkdir -p "$CFG" "$WORKDIR"

cd /Users/aryrabelo/Sites/deep-fable
OPENCODE_CONFIG_DIR="$CFG" ./install.sh opencode
# -> Installed the J-Space skill at $CFG/skills/j-space
```

`adapters/opencode/install.sh` resolves `DEST="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}/skills/j-space"`,
so pointing `OPENCODE_CONFIG_DIR` at the scratch dir put the skill at
`$CFG/skills/j-space` and never touched `~/.config/opencode`.

## Exact command that produced `transcript.txt`

```bash
cd "$WORKDIR"
OPENCODE_CONFIG_DIR="$CFG" timeout 90 \
  /Users/aryrabelo/.opencode/bin/opencode run \
  --model "opencode/deepseek-v4-flash-free" \
  --format json \
  "Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines." \
  > "$SCRATCH/transcript_json.txt" 2>&1
```

`--format json` was added (still `opencode run`, no other semantic change) so the
transcript contains the raw `tool_use` event for OpenCode's built-in `skill` tool —
unambiguous machine evidence of which skill, if any, actually got loaded, instead of
relying on the model's own prose claim.

## Model/provider note (precondition, not part of what's being tested)

OpenCode needs a working model to run at all. Three credentialed providers already
configured on this machine (`kimi/kimi-k2.6`, `cloudflare-workers-ai/@cf/openai/gpt-oss-120b`,
`zai-coding-plan/glm-4.7`) either returned `401 Unauthorized` (expired/invalid stored
keys) or hung indefinitely and were killed — all provider/auth problems unrelated to
skill discovery. `opencode/deepseek-v4-flash-free` (OpenCode's own free hosted "Zen"
tier, ships built into the CLI, no local credential needed) is the model that actually
answered, so it is what this smoke used. This is a precondition failure of the sandbox's
stored API keys, not of J-Space discovery.
