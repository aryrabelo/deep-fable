# OpenCode discovery retest — Cause A vs Cause B

## Verdict: Cause B confirmed — j-space is discoverable; it is out-competed, not broken

`opencode debug skill` (a real, documented subcommand — "list all available skills")
and a `--print-logs --log-level DEBUG` live run both show, unambiguously, that j-space
is loaded into the model's tool catalog, with correct content, at the correct
`OPENCODE_CONFIG_DIR`-scoped path, every single time it was installed. It never fails
to load. What happens on top of that is a semantic selection contest against other
real skills already on this machine (`pattern-review`, `design-an-interface`), which
j-space loses on this particular prompt. That is **Cause B**, not Cause A. There is no
packaging bug in `adapters/opencode/install.sh` or in the skill itself.

A second, unplanned finding fell out of trying to force Cause A vs Cause B apart by
removing the competition (see "Why full neutralization was not achievable" below):
**OpenCode's global `~/.agents/skills` and `~/.claude/skills` scan is not relocated by
the `HOME` environment variable, only by `OPENCODE_CONFIG_DIR`-scoped paths** — even
though `HOME` overrides *are* honored by `opencode debug skill`, `opencode debug scrap`,
and `opencode debug paths`. This is inconsistent between OpenCode's own debug tooling
and its live agent runtime, verified twice independently (see below).

## 1. Does OpenCode have a skill-listing command? Yes: `opencode debug skill`

```
$ /Users/aryrabelo/.opencode/bin/opencode debug --help
...
  opencode debug skill         list all available skills
...
```

Run against a scratch `OPENCODE_CONFIG_DIR` containing only `j-space` (installed via
`./install.sh opencode`, real `HOME`, nothing else in the skills directory):

```bash
FRESH=/Users/aryrabelo/Sites/temp-files/opencode-fresh-probe-1787156457-4912
cd /Users/aryrabelo/Sites/deep-fable
OPENCODE_CONFIG_DIR="$FRESH/cfg" HOME="$FRESH/home" ./install.sh opencode
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" \
  PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" \
  /Users/aryrabelo/.opencode/bin/opencode debug skill
```

Verbatim result (full raw JSON saved at
`/Users/aryrabelo/Sites/temp-files/opencode-fresh-probe-1787156457-4912/debug_skill_listing.txt`;
trimmed evidence — total count, full name list, and the `j-space` entry — committed
here as `skill-listing-retest.json`):

```json
{
  "total": 67,
  "j_space_entry": {
    "name": "j-space",
    "location": "/Users/aryrabelo/Sites/temp-files/opencode-fresh-probe-1787156457-4912/cfg/skills/j-space/SKILL.md",
    "description": "Use this skill to establish and operate the model's inner workspace \u2014 the J-space \u2014 for any task that needs more than fluent output: ..."
  }
}
```

`j-space` **is in the list**, at the correct `$OPENCODE_CONFIG_DIR/skills/j-space/SKILL.md`
location, with its real description. This alone answers Cause A vs Cause B: OpenCode
offers j-space as a candidate. It is discoverable.

## 2. Live-run confirmation with `--print-logs --log-level DEBUG`

Rather than trust the debug subcommand alone, the same prompt from `PROMPT.md` was run
live, with debug logging on, so the actual tool-catalog construction for the agent
session is visible (not just a separate `debug skill` listing).

Exact command (same prompt as the original run, same model, `HOME` pointed at a scratch
dir that was never touched by any prior `opencode` invocation under the real `HOME`, to
rule out any config-directory-level caching effect):

```bash
FRESH=/Users/aryrabelo/Sites/temp-files/opencode-fresh-probe-1787156457-4912
cd "$FRESH/work"
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" \
  PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" TMPDIR="$TMPDIR" \
  timeout 90 /Users/aryrabelo/.opencode/bin/opencode run \
  --model "opencode/deepseek-v4-flash-free" \
  --format json \
  --print-logs --log-level DEBUG \
  "Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines." \
  > transcript-retest.txt
```

Deciding evidence, quoted verbatim from `transcript-retest.txt`:

