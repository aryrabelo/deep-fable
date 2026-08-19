#!/usr/bin/env bash
# Installs the "jspace" OMP profile: DeepSeek default model + the vendored
# J-Space skill loaded on every session, aliased to `deep-fable`.
set -euo pipefail

# Target dispatch. No argument -> the OMP profile flow below, unchanged.
TARGET="${1:-omp}"
case "$TARGET" in
  omp) : ;;
  agents|claude|codex|opencode|cursor|gemini) exec "$(dirname "${BASH_SOURCE[0]}")/adapters/$TARGET/install.sh" ;;
  *) echo "Unknown target: $TARGET (expected: omp, agents, claude, codex, opencode, cursor, gemini)" >&2; exit 1 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="${OMP_PROFILE_DIR:-$HOME/.omp/profiles/jspace/agent}"
SKILLS_DIR="$PROFILE_DIR/skills"
COMMANDS_DIR="$PROFILE_DIR/commands"

mkdir -p "$PROFILE_DIR" "$SKILLS_DIR" "$COMMANDS_DIR"

cp "$SCRIPT_DIR/profile/config.yml" "$PROFILE_DIR/config.yml"
cp "$SCRIPT_DIR/profile/APPEND_SYSTEM.md" "$PROFILE_DIR/APPEND_SYSTEM.md"

# Vendor the skill by copy (not symlink) so the profile survives deletion of
# this repo checkout.
rm -rf "$SKILLS_DIR/j-space"
cp -R "$SCRIPT_DIR/.omp/skills/j-space" "$SKILLS_DIR/j-space"

# The /deep-fable slash command, so the discipline can also be invoked on demand
# mid-session instead of only at boot.
cp "$SCRIPT_DIR/.omp/commands/deep-fable.md" "$COMMANDS_DIR/deep-fable.md"

echo "Installed jspace profile at $PROFILE_DIR"

if SHELL="${SHELL:-/bin/zsh}" omp --profile jspace --alias deep-fable; then
  echo "Registered the 'deep-fable' shell alias via omp."
else
  echo "Warning: could not register the 'deep-fable' alias automatically (is 'omp' installed and on PATH?)." >&2
  echo "You can register it later by running: omp --profile jspace --alias deep-fable" >&2
fi

cat <<'EOF'

Next steps:
  1. Authenticate with OpenRouter (required for the DeepSeek default model):
       export OPENROUTER_API_KEY=<your key>
     or run `omp` once and add the key through its interactive auth flow.
  2. Start a J-Space session with either:
       deep-fable
     or:
       omp --profile jspace
EOF
