#!/usr/bin/env bash
# End-to-end test: verify RepoGuide scaffolding is internally consistent.
# This test does NOT invoke an LLM agent (which is what SKILL.md is for).
# Instead it verifies that all references, scripts, and templates exist and parse.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "=== E2E: Verifying RepoGuide scaffolding ==="

# Test 1: All required files exist
echo "--- Test 1: File presence ---"
REQUIRED_FILES=(
    "repoguide/SKILL.md"
    "repoguide/SKILL.codex.md"
    "repoguide/SKILL.kimi.md"
    "repoguide/references/language-profiles.md"
    "repoguide/references/depth-rules.md"
    "repoguide/references/report-template.md"
    "repoguide/scripts/detect-stack.py"
    "repoguide/scripts/clone-if-url.sh"
    "repoguide/scripts/generate-pdf.sh"
    "tests/unit/test_detect_stack.py"
    "tests/unit/test_clone_if_url.sh"
    "tests/unit/test_generate_pdf.sh"
    "tests/fixtures/small-python/main.py"
    "tests/fixtures/medium-ml-with-paper/main.py"
    "tests/fixtures/multi-lang/app.py"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$f" ]; then
        echo "FAIL: missing required file: $f"
        exit 1
    fi
done
echo "PASS: all required files present"

# Test 2: detect-stack.py works on all fixtures
echo "--- Test 2: detect-stack on all fixtures ---"
for fixture in tests/fixtures/*/; do
    if [ -d "$fixture" ]; then
        output=$(python repoguide/scripts/detect-stack.py "$fixture" 2>&1)
        if [ $? -ne 0 ]; then
            echo "FAIL: detect-stack failed on $fixture"
            echo "$output"
            exit 1
        fi
        echo "PASS: detect-stack on $fixture"
    fi
done

# Test 3: SKILL.md contains all required sections
echo "--- Test 3: SKILL.md structure ---"
SKILL_SECTIONS=(
    "## 触发条件"
    "## Phase 0: 输入归一化"
    "## Phase 1: 探查"
    "## Phase 2: 并行深度分析"
    "## Phase 3: 汇总与输出"
    "## 错误处理"
)
for section in "${SKILL_SECTIONS[@]}"; do
    if ! grep -qF "$section" repoguide/SKILL.md; then
        echo "FAIL: SKILL.md missing section: $section"
        exit 1
    fi
done
echo "PASS: SKILL.md has all required sections"

# Test 4: All scripts are executable
echo "--- Test 4: Scripts executable ---"
for script in repoguide/scripts/*.sh; do
    if [ ! -x "$script" ]; then
        echo "FAIL: $script is not executable"
        exit 1
    fi
done
echo "PASS: all shell scripts executable"

# Test 5: All references are non-empty
echo "--- Test 5: References non-empty ---"
for ref in repoguide/references/*.md; do
    if [ ! -s "$ref" ]; then
        echo "FAIL: $ref is empty"
        exit 1
    fi
done
echo "PASS: all references non-empty"

# Test 6: Unit tests still pass
echo "--- Test 6: Python unit tests ---"
python -m pytest tests/unit/test_detect_stack.py -v
echo "PASS: detect-stack unit tests pass"

# Test 7: Shell unit tests still pass
echo "--- Test 7: Shell unit tests ---"
bash tests/unit/test_clone_if_url.sh
echo "PASS: clone-if-url tests pass"

bash tests/unit/test_generate_pdf.sh
echo "PASS: generate-pdf tests pass"

echo ""
echo "=== All E2E tests passed ==="
echo "RepoGuide scaffolding is ready for LLM-driven execution."
