#!/usr/bin/env bash
# Installs the J-Space skill for Gemini CLI. Never edits your GEMINI.md or
# settings.json -- it copies the skill and prints the optional snippet.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${GEMINI_SKILLS_DIR:-$HOME/.gemini/skills}/j-space"

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -RL "$REPO_ROOT/.omp/skills/j-space" "$DEST"

cat <<EOF
Installed the J-Space skill at $DEST

No gemini-extension.json or extension bundle is needed. Gemini CLI's docs
list four discovery tiers (built-in, extension, user, workspace); a plain
skill directory under ~/.gemini/skills/ already sits in the "user" tier, one
level above extensions -- packaging one would be pure overhead.

Discovery is automatic: Gemini CLI reads the skill's description and
activates it when a task matches. Nothing else is required.

Optional -- to make it always-on, paste this line into ~/GEMINI.md:

  When a task needs multi-step reasoning, use the j-space skill before answering.

Note: ~/.agents/skills is an alias Gemini CLI also reads for user skills, and
Codex CLI reads that same path -- if you already ran the codex adapter, this
one may be redundant.

Model choice stays yours: Gemini CLI picks it from its own settings. This
installer does not touch them.
EOF
