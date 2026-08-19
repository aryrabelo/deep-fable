"""Integration tests for the non-OMP adapters: ./install.sh claude|codex|opencode|cursor|gemini."""
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "install.sh"
CANONICAL_SKILL = REPO_ROOT / ".omp" / "skills" / "j-space"

# target -> (env var the adapter honours, skill path relative to that env dir,
#            a string the printed paste-yourself snippet must contain)
TARGETS = {
    "claude": ("CLAUDE_SKILLS_DIR", "j-space", "CLAUDE.md"),
    "codex": ("AGENTS_SKILLS_DIR", "j-space", "AGENTS.md"),
    "opencode": ("OPENCODE_CONFIG_DIR", "skills/j-space", "AGENTS.md"),
    "cursor": ("CURSOR_SKILLS_DIR", "j-space", "alwaysApply"),
    "gemini": ("GEMINI_SKILLS_DIR", "j-space", "GEMINI.md"),
}


def _run(target: str, root: Path) -> subprocess.CompletedProcess:
    env_var, _, _ = TARGETS[target]
    env = dict(os.environ)
    env[env_var] = str(root)
    return subprocess.run(
        ["bash", str(INSTALL_SH), target],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _installed_skill(target: str, root: Path) -> Path:
    _, rel, _ = TARGETS[target]
    return root / rel


@pytest.mark.parametrize("target", sorted(TARGETS))
def test_adapter_installs_skill_from_canonical_source(target, tmp_path):
    result = _run(target, tmp_path)
    assert result.returncode == 0, result.stderr

    installed = _installed_skill(target, tmp_path)
    assert (installed / "SKILL.md").read_bytes() == (CANONICAL_SKILL / "SKILL.md").read_bytes()
    for sub in ("modules", "references", "scripts"):
        assert (installed / sub).is_dir(), f"missing {sub}/ in {installed}"


@pytest.mark.parametrize("target", sorted(TARGETS))
def test_adapter_prints_snippet_and_never_leaks_secrets(target, tmp_path):
    result = _run(target, tmp_path)
    assert result.returncode == 0, result.stderr

    _, _, expected_snippet = TARGETS[target]
    assert expected_snippet in result.stdout
    assert "sk-or-" not in result.stdout

    forbidden = {".env", "agent.db"}
    for path in tmp_path.rglob("*"):
        assert path.name not in forbidden, f"unexpected secret-like file: {path}"


@pytest.mark.parametrize("target", sorted(TARGETS))
def test_adapter_is_idempotent(target, tmp_path):
    assert _run(target, tmp_path).returncode == 0
    second = _run(target, tmp_path)
    assert second.returncode == 0, second.stderr
    assert (_installed_skill(target, tmp_path) / "SKILL.md").is_file()


def test_unknown_target_fails():
    result = subprocess.run(
        ["bash", str(INSTALL_SH), "nope"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "Unknown target" in result.stderr


def test_shared_skills_symlink():
    shared = REPO_ROOT / ".agents" / "skills" / "j-space"
    assert shared.is_symlink(), f"{shared} should be a committed symlink"
    assert os.path.realpath(shared) == os.path.realpath(CANONICAL_SKILL)
