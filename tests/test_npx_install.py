"""Guards for `npx skills add aryrabelo/deep-fable` (skills.sh CLI, vercel-labs/skills).

The CLI discovers skills in two phases: it first scans a fixed list of conventional agent
skill directories, and only if that finds nothing does it recursively walk the repo. Our
canonical skill lives at `.omp/skills/j-space/`, which is NOT on the conventional list, so
discovery depends on the recursive fallback running. These tests pin the two properties that
keep the npx install honest. Verified against skills CLI v1.5.23.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / ".omp" / "skills" / "j-space" / "SKILL.md"

# Directories the CLI scans BEFORE falling back to a recursive walk. A real skill directory
# under any of these would satisfy phase one and silently drop `.omp/skills/j-space` from
# discovery. A symlink does not count: Node's readdir(withFileTypes) reports isDirectory()
# false for symlink entries, so the CLI skips them during discovery.
PRIORITY_SKILL_DIRS = (
    "skills",
    ".agents/skills",
    ".claude/skills",
    ".cursor/skills",
    ".codex/skills",
    ".gemini/skills",
    ".opencode/skills",
)

NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)


def _real_skill_md_files():
    for path in REPO_ROOT.rglob("SKILL.md"):
        if ".git" in path.relative_to(REPO_ROOT).parts:
            continue
        # Skip anything reached through a symlink; the CLI ignores those too.
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            continue
        if path.is_file():
            yield path


def test_every_j_space_skill_md_in_repo_is_byte_identical_to_canonical():
    """Whatever copy the installer picks up, users must get the same skill.

    The benchmark workdirs under `model-eval/work/` contain copies of this SKILL.md (task D
    operated on the skill's own scripts). The CLI dedupes discovered skills by frontmatter
    `name`, so a *modified* copy declaring `name: j-space` could be the one that ships.
    """
    canonical_bytes = CANONICAL.read_bytes()
    offenders = []
    for path in _real_skill_md_files():
        text = path.read_text(errors="ignore")
        match = NAME_RE.search(text)
        if match and match.group(1).strip().strip("\"'") == "j-space":
            if path.read_bytes() != canonical_bytes:
                offenders.append(path.relative_to(REPO_ROOT))
    assert not offenders, f"SKILL.md files claiming name 'j-space' but differing from canonical: {offenders}"


def test_no_conventional_skill_dir_shadows_the_canonical_one():
    """Keep the recursive fallback reachable.

    Adding a real skill directory under any conventional path (e.g. `.claude/skills/foo/`)
    would make the CLI stop after phase one and never reach `.omp/skills/j-space`. If a
    future layout change needs one of these paths, move the canonical skill there instead and
    delete this test deliberately -- do not add a second location alongside it.
    """
    offenders = []
    for rel in PRIORITY_SKILL_DIRS:
        base = REPO_ROOT / rel
        if not base.is_dir():
            continue
        for child in base.iterdir():
            if child.is_symlink():
                continue  # invisible to the CLI's discovery scan
            if child.is_dir() and (child / "SKILL.md").is_file():
                offenders.append(f"{rel}/{child.name}")
    assert not offenders, (
        "real skill dirs on the CLI's priority path would hide .omp/skills/j-space "
        f"from `npx skills`: {offenders}"
    )


def test_canonical_skill_has_discoverable_frontmatter():
    """The CLI reads `name` and `description` from frontmatter; both must be present."""
    text = CANONICAL.read_text()
    assert text.startswith("---\n"), "SKILL.md must open with YAML frontmatter"
    match = NAME_RE.search(text)
    assert match and match.group(1).strip() == "j-space"
    assert re.search(r"^description:\s*\S", text, re.MULTILINE), "frontmatter needs a description"
