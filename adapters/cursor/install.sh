#!/usr/bin/env bash
# Installs the J-Space skill for Cursor. Never edits your rules, cli-config.json,
# or any other Cursor config -- it copies the skill and prints the optional
# rule body and model caveat.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# Default verified against https://cursor.com/docs/skills: Cursor auto-discovers
# skills from project-level .agents/skills/ and .cursor/skills/, and from
# user-level (global) ~/.agents/skills/ and ~/.cursor/skills/. This installer
# targets the user-level ~/.cursor/skills, mirroring the Claude/Codex adapters.
DEST="${CURSOR_SKILLS_DIR:-$HOME/.cursor/skills}/j-space"

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

Discovery is automatic: Cursor reads the skill's description at startup and
loads it when a task matches. Nothing else is required.

Optional -- to make it always-on, create .cursor/rules/j-space.mdc yourself
with this body (Cursor rule frontmatter supports only description, globs,
and alwaysApply -- no model field):

  ---
  description: Use the j-space skill for multi-step reasoning
  alwaysApply: true
  ---
  When a task needs multi-step reasoning, use the j-space skill before answering.

Model choice: no repo-committed file can pin Cursor's primary-session model.
Project .cursor/cli.json is permissions-only; the model lives in your global
~/.cursor/cli-config.json or is set live with the /model command -- this
installer does not touch either. A committed .cursor/agents/<name>.md
subagent file CAN carry a "model:" field, but that is a separate, explicit
subagent invocation, not a change to this installer.
EOF
