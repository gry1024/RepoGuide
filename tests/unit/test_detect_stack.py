"""Unit tests for detect-stack.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent.parent / "repoguide" / "scripts" / "detect-stack.py"


def run_detect_stack(repo_path: str) -> dict:
    """Run detect-stack.py as a subprocess and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), repo_path],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture
def python_repo(tmp_path):
    """Create a minimal Python repo fixture."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'\n")
    (tmp_path / "main.py").write_text("def main(): pass\n")
    (tmp_path / "utils.py").write_text("def helper(): pass\n")
    return tmp_path


@pytest.fixture
def js_repo(tmp_path):
    """Create a minimal JavaScript repo fixture."""
    (tmp_path / "package.json").write_text('{"name": "foo", "main": "index.js"}')
    (tmp_path / "index.js").write_text("function main() {}")
    return tmp_path


@pytest.fixture
def go_repo(tmp_path):
    """Create a minimal Go repo fixture."""
    (tmp_path / "go.mod").write_text("module foo\n\ngo 1.21\n")
    (tmp_path / "main.go").write_text("package main\n\nfunc main() {}\n")
    return tmp_path


def test_detect_python_repo(python_repo):
    result = run_detect_stack(str(python_repo))
    assert result["primary_language"] == "python"
    assert "pyproject.toml" in result["package_managers"]
    assert "main.py" in result["entry_points"]


def test_detect_js_repo(js_repo):
    result = run_detect_stack(str(js_repo))
    assert result["primary_language"] == "javascript"
    assert "package.json" in result["package_managers"]


def test_detect_go_repo(go_repo):
    result = run_detect_stack(str(go_repo))
    assert result["primary_language"] == "go"
    assert "go.mod" in result["package_managers"]


def test_detect_paper_pdf(tmp_path):
    """Verify paper detection when PDF is present."""
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / "paper.pdf").write_bytes(b"%PDF-1.4\n")
    result = run_detect_stack(str(tmp_path))
    assert result["paper_found"] is True
    assert "paper.pdf" in result["paper_path"]


def test_detect_no_paper(python_repo):
    """Verify paper_found=False when no paper present."""
    result = run_detect_stack(str(python_repo))
    assert result["paper_found"] is False


def test_detect_empty_repo(tmp_path):
    """Verify behavior on empty repo."""
    result = run_detect_stack(str(tmp_path))
    assert result["primary_language"] is None
    assert result["file_count_total"] == 0
