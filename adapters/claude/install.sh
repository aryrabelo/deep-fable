#!/usr/bin/env bash
# Installs the J-Space skill for Claude Code. Never edits your CLAUDE.md or
# settings.json -- it copies the skill and prints the optional snippet.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/j-space"

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

Discovery is automatic: Claude Code reads the skill's description and loads it
when a task matches. Nothing else is required.

Optional -- to make it always-on, paste this line into ~/.claude/CLAUDE.md:

  When a task needs multi-step reasoning, use the j-space skill before answering.

Model choice stays yours: Claude Code picks it from its own settings
(~/.claude/settings.json -> "model"). This installer does not touch it.
EOF
