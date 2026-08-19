# OpenCode discovery smoke — result

## Verdict: FAIL (selection artifact, not a discovery bug — see `RETEST.md`)

j-space was installed, discoverable, and present in the only skills directory the
sandboxed run could see — but OpenCode's `skill` tool resolved a *different* skill
(`design-an-interface`) for this task, and never touched j-space. Discovery-in-general
works (OpenCode really does call a `skill` tool and load real `SKILL.md` content); for
this specific skill, on this specific prompt, it did not fire. `RETEST.md` settles the
ambiguity this left open: a live-run debug-log retest (`opencode debug skill` plus
`opencode run --print-logs --log-level DEBUG`) proves j-space loads correctly and wins
directory precedence every time it is installed — the model considers it and picks a
different real skill anyway. That is Cause B (discoverable but out-competed), not
Cause A (a packaging bug in this repo's adapter).

## Deciding evidence (quoted from `transcript.txt`, line 2 and line 3)

Real tool call, not a hallucinated narrative — `type":"tool_use"`, `"tool":"skill"`:

```
"input":{"name":"design-an-interface"},"state":{"status":"completed", ...
"output":"<skill_content name=\"design-an-interface\">\n# Skill: design-an-interface\n\n<objective>\nGenerate at least three radically different interface designs..."
```

The model's own stated reason (line 3):

```
"text":"I'm operating under **`design-an-interface`** — it governs module boundary
design (\"explore module boundaries\", \"shape this API\"), which is exactly what
splitting a 400-line module into three files with a stable public API is."
```

No occurrence of `j-space`, `J-Space`, or any j-space `SKILL.md` content anywhere in
`transcript.txt`.

## Why this is a genuine negative result, not a broken test

1. The `skill` tool call is real and structured (`type":"tool_use"`, `"tool":"skill"`,
   explicit `input.name`), confirmed via `opencode run --format json`, which streams
   raw internal events — this rules out "the small model just wrote skill-shaped
   prose."
2. `design-an-interface` was **not** installed by us, and does **not** exist under the
   hermetic `OPENCODE_CONFIG_DIR/skills/` (which contains only `j-space`, confirmed by
   directly listing that directory after the run — see "Hermeticity" below). It exists
   at `~/.agents/skills/design-an-interface/SKILL.md` on this machine. **OpenCode reads
   `~/.agents/skills/` globally, in addition to `$OPENCODE_CONFIG_DIR/skills/`, and that
   path is not relocated by `OPENCODE_CONFIG_DIR`.** So the model had two real, live
   skill options on the table — `j-space` (installed by us) and `design-an-interface`
   (pre-existing on the host under `~/.agents/skills/`) — and picked the latter as the
   better semantic match for "split a module into three files, preserve the public API"
   (interface/boundary design reads more literally than j-space's multi-step-reasoning
   framing to this small free model). That is a real discovery contest that j-space
   lost, not a broken sandbox.
3. This is worth flagging as a **known limitation of the hermetic method** for OpenCode
   specifically: `OPENCODE_CONFIG_DIR` isolates `opencode.json` and
   `$OPENCODE_CONFIG_DIR/skills/`, but does **not** isolate `~/.agents/skills/`, which
   OpenCode also scans unconditionally. A cleaner hermetic OpenCode run would additionally
   need `HOME` pointed at a scratch directory (or `~/.agents/skills` temporarily emptied)
   to fully control the skill candidate set. Not done here per the constraint against
   touching real user paths beyond the documented adapter target.

## Exact command

```bash
OPENCODE_CONFIG_DIR=/Users/aryrabelo/Sites/temp-files/opencode-smoke-20260819-125914/config \
  /Users/aryrabelo/.opencode/bin/opencode run \
  --model "opencode/deepseek-v4-flash-free" \
  --format json \
  "Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines."
```

Run from `/Users/aryrabelo/Sites/temp-files/opencode-smoke-20260819-125914/work2`
(scratch project dir under `~/Sites/temp-files/`, per the no-tmp-writes rule).

## Hermeticity

- Install used `OPENCODE_CONFIG_DIR=<scratch>/config ./install.sh opencode`, which per
  `adapters/opencode/install.sh` writes to
  `${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}/skills/j-space` — the scratch value
  redirected every write there. Confirmed `<scratch>/config/skills/` contains only
  `j-space/` (listed directly after the runs).
- **The user's real `~/.config/opencode/opencode.json` was never written to**: its mtime
  is `2026-08-08 11:20:06`, unchanged from before this smoke (today is `2026-08-19`), and
  `~/.config/opencode/skills/j-space` does not exist. Verified by direct listing and
  `stat` after all runs completed.
- Caveat found during the run (disclosed for completeness, not a violation of the stated
  constraint): OpenCode's own headless `run` command auto-bootstraps two files inside
  whatever `OPENCODE_CONFIG_DIR` it is given (`package.json`, `package-lock.json`,
  `.gitignore`, for its provider SDK dependency resolution) — this landed in the scratch
  config dir only, not the real one. Separately, OpenCode's session/message state is
  stored in a **global** SQLite DB at `~/.local/share/opencode/opencode.db`
  (XDG data dir, not relocated by `OPENCODE_CONFIG_DIR`), so these smoke sessions are
  recorded there as ordinary session rows. That path was not named in the constraint
  (only `~/.config/opencode`), but is recorded here in the interest of full disclosure:
  nothing under `~/.config/opencode` was touched; `~/.local/share/opencode/opencode.db`
  gained session rows the way any real `opencode run` invocation would.

## Model/provider precondition

`opencode/deepseek-v4-flash-free` (OpenCode's own built-in free "Zen" tier model,
no external credential required) is what actually produced this transcript. Three
credentialed providers already configured on this machine were tried first and all
failed for reasons unrelated to skill discovery:
- `kimi/kimi-k2.6` → `401 Unauthorized: "The API Key appears to be invalid or may have expired"` (stored key, and re-tried with the real provider's custom `baseURL` config merged in — same error, so it's the key itself, not routing).
- `cloudflare-workers-ai/@cf/openai/gpt-oss-120b` → `401 Unauthorized: "Authentication error"`.
- `zai-coding-plan/glm-4.7` → hung indefinitely (>300s, no output), killed.
- `github-copilot/claude-haiku-4.5` → `Error: The requested model is not supported.`

This is a precondition of the sandbox's stored credentials, not a discovery result;
recorded per the assignment's instruction to note when a model must be configured to run
at all.
