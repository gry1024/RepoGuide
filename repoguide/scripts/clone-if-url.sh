#!/usr/bin/env bash
# clone-if-url.sh - Normalize a repo reference to a local path.
# Usage: clone-if-url.sh <repo-ref> <target-dir>
#   repo-ref: local path, GitHub URL, or empty (uses current dir)
#   target-dir: where to clone if URL
# Output: absolute path to repo (on stdout)

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <repo-ref> [target-dir]" >&2
    exit 1
fi

REPO_REF="$1"
TARGET_DIR="${2:-$(pwd)}"

if [ -z "$REPO_REF" ]; then
    # Empty: use current directory
    if [ -d ".git" ]; then
        REPO_ROOT=$(git rev-parse --show-toplevel)
        echo "$REPO_ROOT"
    else
        echo "Error: current directory is not a git repository" >&2
        exit 1
    fi
    exit 0
fi

# Detect URL
if [[ "$REPO_REF" =~ ^https?://github\.com/ ]]; then
    # GitHub URL: clone to target-dir
    REPO_NAME=$(basename "$REPO_REF" .git)
    TARGET_PATH="$TARGET_DIR/repoguide-$REPO_NAME"
    if [ -d "$TARGET_PATH/.git" ]; then
        echo "Reusing existing clone at $TARGET_PATH" >&2
    else
        mkdir -p "$TARGET_DIR"
        git clone --depth 1 "$REPO_REF" "$TARGET_PATH"
    fi
    echo "$TARGET_PATH"
    exit 0
fi

# Local path
if [ ! -e "$REPO_REF" ]; then
    echo "Error: path does not exist: $REPO_REF" >&2
    exit 1
fi
# Resolve to absolute path
cd "$REPO_REF" || { echo "Error: cannot cd to $REPO_REF" >&2; exit 1; }
pwd
