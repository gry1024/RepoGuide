---
name: repoguide-tool-repo-cloner
description: RepoGuide 的仓库归一化方法：把 GitHub URL、本地路径或当前目录转换为绝对路径，全部以代码片段形式写在 md 中由 agent 执行。
---

# RepoGuide · 仓库归一化

## 输入类型

| 输入 | 处理方式 | 输出 |
|------|----------|------|
| GitHub URL | `git clone --depth 1` 到临时目录 | 克隆后的绝对路径 |
| 本地路径 | 验证存在后解析为绝对路径 | 绝对路径 |
| 空 / 当前目录 | 检查 `.git/` | 当前 git 仓库根目录 |

## 执行代码

### GitHub URL

```bash
URL="https://github.com/owner/repo"
REPO_NAME=$(basename "$URL" .git)
TARGET="/tmp/repoguide-$REPO_NAME"

if [ -d "$TARGET/.git" ]; then
    echo "Reusing existing clone at $TARGET"
else
    mkdir -p "$TARGET"
    git clone --depth 1 "$URL" "$TARGET"
fi

echo "$TARGET"
```

### 本地路径

```bash
REPO_REF="/path/to/repo"
cd "$REPO_REF" || exit 1
pwd
```

### 当前目录

```bash
if [ -d ".git" ]; then
    git rev-parse --show-toplevel
else
    echo "Error: current directory is not a git repository" >&2
    exit 1
fi
```

## 输出

将最终绝对路径写入 `_repoguide/profile.json` 的 `repo_path` 字段。
