#!/usr/bin/env bash
# Installs the J-Space skill for Codex CLI. Never edits your AGENTS.md or
# config.toml -- it copies the skill and prints the optional snippets.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Codex CLI has read $HOME/.agents/skills (personal/user-scope skills, next to
# the deprecated $CODEX_HOME/skills) since openai/codex commit e24058b7a872
# ("feat: Read personal skills from .agents/skills", PR #10437, 2026-02-02),
# first shipped in tag rust-v0.95.0 (2026-02-04) and present unconditionally
# (no feature flag) in every tag since, including the currently installed
# rust-v0.146.0 -- verified two ways on this machine: (1) source at tag
# rust-v0.146.0, codex-rs/core-skills/src/loader.rs unconditionally adds
# `home_dir.join(".agents").join("skills")` as a User-scope root; (2)
# empirically, `codex debug prompt-input` (installed codex-cli 0.146.0) lists
# a probe skill placed under $HOME/.agents/skills. Below that cutoff, only
# $CODEX_HOME/skills (default ~/.codex/skills) is read.
CUTOFF_MINOR=95

codex_minor_version() {
  command -v codex >/dev/null 2>&1 || return 1
  codex --version 2>/dev/null | sed -nE 's/^codex-cli ([0-9]+)\.([0-9]+)\..*/\2/p'
}

DEFAULT_ROOT="$HOME/.agents/skills"
DEFAULT_REASON="the installed Codex build's version could not be determined, so the documented, forward-compatible location was used"
if minor="$(codex_minor_version)" && [ -n "$minor" ]; then
  if [ "$minor" -ge "$CUTOFF_MINOR" ]; then
    DEFAULT_REASON="installed Codex (0.$minor.x) reads \$HOME/.agents/skills"
  else
    DEFAULT_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
    DEFAULT_REASON="installed Codex (0.$minor.x) predates .agents/skills support (added in 0.$CUTOFF_MINOR.0), so \$CODEX_HOME/skills was used instead"
  fi
fi

DEST="${AGENTS_SKILLS_DIR:-$DEFAULT_ROOT}/j-space"
if [ -n "${AGENTS_SKILLS_DIR:-}" ]; then
  DEFAULT_REASON="AGENTS_SKILLS_DIR is set"
fi

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

$DEFAULT_REASON, so discovery is automatic from the skill's description.

Optional -- to make it always-on, paste this line into ~/.codex/AGENTS.md:

  When a task needs multi-step reasoning, use the j-space skill before answering.

Model choice stays yours. If you want a specific model, set it yourself in
~/.codex/config.toml (shown commented -- this installer writes nothing):

  # model = "<your-model-id>"
EOF
