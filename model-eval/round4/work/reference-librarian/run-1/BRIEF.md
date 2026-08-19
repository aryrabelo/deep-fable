# Task R4 — Close four adapter-blocking research questions

You are answering four factual questions about how current coding-agent CLIs load
"Agent Skills" (`SKILL.md` directories) and how their model is configured. Each answer
decides an install path in a real installer, so a wrong-but-confident answer is worse
than an honest `INCONCLUSIVE`.

Work only inside this directory. Use your web tools. Prefer primary sources: official
docs, the vendor's own repo, release notes, or the CLI's source code. Forum posts and
blogs are acceptable only as secondary corroboration.

## The four questions

**Q1 — Gemini CLI: skills outside an extension.**
Can Gemini CLI load a skill directory (`SKILL.md` with `name`/`description` frontmatter)
without packaging it as an extension? If it cannot, state the minimum extension bundle
required (file names and where they go).

**Q2 — Cursor: per-project model override.**
Does Cursor support a per-project / repo-committed model override (a file a repo can
ship that selects the model), or is the model only selectable globally in the UI or via
a user-level config?

**Q3 — Codex CLI: legacy skills path.**
Does current Codex CLI still read a legacy `~/.codex/skills` directory, in addition to
`~/.agents/skills`? If both are read, state the precedence.

**Q4 — OpenCode: relocating the config/skills directory.**
Can OpenCode's config or skills directory be relocated via an environment variable or
CLI flag (the way `XDG_CONFIG_HOME` or a dedicated env var would)? Name the exact
variable or flag if it exists.

## Required output — `ANSWERS.md` in this directory

Use this exact structure, four sections, headings verbatim:

```
## Q1 — Gemini CLI skills outside an extension
**Verdict:** YES | NO | INCONCLUSIVE
**Confidence:** high | medium | low
**Checked:** <tool name and version or release date you verified against>
**Evidence:**
- <url> — <what this source actually says, one line>
- <url> — <what this source actually says, one line>
**Impact on adapter:** <one line: what the installer must do given this answer>

## Q2 — Cursor per-project model override
... same six fields ...

## Q3 — Codex CLI legacy skills path
... same six fields ...

## Q4 — OpenCode config directory relocation
... same six fields ...
```

Rules for the answers:

- At least **two** distinct URLs of evidence per question, and at least one of them must
  be a primary source for that tool (its official docs or its own repository).
- Every URL listed must be one you actually fetched and read in this run. Do not list a
  URL you guessed at or could not open.
- `INCONCLUSIVE` is a valid verdict and is scored as correct when the evidence genuinely
  does not settle the question. Say what you would need to settle it.
- No placeholders: no `TBD`, `TODO`, `N/A`, or empty fields.

Do not modify anything outside this directory. Do not run git. When finished, reply with
one line: `DONE`.
