#!/usr/bin/env bash
# Test clone-if-url.sh
set -e

SCRIPT="$(cd "$(dirname "$0")/../.." && pwd)/repoguide/scripts/clone-if-url.sh"
TEST_TMP=$(mktemp -d)
trap "rm -rf $TEST_TMP" EXIT

# Test 1: Local path (already exists) - returns the path as-is
echo "=== Test 1: Local path ==="
LOCAL_REPO=$(mktemp -d)
touch "$LOCAL_REPO/.git"  # Mark as a git repo
RESULT=$("$SCRIPT" "$LOCAL_REPO" "$TEST_TMP/out1")
EXPECTED=$(cd "$LOCAL_REPO" && pwd)
if [ "$RESULT" = "$EXPECTED" ]; then
    echo "PASS: local path"
else
    echo "FAIL: expected $EXPECTED, got $RESULT"
    exit 1
fi
rm -rf "$LOCAL_REPO"

# Test 2: Empty input in non-git dir - should fail
echo "=== Test 2: Invalid input (non-git dir) ==="
NON_GIT_DIR=$(mktemp -d)
if (cd "$NON_GIT_DIR" && "$SCRIPT" "" "$TEST_TMP/out2") 2>/dev/null; then
    echo "FAIL: should have failed on empty input in non-git dir"
    rm -rf "$NON_GIT_DIR"
    exit 1
else
    echo "PASS: rejects empty input in non-git dir"
    rm -rf "$NON_GIT_DIR"
fi

# Test 3: Non-existent local path - should fail
echo "=== Test 3: Non-existent local path ==="
if "$SCRIPT" "/nonexistent/path/xyz" "$TEST_TMP/out3" 2>/dev/null; then
    echo "FAIL: should have failed on non-existent path"
    exit 1
else
    echo "PASS: rejects non-existent local path"
fi

echo "All tests passed."
