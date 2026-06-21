#!/usr/bin/env bash
# Install RepoGuide skill into Claude Code / Kimi Code / Codex skills directory.
#
# Usage:
#   ./install.sh                          # -> ~/.claude/skills/repoguide/
#   ./install.sh --project <dir>          # -> <dir>/.claude/skills/repoguide/
#   ./install.sh --kimi                   # -> ~/.kimi/skills/repoguide/
#   ./install.sh --codex                  # -> ~/.codex/skills/repoguide/
#   ./install.sh --kimi --project <dir>   # -> <dir>/.kimi/skills/repoguide/
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
HARNESS=".claude"
PROJECT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="${2:?missing project dir}"; shift 2 ;;
    --kimi)    HARNESS=".kimi"; shift ;;
    --codex)   HARNESS=".codex"; shift ;;
    -h|--help)
      echo "Usage: ./install.sh [--project <dir>] [--kimi|--codex]"
      echo ""
      echo "Install RepoGuide skill into an agent harness skills directory."
      echo ""
      echo "  (default)            ~/.claude/skills/repoguide/"
      echo "  --project <dir>      <dir>/.claude/skills/repoguide/"
      echo "  --kimi               ~/.kimi/skills/repoguide/"
      echo "  --codex              ~/.codex/skills/repoguide/"
      echo ""
      echo "Combine --project with --kimi/--codex for project-local non-Claude installs."
      exit 0
      ;;
    *) echo "Unknown flag: $1 (use --help)"; exit 1 ;;
  esac
done

if [ -n "$PROJECT" ]; then
  DEST="$PROJECT/$HARNESS/skills/repoguide"
else
  DEST="$HOME/$HARNESS/skills/repoguide"
fi

echo "RepoGuide -> $DEST"
mkdir -p "$DEST"

# Copy skill files and supporting directories
cp "$SRC/skill.md" "$DEST/"
cp -R "$SRC/references" "$DEST/"
cp -R "$SRC/sub-skills" "$DEST/"

echo ""
echo "RepoGuide installed to $DEST"
echo ""
echo "Usage: in any repo, say \"下载 https://github.com/gry1024/RepoGuide 并执行这个 skill\""
echo "       or \"分析 https://github.com/owner/repo\""
