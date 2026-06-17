#!/usr/bin/env python3
from __future__ import annotations
"""Detect tech stack of a code repository.

Usage: python detect-stack.py <repo_path>
Output: JSON to stdout
"""
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

# Package manager files and entry patterns for each language
LANGUAGE_SIGNALS = {
    "python": {
        "package_files": [
            "pyproject.toml", "requirements.txt", "requirements-dev.txt",
            "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock",
            "conda.yml", "environment.yml",
        ],
        "entry_patterns": ["main.py", "app.py", "__main__.py", "cli.py", "run.py"],
        "exts": {".py"},
    },
    "javascript": {
        "package_files": [
            "package.json", "package-lock.json", "yarn.lock",
            "pnpm-lock.yaml", "bun.lockb",
        ],
        "entry_patterns": ["index.js", "index.mjs", "index.cjs", "app.js", "server.js", "main.js"],
        "exts": {".js", ".mjs", ".cjs"},
    },
    "typescript": {
        "package_files": [
            "tsconfig.json", "package.json", "package-lock.json",
            "yarn.lock", "pnpm-lock.yaml",
        ],
        "entry_patterns": ["index.ts", "app.ts", "main.ts", "src/index.ts", "src/main.ts"],
        "exts": {".ts", ".tsx"},
    },
    "java": {
        "package_files": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
        "entry_patterns": ["Application.java", "Main.java"],
        "exts": {".java"},
    },
    "go": {
        "package_files": ["go.mod", "go.sum"],
        "entry_patterns": ["main.go"],
        "exts": {".go"},
    },
    "rust": {
        "package_files": ["Cargo.toml", "Cargo.lock"],
        "entry_patterns": ["src/main.rs", "src/lib.rs", "main.rs", "lib.rs"],
        "exts": {".rs"},
    },
}

IGNORE_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "env",
               "dist", "build", "target", "__pycache__", ".pytest_cache",
               ".mypy_cache", ".tox", "out"}


def detect_paper(repo_path: Path) -> Tuple[bool, Optional[str]]:
    """Detect if a paper PDF or tex file is present."""
    for pattern in ["*.pdf", "*.tex", "paper*", "Paper*"]:
        matches = sorted(repo_path.glob(pattern))
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


def collect_files(repo_path: Path):
    """Collect all relevant files and compute extension stats."""
    total = 0
    by_ext: dict[str, int] = {}
    files: list[Path] = []
    for item in repo_path.rglob("*"):
        if not item.is_file():
            continue
        if any(p in item.parts for p in IGNORE_DIRS):
            continue
        files.append(item)
        total += 1
        ext = item.suffix.lstrip(".") or "no_ext"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return files, total, by_ext


def detect_language(repo_path: Path, files: list[Path]) -> Tuple[Optional[str], list, list, list]:
    """Detect primary language, package managers, entry points, all languages present."""
    package_managers: list[str] = []
    entry_points: list[str] = []
    languages_present: list[str] = []

    # Signal 1: package files
    for lang, signals in LANGUAGE_SIGNALS.items():
        found_pkg = [pf for pf in signals["package_files"] if (repo_path / pf).exists()]
        if found_pkg:
            package_managers.extend(found_pkg)
            if lang not in languages_present:
                languages_present.append(lang)
        for ep in signals["entry_patterns"]:
            candidate = repo_path / ep
            if candidate.exists():
                rel = candidate.relative_to(repo_path).as_posix()
                if rel not in entry_points:
                    entry_points.append(rel)

    # Signal 2: file extensions (only add languages not already detected)
    ext_counts: dict[str, int] = {}
    for f in files:
        ext_counts[f.suffix] = ext_counts.get(f.suffix, 0) + 1
    for lang, signals in LANGUAGE_SIGNALS.items():
        if lang in languages_present:
            continue
        if any(ext_counts.get(ext, 0) > 0 for ext in signals["exts"]):
            languages_present.append(lang)

    # Primary: first language with package file, else first by file count
    primary = None
    if languages_present:
        primary = languages_present[0]
        # Re-order by file count if no package file was found for the first one
        first_pkg = any((repo_path / pf).exists() for pf in LANGUAGE_SIGNALS[primary]["package_files"])
        if not first_pkg:
            by_lang_count = {
                lang: sum(ext_counts.get(ext, 0) for ext in LANGUAGE_SIGNALS[lang]["exts"])
                for lang in languages_present
            }
            primary = max(languages_present, key=lambda lang: (by_lang_count[lang], lang))

    return primary, package_managers, entry_points, languages_present


def find_module_candidates(repo_path: Path, files: list[Path], primary: Optional[str]) -> list[str]:
    """Find directories that look like modules."""
    candidates: set[str] = set()
    if primary == "python":
        for f in files:
            if f.name == "__init__.py":
                candidates.add(f.parent.relative_to(repo_path).as_posix())
    elif primary in ("javascript", "typescript"):
        for f in files:
            if f.name in ("index.js", "index.ts", "index.mjs", "index.cjs"):
                candidates.add(f.parent.relative_to(repo_path).as_posix())
    elif primary == "rust":
        if (repo_path / "src").is_dir():
            candidates.add("src")
    elif primary == "go":
        for f in files:
            if f.suffix == ".go":
                candidates.add(f.parent.relative_to(repo_path).as_posix())
    elif primary == "java":
        for f in files:
            if f.suffix == ".java":
                candidates.add(f.parent.relative_to(repo_path).as_posix())

    # Always include top-level source-like dirs as fallback
    for child in repo_path.iterdir():
        if child.is_dir() and child.name not in IGNORE_DIRS and not child.name.startswith("."):
            if any((child / f).exists() for f in ["__init__.py", "index.js", "index.ts"]):
                candidates.add(child.relative_to(repo_path).as_posix())

    return sorted(candidates)


def seed_core_files(repo_path: Path, entry_points: list[str], package_managers: list[str]) -> list[str]:
    """Initial seed of core files based on entry points and package manifests."""
    seeds: set[str] = set(entry_points)
    for pm in package_managers:
        if (repo_path / pm).is_file():
            seeds.add(pm)
    # Language-specific conventional files
    for name in ["README.md", "README", "Makefile", "Dockerfile"]:
        if (repo_path / name).exists():
            seeds.add(name)
    return sorted(seeds)


def main():
    if len(sys.argv) != 2:
        print("Usage: detect-stack.py <repo_path>", file=sys.stderr)
        sys.exit(1)
    repo_path = Path(sys.argv[1]).resolve()
    if not repo_path.exists():
        print(f"Error: path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    files, file_count_total, file_count_by_ext = collect_files(repo_path)
    primary, package_managers, entry_points, languages = detect_language(repo_path, files)
    paper_found, paper_path = detect_paper(repo_path)
    module_candidates = find_module_candidates(repo_path, files, primary)
    core_files_seed = seed_core_files(repo_path, entry_points, package_managers)

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
        "module_candidates": module_candidates,
        "core_files_seed": core_files_seed,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
