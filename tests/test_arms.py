"""Tests for bench/arms/arms.py — the jspace/none/placebo prompt arms.

The placebo arm exists to control for prompt LENGTH only. These tests defend
that at two levels: the always-on snippet (placebo.md) and the full skill
payload (placebo-skill/), which is the part of a real J-Space run that a
model actually reads once it follows "read skill://j-space" — 42,675 tokens
across SKILL.md + modules/ + references/, not the 60-token snippet alone.
Both levels must be within 5% of their real counterpart's token count, must
not leak reasoning/metacognition vocabulary that could plausibly help a
model do the task, and must not be degenerate (near-duplicate-line) filler
that a reviewer would reject as an invalid control.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bench.arms.arms import (  # noqa: E402
    ARMS,
    JSPACE_SKILL_DIR,
    PLACEBO_SKILL_DIR,
    SKILL_FILE_PAIRS,
    arm_prompt,
    placebo_skill_dir,
    skill_dir,
    strip_frontmatter,
    token_count,
)

APPEND_SYSTEM_PATH = REPO_ROOT / "profile" / "APPEND_SYSTEM.md"

# Banned substrings: reasoning/metacognition/planning vocabulary the placebo
# must never contain. Built from the actual vocabulary of APPEND_SYSTEM.md
# that names J-Space's reasoning discipline (establish, workspace, discipline,
# classify, route, module) plus the required fixed list of reasoning verbs.
BANNED_SUBSTRINGS = [
    "think", "plan", "reflect", "reason", "verify", "decompose", "step by step",
    "workspace", "scratchpad",
    "discipline", "classify", "route", "module", "establish",
]


def test_placebo_token_count_within_5_percent_of_real_snippet():
    real_tokens = token_count(APPEND_SYSTEM_PATH.read_text())
    placebo_tokens = token_count(arm_prompt("placebo"))
    delta = abs(placebo_tokens - real_tokens) / real_tokens
    assert delta <= 0.05, (
        f"placebo token count {placebo_tokens} is {delta:.1%} off "
        f"real snippet token count {real_tokens} (must be within 5%)"
    )


def test_none_arm_is_empty():
    assert arm_prompt("none") == ""


def test_jspace_arm_matches_append_system_byte_for_byte():
    assert arm_prompt("jspace") == APPEND_SYSTEM_PATH.read_text()


def test_placebo_contains_no_reasoning_vocabulary():
    text = arm_prompt("placebo").lower()
    hits = [word for word in BANNED_SUBSTRINGS if word in text]
    assert not hits, f"placebo leaks reasoning vocabulary: {hits}"


def test_placebo_is_not_degenerate_filler():
    lines = [line for line in arm_prompt("placebo").split("\n") if line.strip()]
    assert lines, "placebo has no non-blank lines"
    unique_ratio = len(set(lines)) / len(lines)
    assert unique_ratio >= 0.6, (
        f"placebo lines are only {unique_ratio:.0%} unique; "
        "a repetitive/degenerate filler is not a valid length control"
    )


def test_unknown_arm_rejected():
    import pytest

    with pytest.raises(ValueError):
        arm_prompt("bogus")


def test_arms_tuple_is_exactly_the_contract():
    assert ARMS == ("jspace", "none", "placebo")


# --- skill_dir() / placebo-skill/ (the actual J-Space payload) ---


def test_skill_dir_jspace_is_the_canonical_skill():
    d = skill_dir("jspace")
    assert d == JSPACE_SKILL_DIR
    assert (d / "SKILL.md").is_file()


def test_skill_dir_none_is_none():
    assert skill_dir("none") is None


def test_skill_dir_placebo_is_placebo_skill_dir():
    assert skill_dir("placebo") == PLACEBO_SKILL_DIR == placebo_skill_dir()
    assert (PLACEBO_SKILL_DIR / "SKILL.md").is_file()


def test_skill_dir_rejects_unknown_arm():
    import pytest

    with pytest.raises(ValueError):
        skill_dir("bogus")


def test_placebo_skill_frontmatter_is_valid():
    text = (PLACEBO_SKILL_DIR / "SKILL.md").read_text()
    assert text.startswith("---\n"), "placebo SKILL.md must open with a YAML frontmatter block"
    header, _, rest = text[4:].partition("\n---\n")
    assert rest, "placebo SKILL.md frontmatter block is never closed with ---"
    assert "name: bench-placebo" in header
    assert "description:" in header
    # the description must mirror enough of J-Space's trigger surface that a
    # discovery system would load this skill for the same task types
    real_description = (JSPACE_SKILL_DIR / "SKILL.md").read_text()
    trigger_words = ["multi-step", "planning", "long-horizon", "debugging", "confidence"]
    for word in trigger_words:
        assert word in real_description, f"fixture assumption broken: {word!r} not in real SKILL.md"
        assert word in header, f"placebo description missing trigger word {word!r}"


def test_every_placebo_skill_file_token_matches_its_real_counterpart_within_5_percent():
    rows = []
    for placebo_rel, real_rel in SKILL_FILE_PAIRS:
        real_tokens = token_count((JSPACE_SKILL_DIR / real_rel).read_text())
        placebo_tokens = token_count((PLACEBO_SKILL_DIR / placebo_rel).read_text())
        delta = abs(placebo_tokens - real_tokens) / real_tokens
        rows.append((placebo_rel, real_rel, real_tokens, placebo_tokens, delta))
    offenders = [r for r in rows if r[4] > 0.05]
    assert not offenders, "per-file token mismatch > 5%: " + ", ".join(
        f"{p} ({real_t} real vs {pb_t} placebo, {d:.1%})" for p, _, real_t, pb_t, d in offenders
    )


def test_placebo_skill_files_contain_no_reasoning_vocabulary():
    hits_by_file = {}
    for placebo_rel, _ in SKILL_FILE_PAIRS:
        text = (PLACEBO_SKILL_DIR / placebo_rel).read_text()
        # SKILL.md's frontmatter is discovery metadata, exempt by design (see arms.py);
        # every other file, and the body of SKILL.md itself, must be clean.
        body = strip_frontmatter(text) if placebo_rel == "SKILL.md" else text
        hits = [w for w in BANNED_SUBSTRINGS if w in body.lower()]
        if hits:
            hits_by_file[placebo_rel] = hits
    assert not hits_by_file, f"placebo-skill files leak reasoning vocabulary: {hits_by_file}"


def test_placebo_skill_files_are_not_degenerate_filler():
    ratios = {}
    for placebo_rel, _ in SKILL_FILE_PAIRS:
        text = (PLACEBO_SKILL_DIR / placebo_rel).read_text()
        lines = [line for line in text.split("\n") if line.strip()]
        ratios[placebo_rel] = len(set(lines)) / len(lines)
    offenders = {k: v for k, v in ratios.items() if v < 0.6}
    assert not offenders, f"degenerate (repetitive) placebo-skill files: {offenders}"
