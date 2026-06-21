---
name: repoguide-tool-latex-renderer
description: RepoGuide 的 LaTeX / xelatex PDF 渲染方法，将 Markdown 手册转换为精美 PDF，全部以代码片段形式写在 md 中由 agent 执行。
---

# RepoGuide · LaTeX PDF 渲染

## 依赖

- TeX Live / MacTeX / MiKTeX，包含 `xelatex`
- 可选：pandoc（用于 Markdown → LaTeX 转换）
- 中文字体（Windows: 宋体/黑体；macOS: 苹方；Linux: Noto CJK / WQY）

## 执行代码

由 renderer agent 执行：

### 步骤 1: 检测 xelatex

```bash
which xelatex || echo "XELATEX_NOT_FOUND"
```

如果未找到，跳过 PDF 渲染，仅保留 Markdown 手册，并在输出摘要中提示用户安装 TeX Live。

### 步骤 2: 准备 Markdown 与模板

假设：
- Markdown 手册路径：`$REPO_PATH/_repoguide/manual.md`
- 模板路径：`$REPO_PATH/_repoguide/repoguide-manual.tex`（从 `references/latex-template/main.tex` 复制并替换占位符）

### 步骤 3: 生成 LaTeX 正文

优先使用 pandoc：

```bash
pandoc "$REPO_PATH/_repoguide/manual.md" -t latex --standalone --listings \
  > "$REPO_PATH/_repoguide/manual-body.tex"
```

如果 pandoc 不可用，使用内置 Python 转换：

```python
import re
from pathlib import Path

md_path = Path("$REPO_PATH/_repoguide/manual.md")
out_path = Path("$REPO_PATH/_repoguide/manual-body.tex")

text = md_path.read_text(encoding="utf-8", errors="ignore")

# Strip YAML frontmatter
if text.startswith("---"):
    parts = text.split("---", 2)
    if len(parts) >= 3:
        text = parts[2]

SPECIAL = {
    "\\": "\\textbackslash{}",
    "{": "\\{",
    "}": "\\}",
    "$": "\\$",
    "&": "\\&",
    "#": "\\#",
    "_": "\\_",
    "%": "\\%",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
}

def escape(s):
    return "".join(SPECIAL.get(c, c) for c in s)

def inline(s):
    s = re.sub(r"`([^`]+)`", lambda m: f"\\texttt{{{escape(m.group(1))}}}", s)
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\\textbf{{{escape(m.group(1))}}}", s)
    s = re.sub(r"\*(.+?)\*", lambda m: f"\\textit{{{escape(m.group(1))}}}", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f"\\href{{{escape(m.group(2))}}}{{{escape(m.group(1))}}}", s)
    return escape(s)

lines = text.splitlines()
out = []
i = 0
while i < len(lines):
    line = lines[i]
    s = line.strip()

    if s.startswith("```"):
        lang = s[3:].strip()
        i += 1
        code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i])
            i += 1
        out.append(f"\\begin{{lstlisting}}[language={lang or 'TeX'},caption=]")
        out.append(escape("\n".join(code)))
        out.append("\\end{lstlisting}")
        i += 1
        continue

    if s.startswith("#"):
        level = len(s) - len(s.lstrip("#"))
        if level <= 6 and s[level:].startswith(" "):
            cmd = ["\\section", "\\subsection", "\\subsubsection", "\\paragraph", "\\subparagraph", "\\subparagraph"][min(level-1, 5)]
            out.append(f"{cmd}{{{inline(s[level+1:].strip())}}}")
            i += 1
            continue

    if s in ("---", "***", "___"):
        out.append("\\hrulefill")
        i += 1
        continue

    if not s:
        out.append("")
        i += 1
        continue

    if s.startswith(("- ", "* ", "+ ")):
        items = [s[2:]]
        i += 1
        while i < len(lines) and lines[i].strip().startswith(("- ", "* ", "+ ")):
            items.append(lines[i].strip()[2:])
            i += 1
        out.append("\\begin{itemize}")
        for item in items:
            out.append(f"  \\item {inline(item)}")
        out.append("\\end{itemize}")
        continue

    para = [line]
    i += 1
    while i < len(lines) and lines[i].strip():
        para.append(lines[i])
        i += 1
    out.append(inline(" ".join(para)))

out_path.write_text("\n".join(out), encoding="utf-8")
```

### 步骤 4: 填充模板

从 `references/latex-template/main.tex` 复制到 `$REPO_PATH/_repoguide/repoguide-manual.tex`，并替换占位符：

- `{TITLE}` → 手册标题
- `{REPO_NAME}` → 仓库名
- `{PRIMARY_LANGUAGE}` → 主语言
- `{FILE_COUNT}` → 文件总数
- `{DATE}` → 生成日期
- `{CONTENT}` → `manual-body.tex` 的内容

### 步骤 5: 编译 PDF

```bash
cd "$REPO_PATH/_repoguide"
xelatex -interaction=nonstopmode repoguide-manual.tex
xelatex -interaction=nonstopmode repoguide-manual.tex
```

### 步骤 6: 复制到用户目录

```bash
cp "$REPO_PATH/_repoguide/repoguide-manual.pdf" "$PWD/repoguide-manual.pdf"
cp "$REPO_PATH/_repoguide/manual.md" "$PWD/repoguide-manual.md"
```

## 降级

如果 `xelatex` 不可用：

1. 保留 Markdown 手册。
2. 在对话中提示用户安装 TeX Live。
3. 不终止整体流程。

## 输出

- `<cwd>/repoguide-manual.pdf`
- `<cwd>/repoguide-manual.md`（中间产物，默认保留）
