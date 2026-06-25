---
name: repoguide-tool-detect-stack
description: RepoGuide 的技术栈识别方法，输出仓库画像 JSON，全部以代码片段形式写在 md 中由 agent 执行。
---

# RepoGuide · 仓库画像

## 执行代码

由 profiler agent 在目标仓库根目录执行以下 Python 代码：

```python
import json
import os
import re
from pathlib import Path

REPO_PATH = Path("/path/to/repo").resolve()
WORK_DIR = Path(os.environ.get("WORK_DIR", str(REPO_PATH.parent / "_repoguide"))).resolve()
DEPTH = os.environ.get("REPOGUIDE_DEPTH", "standard")

LANGUAGE_SIGNALS = {
    "python": {
        "package_files": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock"],
        "entry_patterns": ["main.py", "app.py", "__main__.py", "cli.py", "run.py"],
        "exts": [".py"],
    },
    "javascript": {
        "package_files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"],
        "entry_patterns": ["index.js", "index.mjs", "index.cjs", "app.js", "server.js", "main.js"],
        "exts": [".js", ".mjs", ".cjs"],
    },
    "typescript": {
        "package_files": ["tsconfig.json", "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "entry_patterns": ["index.ts", "app.ts", "main.ts", "src/index.ts", "src/main.ts"],
        "exts": [".ts", ".tsx"],
    },
    "java": {
        "package_files": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
        "entry_patterns": ["Application.java", "Main.java"],
        "exts": [".java"],
    },
    "go": {
        "package_files": ["go.mod", "go.sum"],
        "entry_patterns": ["main.go"],
        "exts": [".go"],
    },
    "rust": {
        "package_files": ["Cargo.toml", "Cargo.lock"],
        "entry_patterns": ["src/main.rs", "src/lib.rs", "main.rs", "lib.rs"],
        "exts": [".rs"],
    },
}

IGNORE_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "env", "dist", "build", "target", "__pycache__", ".pytest_cache"}

def collect_files(repo_path):
    files = []
    by_ext = {}
    for item in repo_path.rglob("*"):
        if not item.is_file():
            continue
        if any(p in item.parts for p in IGNORE_DIRS):
            continue
        files.append(item)
        ext = item.suffix.lstrip(".") or "no_ext"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return files, len(files), by_ext

def detect_paper(repo_path):
    for pattern in ["*.pdf", "*.tex", "paper*", "Paper*"]:
        matches = sorted(repo_path.glob(pattern))
        if matches:
            return True, str(matches[0])
    for readme in repo_path.glob("README*"):
        try:
            content = readme.read_text(encoding="utf-8", errors="ignore")
            if "arxiv.org" in content.lower():
                return True, str(readme)
        except Exception:
            pass
    return False, None

def detect_language(repo_path, files):
    package_managers = []
    entry_points = []
    languages_present = []
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
    ext_counts = {}
    for f in files:
        ext_counts[f.suffix] = ext_counts.get(f.suffix, 0) + 1
    for lang, signals in LANGUAGE_SIGNALS.items():
        if lang in languages_present:
            continue
        if any(ext_counts.get(ext, 0) > 0 for ext in signals["exts"]):
            languages_present.append(lang)
    primary = languages_present[0] if languages_present else None
    return primary, package_managers, entry_points, languages_present

def find_modules(repo_path, files, primary):
    candidates = set()
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
    return sorted(candidates)

files, total, by_ext = collect_files(REPO_PATH)
primary, package_managers, entry_points, languages = detect_language(REPO_PATH, files)
paper_found, paper_path = detect_paper(REPO_PATH)
modules = find_modules(REPO_PATH, files, primary)

# 研究/训练入口脚本提升：train_*.py / run_*.py / combine_*.py 视为入口并加入 core_files_seed
RESEARCH_ENTRY_GLOBS = ["train_*.py", "run_*.py", "combine_*.py"]
research_entrypoints = []
for pat in RESEARCH_ENTRY_GLOBS:
    for f in REPO_PATH.glob(pat):
        if f.is_file():
            rel = f.relative_to(REPO_PATH).as_posix()
            if rel not in research_entrypoints:
                research_entrypoints.append(rel)
            if rel not in entry_points:
                entry_points.append(rel)

# 优先使用环境变量或已有 profile 中的 repo_name / repo_ref，其次从路径推断
repo_name = os.environ.get("REPO_NAME")
repo_ref = os.environ.get("REPO_REF")
existing = {}
if (WORK_DIR / "profile.json").exists():
    try:
        existing = json.loads((WORK_DIR / "profile.json").read_text(encoding="utf-8"))
    except Exception:
        existing = {}
if not repo_name:
    repo_name = existing.get("repo_name")
if not repo_name:
    repo_name = REPO_PATH.name
if not repo_ref:
    repo_ref = existing.get("repo_ref")

# 分析模式：从已有 profile 继承（Phase 0 写入），否则按路径推断
analysis_mode = existing.get("analysis_mode", "local")

profile = {
    "repo_path": str(REPO_PATH),
    "work_dir": str(WORK_DIR),
    "analysis_mode": analysis_mode,
    "repo_name": repo_name,
    "repo_ref": repo_ref,
    "primary_language": primary,
    "all_languages": languages,
    "package_managers": package_managers,
    "entry_points": entry_points,
    "paper_found": paper_found,
    "paper_path": paper_path,
    "depth": DEPTH if DEPTH in ("standard", "deep") else "standard",
    "file_count_total": total,
    "file_count_by_ext": by_ext,
    "module_candidates": modules,
    "core_files_seed": sorted(set(entry_points + package_managers + research_entrypoints + ["README.md"])),
}

WORK_DIR.mkdir(parents=True, exist_ok=True)
(WORK_DIR / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(profile, indent=2, ensure_ascii=False))
```

## 输出字段

```json
{
  "repo_path": "...",
  "work_dir": "...",
  "repo_name": "...",
  "primary_language": "python",
  "all_languages": ["python"],
  "package_managers": ["pyproject.toml"],
  "entry_points": ["src/main.py"],
  "paper_found": false,
  "paper_path": null,
  "depth": "standard",
  "file_count_total": 42,
  "file_count_by_ext": {"py": 30, "md": 5},
  "module_candidates": ["src"],
  "core_files_seed": ["src/main.py", "pyproject.toml", "README.md"]
}
```

## 使用方式

1. 由 profiler agent 执行上述代码，生成 `profile.json`。
2. 其他 agent 读取 `profile.json` 作为分析输入。
3. 语言特定入口识别参考 `references/language-profiles.md`。
