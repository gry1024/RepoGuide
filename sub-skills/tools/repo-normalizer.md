---
name: repoguide-tool-repo-normalizer
description: RepoGuide 的仓库归一化方法：把 GitHub URL、本地路径或当前目录转换为可用于分析的绝对路径，并确定中间产物目录。全部以代码片段形式写在 md 中由 agent 执行。
---

# RepoGuide · 仓库归一化

## 设计原则

1. **克隆不是必须的**：本地路径和当前目录直接分析，无需克隆。
2. **中间产物与代码分离**：所有工作产物统一放在 `<cwd>/_repoguide/`，不写入被分析仓库内部。
3. **默认浅克隆**：分析 GitHub 仓库时，默认 `git clone --depth 1` 到 `<cwd>/_repoguide/repo/`，用完可清理。
4. **可选远程模式**：如果环境不允许克隆，可使用 GitHub API 直接读取文件（仅适合小型仓库，会记录在 limitation_notes）。

## 变量约定

- `$REPO_PATH`: 被分析仓库代码的绝对路径（agent 读取代码的位置）。
- `$WORK_DIR`: 中间产物目录，固定为 `<cwd>/_repoguide/`。

## 输入类型

| 输入 | 处理方式 | `$REPO_PATH` | 是否需要克隆 |
|------|----------|--------------|--------------|
| 本地路径 | 验证存在后解析为绝对路径 | 本地路径 | 否 |
| 当前目录 | 检查 `.git/` 或直接使用当前目录 | 当前目录 / git 根目录 | 否 |
| GitHub URL | 克隆到 `$WORK_DIR/repo/` | `$WORK_DIR/repo/` | 是（默认） |
| GitHub URL（远程模式） | 不克隆，通过 GitHub API 读取 | `null`（远程分析） | 否 |

## 执行代码

### 1. 确定工作目录

```bash
WORK_DIR="$PWD/_repoguide"
mkdir -p "$WORK_DIR"
echo "$WORK_DIR"
```

### 2. 本地路径

```bash
REPO_REF="/path/to/repo"
cd "$REPO_REF" || exit 1
REPO_PATH=$(pwd)
echo "$REPO_PATH"
```

### 3. 当前目录

```bash
if [ -d ".git" ]; then
    REPO_PATH=$(git rev-parse --show-toplevel)
else
    # 不是 git 仓库也允许分析当前目录
    REPO_PATH=$(pwd)
fi
echo "$REPO_PATH"
```

### 4. GitHub URL（默认浅克隆）

```bash
URL="https://github.com/owner/repo"
REPO_NAME=$(basename "$URL" .git)
WORK_DIR="$PWD/_repoguide"
REPO_PATH="$WORK_DIR/repo"

if [ -d "$REPO_PATH/.git" ]; then
    echo "Reusing existing clone at $REPO_PATH"
else
    rm -rf "$REPO_PATH"
    mkdir -p "$WORK_DIR"
    git clone --depth 1 "$URL" "$REPO_PATH"
fi

echo "$REPO_PATH"
```

### 5. GitHub URL（远程模式，不克隆）

当环境无法/不允许克隆时使用：

```bash
URL="https://github.com/owner/repo"
REPO_NAME=$(basename "$URL" .git)
WORK_DIR="$PWD/_repoguide"
REPO_PATH="$WORK_DIR/repo"

# 仅下载文件树和少量核心文件到本地
mkdir -p "$REPO_PATH"
curl -sL "https://api.github.com/repos/owner/repo/contents/" \
  -H "Accept: application/vnd.github+json" \
  > "$WORK_DIR/github-tree.json"

echo "REMOTE:$REPO_PATH"
```

远程模式下：
- `$REPO_PATH` 仍指向 `$WORK_DIR/repo/`，但只包含通过 API 下载的部分文件。
- 必须在 `profile.json` 中设置 `"analysis_mode": "remote"` 和 `"limitation_notes": ["使用 GitHub API 远程读取，可能遗漏大文件或私有文件"]`。

## 输出

在归一化仓库后，立即把以下信息写入 `$WORK_DIR/profile.json`：

```python
import json
import os
from pathlib import Path
import re

def extract_repo_name(repo_ref: str) -> str:
    """从 GitHub URL 或本地路径解析仓库名。"""
    if not repo_ref:
        return "repo"
    # GitHub URL: https://github.com/owner/repo.git or git@github.com:owner/repo.git
    m = re.search(r"github\.com[/:]([^/]+)/([^/?#]+)", repo_ref)
    if m:
        name = m.group(2).rstrip("/")
        return name[:-4] if name.endswith(".git") else name
    # 本地路径
    p = Path(repo_ref)
    return p.name if p.name else "repo"

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
work_dir.mkdir(parents=True, exist_ok=True)

repo_ref = os.environ.get("REPO_REF", os.environ.get("REPO_PATH", ""))
repo_name = os.environ.get("REPO_NAME") or extract_repo_name(repo_ref)

profile = {
    "repo_path": os.environ.get("REPO_PATH", ""),
    "work_dir": str(work_dir.resolve()),
    "analysis_mode": os.environ.get("ANALYSIS_MODE", "clone"),
    "repo_name": repo_name,
}

(work_dir / "profile.json").write_text(
    json.dumps(profile, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
```

```json
{
  "repo_path": "...",
  "work_dir": "...",
  "analysis_mode": "local|clone|remote",
  "repo_name": "AlphaSAGE"
}
```
