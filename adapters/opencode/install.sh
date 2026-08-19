#!/usr/bin/env bash
# Installs the J-Space skill for OpenCode. Never edits your opencode.json --
# it copies the skill and prints the optional snippet.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# OPENCODE_CONFIG_DIR is OpenCode's own override; unset, it falls back to
# ~/.config/opencode (itself relocatable via XDG_CONFIG_HOME, which OpenCode
# also honors -- not read directly here, only via the OS/user's environment).
DEST="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}/skills/j-space"

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

Discovery is automatic: OpenCode reads the skill's description and loads it
when a task matches. Nothing else is required.

Optional -- to make it always-on, paste this line into your AGENTS.md:

  When a task needs multi-step reasoning, use the j-space skill before answering.

Model choice stays yours: OpenCode picks it from its own config
(opencode.json). This installer does not touch it.
EOF
