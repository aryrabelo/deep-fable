#!/usr/bin/env bash
# Installs the J-Space skill into the shared user-level Agent Skills directory,
# ~/.agents/skills -- the one path read by OMP, Codex CLI (0.147+), Cursor, and
# Gemini CLI. Use this when you want the skill in EVERY session of every agent,
# with no profile and no per-harness install.
#
# Verified 2026-08-19: a plain `omp` session outside the repo checkout does not
# see the skill until it exists here (probed before/after -- "no" then "yes").
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}/j-space"

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
# Copy, never symlink: the install must survive deletion of this checkout.
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

This is the shared Agent Skills path. One copy now serves every session of:
  OMP           (any directory, no --profile needed)
  Codex CLI     (0.147+; older builds read \$CODEX_HOME/skills -- use ./install.sh codex)
  Cursor        (also reads ~/.cursor/skills)
  Gemini CLI    (also reads ~/.gemini/skills)

Discovery is automatic from the skill's description -- nothing else is required.

Optional -- to make it always-on rather than discovered, paste this line into the
AGENTS.md your agent reads:

  When a task needs multi-step reasoning, use the j-space skill before answering.

Optional -- for a /deep-fable slash command in every OMP session, copy one file:

  cp "$REPO_ROOT/.omp/commands/deep-fable.md" ~/.omp/agent/commands/deep-fable.md

Model choice stays yours, in each agent's own settings. This installer writes none.

To undo: rm -rf "$DEST"
EOF
