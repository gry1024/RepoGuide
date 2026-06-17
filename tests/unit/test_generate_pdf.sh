#!/usr/bin/env bash
# Test generate-pdf.sh
set -e

SCRIPT="$(cd "$(dirname "$0")/../.." && pwd)/repoguide/scripts/generate-pdf.sh"
TEST_TMP=$(mktemp -d)
trap "rm -rf $TEST_TMP" EXIT

# Test 1: Generate PDF from simple markdown
echo "=== Test 1: Simple markdown ==="
cat > "$TEST_TMP/simple.md" << 'EOF'
# Test Report

This is a **test** document.

## Section 1

Some content here.
EOF

OUTPUT=$("$SCRIPT" "$TEST_TMP/simple.md" 2>&1) || true
echo "Output: $OUTPUT"

# If a PDF was generated, verify it exists
if echo "$OUTPUT" | grep -v "PDF_GENERATION_FAILED" | grep -q ".pdf$"; then
    PDF_PATH=$(echo "$OUTPUT" | tail -1)
    if [ -f "$PDF_PATH" ]; then
        echo "PASS: PDF generated at $PDF_PATH"
    else
        echo "FAIL: PDF path reported but file not found"
        exit 1
    fi
else
    # Graceful fallback - just check script ran without crashing
    if echo "$OUTPUT" | grep -q "PDF_GENERATION_FAILED"; then
        echo "PASS: graceful fallback (no PDF tool installed, as expected)"
    else
        echo "FAIL: unexpected output: $OUTPUT"
        exit 1
    fi
fi

# Test 2: Non-existent input - should fail
echo "=== Test 2: Non-existent input ==="
if "$SCRIPT" "/nonexistent/file.md" 2>/dev/null; then
    echo "FAIL: should have failed on non-existent input"
    exit 1
else
    echo "PASS: rejects non-existent input"
fi

# Test 3: No arguments - should fail
echo "=== Test 3: No arguments ==="
if "$SCRIPT" 2>/dev/null; then
    echo "FAIL: should have failed with no arguments"
    exit 1
else
    echo "PASS: rejects no arguments"
fi

echo "All tests passed."
