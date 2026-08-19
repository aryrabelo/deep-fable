"""Integration tests for install.sh: installs the jspace OMP profile."""
import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "install.sh"


def _make_omp_stub(bin_dir: Path, argv_log: Path) -> None:
    """Fake `omp` binary that records its argv and exits 0."""
    stub = bin_dir / "omp"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" >> "{argv_log}"\n'
        "exit 0\n"
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_install(tmp_path: Path, profile_dir: Path, bin_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["OMP_PROFILE_DIR"] = str(profile_dir)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_install_copies_profile_and_skill_and_registers_alias(tmp_path):
    profile_dir = tmp_path / "profile-out"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "omp_argv.log"
    _make_omp_stub(bin_dir, argv_log)

    result = _run_install(tmp_path, profile_dir, bin_dir)
    assert result.returncode == 0, result.stderr

    config = profile_dir / "config.yml"
    append_system = profile_dir / "APPEND_SYSTEM.md"
    assert config.read_bytes() == (REPO_ROOT / "profile" / "config.yml").read_bytes()
    assert append_system.read_bytes() == (REPO_ROOT / "profile" / "APPEND_SYSTEM.md").read_bytes()

    skill_md = profile_dir / "skills" / "j-space" / "SKILL.md"
    assert skill_md.exists()

    assert argv_log.exists()
    invocation = argv_log.read_text()
    assert "--alias" in invocation
    assert "deep-fable" in invocation


def test_install_is_idempotent(tmp_path):
    profile_dir = tmp_path / "profile-out"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "omp_argv.log"
    _make_omp_stub(bin_dir, argv_log)

    first = _run_install(tmp_path, profile_dir, bin_dir)
    assert first.returncode == 0, first.stderr
    second = _run_install(tmp_path, profile_dir, bin_dir)
    assert second.returncode == 0, second.stderr

    assert (profile_dir / "skills" / "j-space" / "SKILL.md").exists()


def test_install_never_writes_secrets(tmp_path):
    profile_dir = tmp_path / "profile-out"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "omp_argv.log"
    _make_omp_stub(bin_dir, argv_log)

    result = _run_install(tmp_path, profile_dir, bin_dir)
    assert result.returncode == 0, result.stderr

    forbidden_names = {".env", "agent.db"}
    for path in profile_dir.rglob("*"):
        assert path.name not in forbidden_names, f"unexpected secret-like file: {path}"
