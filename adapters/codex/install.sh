#!/usr/bin/env bash
# Installs the J-Space skill for Codex CLI. Never edits your AGENTS.md or
# config.toml -- it copies the skill and prints the optional snippets.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}/j-space"

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

~/.agents/skills is the shared Agent Skills location Codex CLI reads, so
discovery is automatic from the skill's description.

Optional -- to make it always-on, paste this line into ~/.codex/AGENTS.md:

  When a task needs multi-step reasoning, use the j-space skill before answering.

Model choice stays yours. If you want a specific model, set it yourself in
~/.codex/config.toml (shown commented -- this installer writes nothing):

  # model = "<your-model-id>"
EOF
