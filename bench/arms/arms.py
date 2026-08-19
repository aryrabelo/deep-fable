"""Arm definitions for the J-Space benchmark harness.

Three arms are compared, paired on the same task:

- "jspace"  — the real always-on J-Space snippet (profile/APPEND_SYSTEM.md)
  appended to the system prompt, unmodified, with the real skill directory
  (.omp/skills/j-space) available for the agent to read on demand.
- "none"    — no addendum at all (empty string), no skill directory.
- "placebo" — a length-matched but content-free addendum (bench/arms/placebo.md)
  plus a length-matched, content-free skill directory (bench/arms/placebo-skill).
  Both add the same number of tokens as their "jspace" counterparts without
  teaching the model anything about how to approach the task. Controls for
  "longer system prompt" / "more skill material to read" as confounds,
  distinct from controlling for "J-Space's instructions".

Stdlib only, no repo-level dependency file needed.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JSPACE_SNIPPET_PATH = REPO_ROOT / "profile" / "APPEND_SYSTEM.md"
PLACEBO_PATH = Path(__file__).resolve().parent / "placebo.md"
JSPACE_SKILL_DIR = REPO_ROOT / ".omp" / "skills" / "j-space"
PLACEBO_SKILL_DIR = Path(__file__).resolve().parent / "placebo-skill"

ARMS = ("jspace", "none", "placebo")

# Per-file correspondence between the placebo skill tree and the real one,
# used to check each placebo file is token-matched against its specific
# real counterpart (not just matched in aggregate). Paths are relative to
# PLACEBO_SKILL_DIR / JSPACE_SKILL_DIR respectively.
SKILL_FILE_PAIRS = (
    ("SKILL.md", "SKILL.md"),
    ("entries/numeric-broadcast-format.md", "modules/broadcast.md"),
    ("entries/capacity-display.md", "modules/capacity.md"),
    ("entries/list-indentation.md", "modules/deep-reasoning.md"),
    ("entries/cross-reference-format.md", "modules/directed-focus.md"),
    ("entries/precision-display.md", "modules/empirics.md"),
    ("entries/front-matter-format.md", "modules/introspection.md"),
    ("entries/marker-glyphs.md", "modules/markers.md"),
    ("entries/status-labels.md", "modules/self-monitoring.md"),
    ("entries/abbreviation-format.md", "modules/shorthand.md"),
    ("appendix/worked-examples.md", "references/exemplars.md"),
    ("appendix/onboarding-checklist.md", "references/induction-playbook.md"),
    ("appendix/citation-catalog.md", "references/j-space-science.md"),
)

# The placebo file opens with an HTML comment explaining why it must stay
# content-free (see placebo.md). That comment is developer documentation,
# never sent to the model — arm_prompt() strips it before returning the
# actual system-prompt addendum.
_COMMENT_HEADER = re.compile(r"\A<!--.*?-->\n+", re.DOTALL)

# placebo-skill/SKILL.md's frontmatter `description:` intentionally mirrors
# J-Space's trigger vocabulary (reasoning, planning, debugging, ...) so a
# real skill-discovery system loads the placebo under the same conditions
# it would load the real skill — that is what makes it a fair control.
# Frontmatter is discovery metadata, not instructional payload delivered to
# the model as guidance, so banned-vocabulary checks apply to the body
# (everything after the closing `---`), not the frontmatter block.
_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def strip_frontmatter(text: str) -> str:
    """Return `text` with a leading YAML frontmatter block removed, if present."""
    m = _FRONTMATTER.match(text)
    return text[m.end():] if m else text


def arm_prompt(arm: str) -> str:
    """Return the system-prompt addendum for `arm`."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}, expected one of {ARMS}")
    if arm == "none":
        return ""
    if arm == "jspace":
        return JSPACE_SNIPPET_PATH.read_text()
    return _COMMENT_HEADER.sub("", PLACEBO_PATH.read_text(), count=1)


def skill_dir(arm: str) -> Path | None:
    """Directory to point the agent's skill-loading mechanism at for `arm`.

    "jspace" -> the real, canonical .omp/skills/j-space directory.
    "placebo" -> the length-matched, content-free bench/arms/placebo-skill
                 directory (see SKILL_FILE_PAIRS for the per-file mapping).
    "none" -> None; no skill directory is installed at all.
    """
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}, expected one of {ARMS}")
    if arm == "none":
        return None
    if arm == "jspace":
        return JSPACE_SKILL_DIR
    return PLACEBO_SKILL_DIR


def placebo_skill_dir() -> Path:
    """Path to the placebo skill directory (bench/arms/placebo-skill)."""
    return PLACEBO_SKILL_DIR


def token_count(text: str) -> int:
    """Deterministic, stdlib-only approximation of a prompt's token count.

    Splits `text` into runs of word characters and individual punctuation
    characters (`\\w+|[^\\w\\s]`), and returns the number of pieces. This is
    NOT a real BPE tokenizer — it roughly tracks "one token per word or
    punctuation mark", which is close enough for length-matching the arms
    against each other. Do not use it for cost estimation or as a stand-in
    for the target model's actual tokenizer.
    """
    return len(re.findall(r"\w+|[^\w\s]", text))
