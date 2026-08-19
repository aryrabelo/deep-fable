# Discovery smokes — does the skill actually fire?

`tests/test_adapters.py` proves the skill files land where they should. It cannot prove the
harness *reads* them. These smokes run each real CLI headless with a task that matches the
skill's description but **never names it**, and check the transcript for evidence that
j-space was actually loaded. Naming the skill in the prompt would invalidate the test.

Run 2026-08-19. Every raw transcript is committed unedited next to its verdict.

| harness | verdict | evidence |
|---|---|---|
| Claude Code | **PASS** | `[TOOL_USE] Skill {"skill": "j-space"}` / `Launching skill: j-space` fired before any other tool call; final answer states "Skill: j-space, at the full pass" |
| Codex CLI | **PASS** | Declared it would operate under j-space, then actually `cat`-ed the real `SKILL.md` through its shell tool and restated the choice in the skill's own pass-classification language |
| Gemini CLI | **INCONCLUSIVE** | `gemini skills list --all` shows `j-space [Enabled]` with the correct description, so loading works at v0.40.1 — but every model call was rejected by the ambient API key (429 `limit: 0`, or 403 project denied), so no live turn was observed |
| OpenCode | **FAIL** (selection artifact) | A real `skill` tool call fired, but resolved to a pre-existing `design-an-interface` skill. `opencode debug skill` proves j-space *was* loaded from the scratch config; the model simply preferred another skill. See `opencode/RETEST.md` |
| Cursor | **not run** | No Cursor CLI on this machine (`cursor` / `cursor-agent` both absent) |

## What the failures actually mean

**OpenCode is Cause B, not a packaging bug.** The retest found OpenCode's own
`opencode debug skill` listing, installed j-space into two independent scratch config trees
(one brand new, to rule out caching), and confirmed it loads with correct content every time.
The live agent then still chose a competing skill from the machine's real
`~/.agents/skills` and `~/.claude/skills`. Nothing to fix in `adapters/opencode/install.sh`.

**A fully hermetic OpenCode smoke is structurally impossible here.** OpenCode's global
`~/.agents/skills` and `~/.claude/skills` scan is not relocated by `OPENCODE_CONFIG_DIR` —
and, proven twice independently, not relocated by `HOME` either, even though
`opencode debug skill`, `debug scrap`, and `debug paths` all honor the override correctly.
There is no config-level opt-out. On a machine with other skills installed at those two real
paths, competitors cannot be removed without touching the user's real directories.

**Claude Code cannot be made hermetic non-interactively on macOS.** `CLAUDE_CONFIG_DIR` does
relocate the config home (verified empirically), but macOS Keychain namespaces Claude Code's
OAuth credentials per resolved config path, so a fresh config dir has no matching credential
and `claude -p` fails "Not logged in". The one bypass flag, `--bare`, explicitly disables
description-based skill auto-discovery — which would invalidate the test. This smoke
therefore installed to the real `~/.claude/skills/j-space` and removed it afterward.

**Gemini's block is credentials, not the skill.** Install and discovery are proven by the
CLI's own listing command. The remaining gap needs a working Gemini API key or an
interactive OAuth login; it is not something this repo can fix.

## Correction worth recording

The Codex smoke inferred from `strings` on the installed binary that
`codex-cli 0.146.0` reads only `$CODEX_HOME/skills` and that `.agents/skills` was new in
`rust-v0.148.0`. **That inference was wrong.** A follow-up pass verified two ways that
`.agents/skills` has been an unconditional user-scope root since **`rust-v0.95.0`**
(commit `e24058b7a872`, PR #10437): source inspection at tag `rust-v0.146.0`
(`codex-rs/core-skills/src/loader.rs`), and empirically — running the installed 0.146.0
binary's `codex debug prompt-input` with a probe skill at the real `~/.agents/skills`, which
appeared in the rendered list. `adapters/codex/install.sh` keeps version-aware fallback logic
with the cutoff pinned at the real boundary, so it guards genuinely ancient installs rather
than a version that never existed.

## Re-running

Each directory holds `PROMPT.md` (verbatim prompt + exact command line, env vars included),
`transcript.txt`, and `RESULT.md`. OpenCode additionally has `RETEST.md`,
`transcript-retest.txt`, and `skill-listing-retest.json`.