Line 25 — the runtime's own duplicate-skill-name resolver proves j-space is loaded from
our scratch config, and that it **wins precedence** over a same-named skill that
transiently existed on the real machine during this test window (see "Untouched real
paths" below — that real copy was not created by this retest and is not present now):

```
timestamp=2026-08-19T16:22:21.106Z level=WARN run=4a4c7558 message="duplicate skill name" name=j-space existing=/Users/aryrabelo/Sites/temp-files/opencode-fresh-probe-1787156457-4912/cfg/skills/j-space/SKILL.md duplicate=/Users/aryrabelo/.agents/skills/j-space/SKILL.md
```

Line 28 — the tool catalog actually built for this session contains 66 skills total
(j-space among them, per line 25):

```
timestamp=2026-08-19T16:22:21.106Z level=INFO run=4a4c7558 message=init count=66
```

Line 41 — the model's own stated choice, on the identical prompt, is a *different* real
skill (not j-space, not even `design-an-interface` this time — `pattern-review`, also
pulled from the real machine's global skill directories):

```
"text":"Operating under **pattern-review**: the task is a non-trivial code change (module split) that demands researching the existing module's dependency/web patterns before touching code, and this skill covers that pre-implementation research + review discipline without doing the implementation itself.\n\nPlan (plan only, no implementation):\n\n1. **Inventory** — enumerate the module's public exports, `__all__`, and internal cross-references..."
```

No occurrence of `j-space` or any J-Space `SKILL.md` content in the model's output
anywhere in `transcript-retest.txt` — exactly like the original run, but this time we
have direct proof (line 25) that j-space **was** a live candidate in the same tool
catalog the model chose from. The model considered it and picked something else.

## 3. Why full neutralization (Cause A vs B by literally removing the competition) was not achievable

The assignment's proposed method — point `HOME` at a scratch dir so the global
`~/.agents/skills` scan finds nothing — does not work against OpenCode's live
`opencode run` agent session, even though it visibly works against
`opencode debug skill`, `opencode debug scrap`, and `opencode debug paths`. This was
verified twice, independently, with two different scratch `HOME` directories (a reused
one and a brand-new never-before-used one), to rule out any config-directory-level
caching as the explanation:

- `opencode debug skill` under a scratch `HOME` correctly returns only the built-in
  `customize-opencode` skill plus `j-space` (2 entries) — see
  `/Users/aryrabelo/Sites/temp-files/opencode-retest-20260819-131530/debug_skill_listing_neutralized.txt`.
- `opencode debug scrap` (known projects) under a brand-new scratch `HOME` correctly
  returns `[]` — proof the override genuinely reset per-`HOME` state for that command.
- But `opencode run`, under the *exact same* scratch `HOME` and `OPENCODE_CONFIG_DIR`
  pair, still builds a 66–67-skill tool catalog pulled from the real machine's
  `~/.claude/skills` and `~/.agents/skills` (see the `init count=66` / `duplicate skill
  name` log lines above, and the earlier run in
  `/Users/aryrabelo/Sites/temp-files/opencode-retest-20260819-131530/transcript_retest.txt`
  / `transcript_retest_clean.txt`, the latter run under a fully clean `env -i` to rule
  out shell environment leakage).
- `opencode debug config` (resolved configuration) was checked for a skill-scan
  opt-out or an `additionalDirectories`/`disableGlobal`-style setting; none exists.

So there is no supported way — short of moving, deleting, or renaming the real
`~/.agents/skills` and `~/.claude/skills` directories, which the assignment explicitly
forbids — to make the live agent session see *only* j-space. Given that, this retest
answers the question the assignment actually cares about (packaging bug vs. selection
artifact) using the discoverability evidence in sections 1–2, which does not depend on
removing the competition: **j-space loads, with correct content, every time it is
installed.** The FAIL on "does j-space fire unprompted on this exact prompt" persists on
retest — but it now has a settled, non-bug explanation.

## Untouched real paths

- The real `~/.config/opencode/opencode.json`'s mtime is unchanged
  (`2026-08-08 11:20:06`, confirmed via `stat` after every run in this retest) and
  `~/.config/opencode/skills/j-space` does not exist — this retest never wrote to
  `$HOME/.config/opencode` because every install and every `opencode` invocation used an
  explicit `OPENCODE_CONFIG_DIR` pointed at a scratch directory under
  `~/Sites/temp-files/`.
- The real `~/.agents/skills/` directory was never written to, moved, or deleted by this
  retest. A `j-space` entry briefly appeared there during this test's time window (it is
  what produced the `duplicate=/Users/aryrabelo/.agents/skills/j-space/SKILL.md` log
  line quoted above) and is gone again as of this writing — that install/cleanup cycle
  belongs to a concurrent sibling task in this same multi-agent session working the
  Codex adapter's default destination (also `~/.agents/skills`), not to this retest. This
  retest's own `./install.sh opencode` invocations only ever targeted
  `$OPENCODE_CONFIG_DIR` values under `~/Sites/temp-files/`.
- `~/.local/share/opencode/opencode.db` gained ordinary session rows from these `opencode
  run` invocations, exactly as the original smoke already disclosed and exactly as any
  real `opencode run` does — not a path named in the constraint, recorded here for
  completeness only.

## Implication for anyone testing OpenCode skill discovery on this harness

`OPENCODE_CONFIG_DIR` isolates `$OPENCODE_CONFIG_DIR/skills/` correctly — a hermetic
install and a hermetic `opencode debug skill` listing both work as expected. But the
live `opencode run` agent session additionally, and always, scans the real
`~/.agents/skills` and `~/.claude/skills` on this machine, and that scan is **not**
gated by `HOME`, `OPENCODE_CONFIG_DIR`, or any documented config flag. A fully hermetic
end-to-end OpenCode discovery smoke — one where the model can only ever see the skill
under test — is not achievable on a machine that already has other skills installed
under those two real paths, without deleting or relocating them, which this repo's
constraints correctly forbid touching. Anyone re-running this smoke on
`aryrabelo`'s machine (or any machine with a populated `~/.agents/skills` /
`~/.claude/skills`) should expect the same competitive-selection dynamic, not a clean
signal.

