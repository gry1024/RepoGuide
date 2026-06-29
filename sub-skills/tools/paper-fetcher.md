---
name: repoguide-tool-paper-fetcher
description: RepoGuide 的论文获取工具，支持 arXiv 链接解析与 PDF 下载。
---

# RepoGuide · 论文获取与发现

## 输入类型

| 输入 | 处理方式 |
|------|----------|
| arXiv URL (`https://arxiv.org/abs/xxxx.xxxxx`) | 下载 PDF 到 `$WORK_DIR/paper.pdf` |
| arXiv PDF URL (`https://arxiv.org/pdf/xxxx.xxxxx`) | 直接下载 |
| 本地 PDF 路径 | 复制到 `$WORK_DIR/paper.pdf` |
| 本地 .tex 路径 | 直接使用 |
| 未显式提供论文 | 扫描仓库元文件中的 arXiv 或本地论文文件 |

## arXiv 下载

```bash
# 从 abs 页面提取 PDF 链接后下载
ARXIV_ID="xxxx.xxxxx"
PDF_URL="https://arxiv.org/pdf/${ARXIV_ID}.pdf"
curl -L -o "$WORK_DIR/paper.pdf" "$PDF_URL"
```

或用 Python：

```python
import json
import os
import re
import shutil
import urllib.request
from pathlib import Path

ARXIV_URL_RE = re.compile(
    r"https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/"
    r"([a-zA-Z-]+(?:\.[A-Z]+)?/\d+|\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?",
    re.I,
)

METADATA_GLOBS = [
    "README*",
    "CITATION*",
    "codemeta.json",
    "paper*.md",
    "paper*.rst",
    "paper*.txt",
    "paper*.tex",
    "docs/**/*.md",
    "docs/**/*.rst",
    "docs/**/*.txt",
    "paper/**/*.md",
    "paper/**/*.rst",
    "paper/**/*.txt",
    "papers/**/*.md",
    "papers/**/*.rst",
    "papers/**/*.txt",
]
LOCAL_PAPER_GLOBS = [
    "paper*.pdf",
    "paper*.tex",
    "paper/**/*.pdf",
    "paper/**/*.tex",
    "papers/**/*.pdf",
    "papers/**/*.tex",
    "docs/**/*.pdf",
    "docs/**/*.tex",
]
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build", "__pycache__"}
MAX_SCAN_BYTES = 1_000_000


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _candidate_files(repo_path: Path, patterns: list[str]):
    seen = set()
    for pattern in patterns:
        for path in sorted(repo_path.glob(pattern)):
            if not path.is_file() or path in seen:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            seen.add(path)
            yield path


def discover_paper_reference(repo_path):
    """从仓库元文件发现论文引用；未找到时返回 None。"""
    repo_path = Path(repo_path).resolve()

    for path in _candidate_files(repo_path, METADATA_GLOBS):
        if path.stat().st_size > MAX_SCAN_BYTES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = ARXIV_URL_RE.search(text)
        if match:
            return {
                "paper_ref": f"https://arxiv.org/abs/{match.group(1)}",
                "paper_source": _safe_rel(path, repo_path),
                "paper_source_type": "arxiv",
            }

    for path in _candidate_files(repo_path, LOCAL_PAPER_GLOBS):
        return {
            "paper_ref": str(path.resolve()),
            "paper_source": _safe_rel(path, repo_path),
            "paper_source_type": "local_file",
        }

    return None


def fetch_arxiv(url: str, output: str = None):
    if output is None:
        output = os.path.join(os.environ.get("WORK_DIR", "_repoguide"), "paper.pdf")
    # 兼容新版 ID（如 2401.12345）和老版分类 ID（如 cs/0011001、quant-ph/9809069）
    arxiv_id = re.search(
        r"arxiv\.org/(?:abs|pdf)/([a-zA-Z-]+(?:\.[A-Z]+)?/\d+|\d+\.\d+)",
        url,
    ).group(1)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    urllib.request.urlretrieve(pdf_url, output)
    return output


def fetch_paper_reference(paper_ref: str, output: str = None):
    """下载或复制论文，返回可交给 Phase 3 的本地路径。"""
    if ARXIV_URL_RE.search(paper_ref):
        return fetch_arxiv(paper_ref, output)

    src = Path(paper_ref).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"论文文件不存在: {src}")
    if src.suffix.lower() == ".tex":
        return str(src)

    if output is None:
        output = os.path.join(os.environ.get("WORK_DIR", "_repoguide"), "paper.pdf")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, output)
    return output


def update_profile_with_paper(work_dir, paper_ref, paper_path, source=None, source_type=None):
    work_dir = Path(work_dir)
    profile_path = work_dir / "profile.json"
    profile = {}
    if profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile.update(
        {
            "paper_found": True,
            "paper_ref": paper_ref,
            "paper_path": str(paper_path),
            "paper_source": source,
            "paper_source_type": source_type,
        }
    )
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return profile
```

## 输出

- 论文 PDF 保存到 `$WORK_DIR/paper.pdf`
- 在 `profile.json` 中设置 `paper_found`, `paper_ref`, `paper_path`, `paper_source`
