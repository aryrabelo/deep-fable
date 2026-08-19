# Verdict: PASS

Claude Code discovered and invoked the j-space skill unprompted, from its
`description` field alone, based purely on the shape of the task (a plan with
several interacting constraints that must stay consistent).

## Deciding evidence (verbatim from `transcript.txt`)

Line containing the tool-use event (`stream-json`, decoded):

```
[TOOL_USE] Skill {"skill": "j-space"}
[TOOL_RESULT] Launching skill: j-space
```

This is the harness's own `Skill` tool being called with `"skill": "j-space"` before
any other work happens — i.e. discovery, not a lucky guess in prose.

The final assistant text then explicitly names it as the operating skill and gives the
matching rationale:

> **Skill: `j-space`**, at the **full** pass. I chose it because the request is a
> plan — several coupled constraints (public API, acyclic imports, a shim with a
> lifetime) that have to stay consistent with each other inside one short
> deliverable, which is what that skill is for rather than a straight recall answer.

The requested plan was also produced (written to a plan file, summarized in the
final message), so the skill invocation was not a substitute for doing the task —
it ran alongside it, as intended.

## Hermeticity

**Attempted hermetic run first, and it is a genuine, documented capability of Claude
Code:** `CLAUDE_CONFIG_DIR=<path> claude ...` does relocate the whole config home
(settings, skills, history, plugins), confirmed empirically — pointing
`CLAUDE_SKILLS_DIR` and `CLAUDE_CONFIG_DIR` at a scratch directory under
`~/Sites/temp-files/jspace-claude-<timestamp>/config` correctly installed and would
have been read from that relocated `skills/` directory.

**It could not be exercised end-to-end in this environment**, and the reason is worth
recording as a finding in its own right: on macOS, Claude Code's OAuth credentials are
not stored in `~/.claude/.credentials.json` (that file exists but is not what gets
read) — they live in the macOS Keychain under a service name that appears to be
namespaced per resolved `CLAUDE_CONFIG_DIR` path (observed multiple
`Claude Code-credentials-<8-hex>` entries in the login keychain, one per distinct
config dir previously used on this machine, e.g. by Orca/bora worktrees). A brand-new
`CLAUDE_CONFIG_DIR` therefore has no matching Keychain entry and `claude -p` fails
immediately with `Not logged in · Please run /login` — copying the (non-authoritative)
`.credentials.json` into the new dir does not help, since it isn't what's consulted. No
`ANTHROPIC_API_KEY` or `apiKeyHelper` was available in this environment as an
alternative (and the one built-in bypass, `--bare`, explicitly disables
description-based skill auto-discovery — "skills still resolve via `/skill-name`" per
`claude --help` — so it would have invalidated the discovery test even if a key had
been available).

**Fallback used (as the assignment permits):** installed into the real
`~/.claude/skills` directory via the repo's own adapter, no env override:

```
./install.sh claude
```

which wrote **`~/.claude/skills/j-space`**. The run itself happened in a scratch
directory, `~/Sites/temp-files/jspace-claude-smoke-work`, so no repo/session files were
touched by Claude Code's own filesystem tools other than one side effect of
`--permission-mode plan`: it wrote its plan artifact to
`~/.claude/plans/before-you-start-state-transient-lovelace.md`, a normal Claude Code
plan-mode behavior.

**Both of those real paths were removed immediately after the transcript was
captured** (verified by an explicit existence check before/after):
- `~/.claude/skills/j-space` — deleted.
- `~/.claude/plans/before-you-start-state-transient-lovelace.md` — deleted.

No other file under the user's real `~/.claude` was created, modified, or deleted.
Nothing under this repo was touched by the `claude` run itself.
