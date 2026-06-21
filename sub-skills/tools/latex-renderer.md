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

如果未找到，跳过 PDF 渲染，保留 Markdown 手册并降级渲染为 HTML 格式，同时在输出摘要中提示用户安装 TeX Live。

### 步骤 1.5: 降级渲染 HTML（当 xelatex 不可用时）

优先使用 pandoc：

```bash
pandoc "$WORK_DIR/manual.md" -t html --standalone \
  -o "$WORK_DIR/repoguide-manual.html"
```

如果 pandoc 不可用，使用 Python 生成基础 HTML：

```python
import re
from pathlib import Path

md_path = Path("$WORK_DIR/manual.md")
html_path = Path("$WORK_DIR/repoguide-manual.html")

text = md_path.read_text(encoding="utf-8", errors="ignore")

# Strip YAML frontmatter
if text.startswith("---"):
    parts = text.split("---", 2)
    if len(parts) >= 3:
        text = parts[2]

def escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(s):
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{escape_html(m.group(1))}</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: f"<strong>{escape_html(m.group(1))}</strong>", s)
    s = re.sub(r"\*(.+?)\*", lambda m: f"<em>{escape_html(m.group(1))}</em>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img src="{escape_html(m.group(2))}" alt="{escape_html(m.group(1))}" style="max-width:100%">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{escape_html(m.group(2))}">{escape_html(m.group(1))}</a>', s)
    return s

lines = text.splitlines()
body = []
i = 0
while i < len(lines):
    line = lines[i]
    s = line.strip()

    if s.startswith("```"):
        i += 1
        code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i])
            i += 1
        body.append(f"<pre><code>{escape_html(chr(10).join(code))}</code></pre>")
        i += 1
        continue

    if s.startswith("#"):
        level = len(s) - len(s.lstrip("#"))
        if level <= 6 and s[level:].startswith(" "):
            body.append(f"<h{level}>{inline(s[level+1:].strip())}</h{level}>")
            i += 1
            continue

    if s in ("---", "***", "___"):
        body.append("<hr>")
        i += 1
        continue

    if not s:
        i += 1
        continue

    if s.startswith(("- ", "* ", "+ ")):
        items = [s[2:]]
        i += 1
        while i < len(lines) and lines[i].strip().startswith(("- ", "* ", "+ ")):
            items.append(lines[i].strip()[2:])
            i += 1
        body.append("<ul>")
        for item in items:
            body.append(f"<li>{inline(item)}</li>")
        body.append("</ul>")
        continue

    para = [line]
    i += 1
    while i < len(lines) and lines[i].strip():
        para.append(lines[i])
        i += 1
    body.append(f"<p>{inline(' '.join(para))}</p>")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>仓库手册指南</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; line-height: 1.7; color: #333; }}
h1, h2, h3, h4 {{ color: #1a1a1a; margin-top: 1.5em; }}
pre {{ background: #f6f8fa; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
code {{ font-family: Consolas, Monaco, monospace; font-size: 0.9em; }}
img {{ max-width: 100%; height: auto; }}
a {{ color: #0366d6; }}
</style>
</head>
<body>
{chr(10).join(body)}
</body>
</html>"""

html_path.write_text(html, encoding="utf-8")
```

### 步骤 2: 准备 Markdown 与模板

假设：
- Markdown 手册路径：`$WORK_DIR/manual.md`
- 模板路径：`$WORK_DIR/repoguide-manual.tex`（从 `references/latex-template/main.tex` 复制并替换占位符）

### 步骤 3: 生成 LaTeX 正文

优先使用 pandoc：

```bash
pandoc "$WORK_DIR/manual.md" -t latex --standalone --listings \
  > "$WORK_DIR/manual-body.tex"
```

如果 pandoc 不可用，使用内置 Python 转换：

```python
import re
from pathlib import Path

md_path = Path("$WORK_DIR/manual.md")
out_path = Path("$WORK_DIR/manual-body.tex")

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

### 步骤 4: 处理图片

1. 确保 `$WORK_DIR/images/` 目录存在。
2. 将图片复制到 `$WORK_DIR/images/`（如果尚未在）。
3. 将 Markdown 图片语法转换为 LaTeX figure 环境：

```python
import re

body = Path('$WORK_DIR/manual-body.tex').read_text(encoding='utf-8')

def md_img_to_latex(m):
    alt = m.group(1)
    src = m.group(2)
    return f"""\\begin{{figure}}[htbp]
  \\centering
  \\includegraphics[width=0.8\\textwidth]{{{src}}}
  \\caption{{{alt}}}
\\end{{figure}}"""

body = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', md_img_to_latex, body)
Path('$WORK_DIR/manual-body.tex').write_text(body, encoding='utf-8')
```

### 步骤 5: 填充模板

从 `references/latex-template/main.tex` 复制到 `$WORK_DIR/repoguide-manual.tex`，并替换占位符：

- `{TITLE}` → 手册标题
- `{REPO_NAME}` → 仓库名
- `{PRIMARY_LANGUAGE}` → 主语言
- `{FILE_COUNT}` → 文件总数
- `{DATE}` → 生成日期
- `{CONTENT}` → `manual-body.tex` 的内容

### 步骤 6: 编译 PDF

```bash
cd "$WORK_DIR"
xelatex -interaction=nonstopmode repoguide-manual.tex
xelatex -interaction=nonstopmode repoguide-manual.tex
```

### 步骤 7: 复制到用户目录

```bash
# PDF
if [ -f "$WORK_DIR/repoguide-manual.pdf" ]; then
  cp "$WORK_DIR/repoguide-manual.pdf" "$PWD/repoguide-manual.pdf"
fi

# HTML（降级时生成）
if [ -f "$WORK_DIR/repoguide-manual.html" ]; then
  cp "$WORK_DIR/repoguide-manual.html" "$PWD/repoguide-manual.html"
fi

# Markdown（始终保留）
cp "$WORK_DIR/manual.md" "$PWD/repoguide-manual.md"
```

## 降级

如果 `xelatex` 不可用：

1. 保留 Markdown 手册。
2. 渲染 HTML 格式（优先 pandoc，否则使用 Python 降级方案）。
3. 在对话中提示用户安装 TeX Live。
4. 不终止整体流程。

## 输出

- `<cwd>/repoguide-manual.pdf`（需要 xelatex）
- `<cwd>/repoguide-manual.html`（xelatex 不可用时降级输出）
- `<cwd>/repoguide-manual.md`（中间产物，默认保留）
