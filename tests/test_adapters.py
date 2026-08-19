"""Integration tests for the non-OMP adapters: ./install.sh claude|codex."""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "install.sh"
CANONICAL_SKILL = REPO_ROOT / ".omp" / "skills" / "j-space"

# target -> env var the adapter honours for its destination root
TARGETS = {"claude": "CLAUDE_SKILLS_DIR", "codex": "AGENTS_SKILLS_DIR"}


def _run(target: str, skills_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env[TARGETS[target]] = str(skills_dir)
    return subprocess.run(
        ["bash", str(INSTALL_SH), target],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _assert_skill_installed(skills_dir: Path) -> None:
    installed = skills_dir / "j-space"
    assert (installed / "SKILL.md").read_bytes() == (CANONICAL_SKILL / "SKILL.md").read_bytes()
    for sub in ("modules", "references", "scripts"):
        assert (installed / sub).is_dir(), f"missing {sub}/ in {installed}"


def test_claude_adapter_installs_skill(tmp_path):
    result = _run("claude", tmp_path / "claude-skills")
    assert result.returncode == 0, result.stderr
    _assert_skill_installed(tmp_path / "claude-skills")
    assert "CLAUDE.md" in result.stdout


def test_codex_adapter_installs_skill(tmp_path):
    result = _run("codex", tmp_path / "agents-skills")
    assert result.returncode == 0, result.stderr
    _assert_skill_installed(tmp_path / "agents-skills")
    assert "AGENTS.md" in result.stdout


def test_adapters_idempotent(tmp_path):
    for target in TARGETS:
        skills_dir = tmp_path / target
        assert _run(target, skills_dir).returncode == 0
        second = _run(target, skills_dir)
        assert second.returncode == 0, second.stderr
        _assert_skill_installed(skills_dir)


def test_adapters_write_no_secrets(tmp_path):
    forbidden = {".env", "agent.db"}
    for target in TARGETS:
        skills_dir = tmp_path / target
        result = _run(target, skills_dir)
        assert result.returncode == 0, result.stderr
        assert "sk-or-" not in result.stdout
        for path in skills_dir.rglob("*"):
            assert path.name not in forbidden, f"unexpected secret-like file: {path}"


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
