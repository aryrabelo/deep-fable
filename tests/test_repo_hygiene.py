"""Static hygiene checks: no secrets or credential files ship in the repo."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_NAMES = {".env", "agent.db"}
FORBIDDEN_SUFFIXES = (".db-wal",)
KEY_PREFIX = "sk-or-"


def _iter_repo_files():
    for path in REPO_ROOT.rglob("*"):
        if ".git" in path.relative_to(REPO_ROOT).parts:
            continue
        if path.is_file():
            yield path


def test_no_secret_files_anywhere_in_repo():
    offenders = [
        path
        for path in _iter_repo_files()
        if path.name in FORBIDDEN_NAMES or path.name.endswith(FORBIDDEN_SUFFIXES)
    ]
    assert not offenders, f"secret-like files present: {offenders}"


def test_no_openrouter_key_prefix_in_profile_or_install():
    targets = [REPO_ROOT / "install.sh", *((REPO_ROOT / "profile").rglob("*"))]
    offenders = []
    for path in targets:
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="ignore")
        except (UnicodeDecodeError, OSError):
            continue
        if KEY_PREFIX in text:
            offenders.append(path)
    assert not offenders, f"possible leaked API key prefix in: {offenders}"