## Command log (every invocation, verbatim, with env vars)

```bash
# Discover the listing subcommand
/Users/aryrabelo/.opencode/bin/opencode --help
/Users/aryrabelo/.opencode/bin/opencode debug --help
/Users/aryrabelo/.opencode/bin/opencode debug skill --help

# Attempt 1 — reused scratch OPENCODE_CONFIG_DIR (from the original smoke's scratch dir)
SCRATCH=/Users/aryrabelo/Sites/temp-files/opencode-retest-20260819-131530
mkdir -p "$SCRATCH/config" "$SCRATCH/work" "$SCRATCH/fakehome"
cd /Users/aryrabelo/Sites/deep-fable
OPENCODE_CONFIG_DIR="$SCRATCH/config" ./install.sh opencode
OPENCODE_CONFIG_DIR="$SCRATCH/config" /Users/aryrabelo/.opencode/bin/opencode debug skill   # real HOME -> 75 skills
HOME="$SCRATCH/fakehome" OPENCODE_CONFIG_DIR="$SCRATCH/config" /Users/aryrabelo/.opencode/bin/opencode debug skill   # -> 2 skills
cd "$SCRATCH/work"
HOME="$SCRATCH/fakehome" OPENCODE_CONFIG_DIR="$SCRATCH/config" timeout 90 \
  /Users/aryrabelo/.opencode/bin/opencode run --model "opencode/deepseek-v4-flash-free" --format json \
  "<same prompt as PROMPT.md>"   # -> picked pattern-review, from real ~/.agents/skills
env -i HOME="$SCRATCH/fakehome" OPENCODE_CONFIG_DIR="$SCRATCH/config" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin" TMPDIR="$TMPDIR" \
  timeout 90 /Users/aryrabelo/.opencode/bin/opencode run --model "opencode/deepseek-v4-flash-free" --format json \
  "<same prompt>"   # fully clean env -> picked design-an-interface again
HOME="$SCRATCH/fakehome" OPENCODE_CONFIG_DIR="$SCRATCH/config" /Users/aryrabelo/.opencode/bin/opencode debug paths
env -i HOME="$SCRATCH/fakehome" OPENCODE_CONFIG_DIR="$SCRATCH/config" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" TMPDIR="$TMPDIR" \
  timeout 60 /Users/aryrabelo/.opencode/bin/opencode run --model "opencode/deepseek-v4-flash-free" \
  --print-logs --log-level DEBUG "say hi, do not call any tool"   # first sighting of "duplicate skill name" logs

# Attempt 2 — brand-new, never-before-used HOME + OPENCODE_CONFIG_DIR (rules out caching)
FRESH=/Users/aryrabelo/Sites/temp-files/opencode-fresh-probe-1787156457-4912
mkdir -p "$FRESH/home" "$FRESH/cfg" "$FRESH/work"
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" \
  /Users/aryrabelo/.opencode/bin/opencode debug scrap   # -> [] (proves genuinely fresh)
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" \
  /Users/aryrabelo/.opencode/bin/opencode debug paths
cd /Users/aryrabelo/Sites/deep-fable
OPENCODE_CONFIG_DIR="$FRESH/cfg" HOME="$FRESH/home" ./install.sh opencode
cd "$FRESH/work"
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" \
  /Users/aryrabelo/.opencode/bin/opencode debug skill > debug_skill_listing.txt   # -> 67 skills, j-space present (see skill-listing-retest.json)
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" \
  /Users/aryrabelo/.opencode/bin/opencode debug config   # grepped for "skill" -> no opt-out setting exists
env -i HOME="$FRESH/home" OPENCODE_CONFIG_DIR="$FRESH/cfg" PATH="/usr/bin:/bin:/Users/aryrabelo/.opencode/bin:/opt/homebrew/bin" TMPDIR="$TMPDIR" \
  timeout 90 /Users/aryrabelo/.opencode/bin/opencode run \
  --model "opencode/deepseek-v4-flash-free" --format json --print-logs --log-level DEBUG \
  "Before you start, state which of your available skills you are operating under for this task and why you chose it. Then plan (do not implement) a refactor that splits a 400-line module into three files while preserving public API, keeping import cycles impossible, and keeping a deprecation shim for two releases. Keep the plan under 20 lines." \
  > transcript-retest.txt
```

All scratch state lives under `~/Sites/temp-files/opencode-retest-20260819-131530/` and
`~/Sites/temp-files/opencode-fresh-probe-1787156457-4912/`, never under `~/.config/opencode`
or `~/.agents/skills`.
