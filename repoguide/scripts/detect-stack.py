#!/usr/bin/env python3
"""Detect tech stack of a code repository.

Usage: python detect-stack.py <repo_path>
Output: JSON to stdout
"""
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

# Package manager files for each language
LANGUAGE_SIGNALS = {
    "python": {
        "package_files": [
            "pyproject.toml", "requirements.txt", "requirements-dev.txt",
            "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock",
            "conda.yml", "environment.yml",
        ],
        "entry_patterns": ["main.py", "app.py", "__main__.py", "cli.py", "run.py"],
    },
    "javascript": {
        "package_files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "entry_patterns": ["index.js", "app.js", "server.js", "main.js"],
    },
    "typescript": {
        "package_files": ["tsconfig.json"],
        "entry_patterns": ["index.ts", "app.ts", "main.ts", "src/index.ts"],
    },
    "java": {
        "package_files": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
        "entry_patterns": ["Application.java", "Main.java", "src/main/java"],
    },
    "go": {
        "package_files": ["go.mod", "go.sum"],
        "entry_patterns": ["main.go", "cmd/", "app.go"],
    },
    "rust": {
        "package_files": ["Cargo.toml", "Cargo.lock"],
        "entry_patterns": ["src/main.rs", "src/lib.rs", "main.rs", "lib.rs"],
    },
}

IGNORE_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "env",
               "dist", "build", "target", "__pycache__", ".pytest_cache",
               ".mypy_cache", ".tox", "out"}


def detect_paper(repo_path: Path) -> Tuple[bool, Optional[str]]:
    """Detect if a paper PDF or tex file is present."""
    for pattern in ["*.pdf", "*.tex", "paper*", "Paper*"]:
        matches = list(repo_path.glob(pattern))
        if matches:
            return True, str(matches[0])
    # Check README for arxiv link
    for readme in repo_path.glob("README*"):
        try:
            content = readme.read_text(encoding="utf-8", errors="ignore")
            if "arxiv.org" in content.lower():
                return True, str(readme)
        except Exception:
            pass
    return False, None


def detect_language(repo_path: Path) -> Tuple[Optional[str], list, list, list]:
    """Detect primary language, package managers, entry points, all languages present."""
    package_managers: list[str] = []
    entry_points: list[str] = []
    languages_present: list[str] = []

    for lang, signals in LANGUAGE_SIGNALS.items():
        has_package_file = False
        for pf in signals["package_files"]:
            if (repo_path / pf).exists():
                package_managers.append(pf)
                has_package_file = True
        if has_package_file:
            languages_present.append(lang)
        for ep in signals["entry_patterns"]:
            if (repo_path / ep).exists():
                entry_points.append(ep)

    primary = languages_present[0] if languages_present else None
    return primary, package_managers, entry_points, languages_present


def count_files(repo_path: Path) -> Tuple[int, dict]:
    """Count total files and files by extension."""
    total = 0
    by_ext: dict[str, int] = {}
    for item in repo_path.rglob("*"):
        if item.is_file() and not any(p in item.parts for p in IGNORE_DIRS):
            total += 1
            ext = item.suffix.lstrip(".") or "no_ext"
            by_ext[ext] = by_ext.get(ext, 0) + 1
    return total, by_ext


def main():
    if len(sys.argv) != 2:
        print("Usage: detect-stack.py <repo_path>", file=sys.stderr)
        sys.exit(1)
    repo_path = Path(sys.argv[1]).resolve()
    if not repo_path.exists():
        print(f"Error: path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    primary, package_managers, entry_points, languages = detect_language(repo_path)
    paper_found, paper_path = detect_paper(repo_path)
    file_count_total, file_count_by_ext = count_files(repo_path)

    result = {
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "primary_language": primary,
        "all_languages": languages,
        "package_managers": package_managers,
        "entry_points": entry_points,
        "paper_found": paper_found,
        "paper_path": paper_path,
        "file_count_total": file_count_total,
        "file_count_by_ext": file_count_by_ext,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
