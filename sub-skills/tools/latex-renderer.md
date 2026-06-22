---
name: repoguide-tool-latex-renderer
description: RepoGuide 的 LaTeX / xelatex PDF 渲染方法：将 Markdown 仓库手册转换为精美中文 PDF。全部以代码片段形式写在 md 中由 agent 执行。
---

# RepoGuide · LaTeX PDF 渲染

## 设计原则

1. **必须用 xelatex 编译**：pandoc 只作为 Markdown→LaTeX 正文的辅助转换，最终 PDF 必须由 xelatex 生成。
2. **图片必须显式处理**：统一复制到 `$WORK_DIR/images/`，并在 LaTeX 中设置正确的 `\graphicspath`。
3. **中文必须正确渲染**：使用 `ctex` 文档类 + 系统 CJK 字体（Windows: 微软雅黑/宋体；macOS: 苹方；Linux: Noto CJK）。
4. **产物命名带仓库名**：`<repo_name>-manual.pdf`。

## 依赖

- TeX Live / MacTeX / MiKTeX / TinyTeX，包含 `xelatex`
- 中文字体（Windows: SimSun/SimHei/Microsoft YaHei；macOS: PingFang SC/STSong；Linux: Noto Sans CJK SC/WenQuanYi）
- 可选：`pandoc`（仅用于快速将 Markdown 转为 LaTeX 正文，若不可用则用内置 Python 转换器）

## 变量

- `$WORK_DIR`: `<cwd>/_repoguide/`
- `$REPO_NAME`: 仓库名（从 `$WORK_DIR/profile.json` 的 `repo_name` 字段读取）
- 最终产物前缀: `$REPO_NAME-manual`

## 执行代码

由 renderer agent 执行。

### 步骤 1: 检测 xelatex

```bash
which xelatex || echo "XELATEX_NOT_FOUND"
```

如果未找到，跳过 PDF 渲染，保留 Markdown 手册并降级渲染为 HTML 格式，同时在输出摘要中提示用户安装 TeX Live。

### 步骤 1.5: 降级渲染 HTML（当 xelatex 不可用时）

优先使用 pandoc，并显式声明 UTF-8 与中文：

```bash
pandoc "$WORK_DIR/manual.md" -t html --standalone \
  --metadata charset=UTF-8 \
  --metadata lang=zh-CN \
  -V "header-includes=<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">" \
  -o "$WORK_DIR/${REPO_NAME}-manual.html"
```

如果 pandoc 不可用，使用 Python 生成基础 HTML（带 UTF-8 BOM，Windows 记事本可直接识别）：

```python
import os, re
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
repo_name = os.environ.get("REPO_NAME", "repo")
md_path = work_dir / "manual.md"
html_path = work_dir / f"{repo_name}-manual.html"

text = md_path.read_text(encoding="utf-8", errors="ignore")

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
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{repo_name} 仓库手册指南</title>
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

# 带 UTF-8 BOM，确保 Windows 记事本和旧浏览器正确识别中文
html_path.write_bytes("\ufeff".encode("utf-8") + html.encode("utf-8"))
```

### 步骤 2: 读取元数据

```python
import os, json
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
profile = json.loads((work_dir / "profile.json").read_text(encoding="utf-8"))

repo_name = profile["repo_name"]
primary_language = profile.get("primary_language", "")
file_count_total = profile.get("file_count_total", 0)
date = profile.get("generated_at", "")
if not date:
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

# 导出环境变量供后续脚本使用
print(f"REPO_NAME={repo_name}")
print(f"PRIMARY_LANGUAGE={primary_language}")
print(f"FILE_COUNT={file_count_total}")
print(f"DATE={date}")
```

### 步骤 2.5: 图片预处理

在把 Markdown 转成 LaTeX 之前，先把 `manual.md` 里引用的图片统一整理到 `$WORK_DIR/images/`，并生成标准化路径映射。

```python
import json
import os
import re
import shutil
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
img_dir = work_dir / "images"
img_dir.mkdir(exist_ok=True)

md_path = work_dir / "manual.md"
md_text = md_path.read_text(encoding="utf-8", errors="ignore")

image_map = {}      # 原始路径 -> images/fig_xxx.ext
counter = 0

def normalize_image(m):
    global counter
    alt = m.group(1).strip() or "图"
    src = m.group(2).strip()

    # 网络图片保持原样，生成占位
    if src.startswith("http://") or src.startswith("https://"):
        return f"![{alt}]({src})"

    original = Path(src)
    if original.is_absolute():
        resolved = original
    else:
        # 先相对于 manual.md/work_dir 解析，再回退到仓库根
        resolved = work_dir / original
        if not resolved.exists():
            repo_path = Path(os.environ.get("REPO_PATH", work_dir / "repo"))
            resolved = repo_path / original

    if resolved.exists():
        ext = resolved.suffix or ".png"
        counter += 1
        new_name = f"fig_{counter:03d}{ext}"
        dst = img_dir / new_name
        shutil.copy2(resolved, dst)
        image_map[src] = f"images/{new_name}"
        return f"![{alt}](images/{new_name})"
    else:
        # 图片不存在，保留原路径并在 limitation 中记录
        return f"![{alt}]({src})"

new_md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", normalize_image, md_text)

# 写回标准化后的 manual.md，后续转换基于它
md_path.write_text(new_md_text, encoding="utf-8")

# 记录映射供调试
(work_dir / "image-map.json").write_text(
    json.dumps(image_map, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
```

### 步骤 3: 生成 LaTeX 正文

步骤 2.5 已经把 `manual.md` 中的图片路径标准化为 `images/fig_xxx.ext`，本步骤基于标准化后的 `manual.md` 转换。

**首选方案：使用 pandoc 快速转换**：

```bash
cd "$WORK_DIR"
pandoc "manual.md" -t latex --listings \
  --template="$WORK_DIR/raw-body.tex" \
  -o "$WORK_DIR/manual-body.tex" 2>/dev/null || true
```

如果 pandoc 没有生成有效文件，或转换结果不理想，**使用内置 Python 转换器**重写 `$WORK_DIR/manual-body.tex`：

```python
import os, re
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
md_path = work_dir / "manual.md"
out_path = work_dir / "manual-body.tex"

text = md_path.read_text(encoding="utf-8", errors="ignore")

# Strip YAML frontmatter
if text.startswith("---"):
    parts = text.split("---", 2)
    if len(parts) >= 3:
        text = parts[2]

INLINE_ESCAPES = {
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
    return "".join(INLINE_ESCAPES.get(c, c) for c in s)

def inline(s):
    s = re.sub(r"`([^`]+)`", lambda m: f"\\texttt{{{escape(m.group(1))}}}", s)
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\\textbf{{{escape(m.group(1))}}}", s)
    s = re.sub(r"\*(.+?)\*", lambda m: f"\\textit{{{escape(m.group(1))}}}", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f"\\href{{{escape(m.group(2))}}}{{{escape(m.group(1))}}}", s)
    return escape(s)

def figure_env(alt, src):
    alt = inline(alt) or "图"
    if src.startswith("http://") or src.startswith("https://"):
        return (
            f"\\begin{{figure}}[htbp]\n"
            f"  \\centering\n"
            f"  \\fbox{{\\parbox{{0.8\\textwidth}}{{\\centering [{alt}] \\newline \\footnotesize \\url{{{escape(src)}}}}}}}\n"
            f"  \\caption{{{alt}}}\n"
            f"\\end{{figure}}"
        )
    return (
        f"\\begin{{figure}}[htbp]\n"
        f"  \\centering\n"
        f"  \\includegraphics[width=0.85\\textwidth]{{{escape(src)}}}\n"
        f"  \\caption{{{alt}}}\n"
        f"\\end{{figure}}"
    )

def parse_table(lines, start):
    """Parse a Markdown table starting at index `start`. Returns (latex_lines, next_index)."""
    header = lines[start].strip()
    sep = lines[start + 1].strip() if start + 1 < len(lines) else ""
    if not sep or not all(c in "-|:\" for c in sep):
        return None, start
    cols = header.split("|")[1:-1]
    n = len(cols)
    align = []
    for cell in sep.split("|")[1:-1]:
        cell = cell.strip()
        if cell.startswith(":") and cell.endswith(":"):
            align.append("c")
        elif cell.endswith(":"):
            align.append("r")
        else:
            align.append("l")
    align = align[:n] + ["l"] * (n - len(align))
    out_lines = ["\\begin{center}", "\\begin{tabular}{" + "".join(align) + "}", "\\toprule"]
    out_lines.append(" & ".join(escape(c.strip()) for c in cols) + " \\\\")
    out_lines.append("\\midrule")
    i = start + 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = lines[i].strip().split("|")[1:-1]
        row = row[:n] + [""] * (n - len(row))
        out_lines.append(" & ".join(escape(c.strip()) for c in row) + " \\\\")
        i += 1
    out_lines.append("\\bottomrule")
    out_lines.append("\\end{tabular}")
    out_lines.append("\\end{center}")
    return out_lines, i

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
        out.append(f"\\begin{{lstlisting}}[language={lang or 'TeX'},basicstyle=\\small\\ttfamily,breaklines=true]")
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

    if s.startswith("|"):
        table_lines, next_i = parse_table(lines, i)
        if table_lines:
            out.extend(table_lines)
            i = next_i
            continue

    if s in ("---", "***", "___"):
        out.append("\\hrulefill")
        i += 1
        continue

    if not s:
        out.append("")
        i += 1
        continue

    # 图片独立成段，直接生成 figure 环境
    if s.startswith("!["):
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            out.append(figure_env(m.group(1), m.group(2)))
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

    if re.match(r"^\d+\\.\\s", s):
        items = [re.sub(r"^\d+\\.\\s", "", s)]
        i += 1
        while i < len(lines) and re.match(r"^\d+\\.\\s", lines[i].strip()):
            items.append(re.sub(r"^\d+\\.\\s", "", lines[i].strip()))
            i += 1
        out.append("\\begin{enumerate}")
        for item in items:
            out.append(f"  \\item {inline(item)}")
        out.append("\\end{enumerate}")
        continue

    para = [line]
    i += 1
    while i < len(lines) and lines[i].strip():
        para.append(lines[i])
        i += 1
    out.append(inline(" ".join(para)))

out_path.write_text("\n".join(out), encoding="utf-8")
```

### 步骤 4: 图片最终检查

步骤 2.5 已经把 `manual.md` 中的图片路径标准化为 `images/fig_xxx.ext`，步骤 3 的转换器也已把图片语法转成 LaTeX `figure` 环境。本步骤做最终兜底：

1. 确保 `$WORK_DIR/images/` 目录存在。
2. 扫描 `manual-body.tex`，若还有未标准化的本地图片路径，复制到 `images/` 并修正路径。
3. 网络图片保持 `[网络图片]` 占位框。

```python
import os, re, shutil
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
img_dir = work_dir / "images"
img_dir.mkdir(exist_ok=True)

body_path = work_dir / "manual-body.tex"
if body_path.exists():
    body = body_path.read_text(encoding="utf-8", errors="ignore")

    def collect_and_rename(m):
        alt = m.group(1).strip() or "图"
        src = m.group(2).strip()
        if src.startswith("http://") or src.startswith("https://"):
            return m.group(0)
        original = Path(src)
        resolved = original if original.is_absolute() else (work_dir / original)
        if resolved.exists() and not src.startswith("images/"):
            ext = resolved.suffix or ".png"
            counter = getattr(collect_and_rename, "counter", 0) + 1
            collect_and_rename.counter = counter
            new_name = f"fig_{counter:03d}{ext}"
            shutil.copy2(resolved, img_dir / new_name)
            return f"\\includegraphics[width=0.85\\textwidth]{{images/{new_name}}}"
        return m.group(0)

    body = re.sub(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', collect_and_rename, body)
    body_path.write_text(body, encoding="utf-8")
```

### 步骤 5: 填充模板

从 `references/latex-template/main.tex` 复制到 `$WORK_DIR/<repo_name>-manual.tex`，并替换占位符。替换时必须对值进行 LaTeX 转义，避免仓库名含 `# % & _ ^` 等字符时编译失败。

占位符：

- `{TITLE}` → 手册标题
- `{REPO_NAME}` → 仓库名
- `{PRIMARY_LANGUAGE}` → 主语言
- `{FILE_COUNT}` → 文件总数
- `{DATE}` → 生成日期
- `{CONTENT}` → `manual-body.tex` 的内容（已在步骤 3 转义）

```python
import os
import re
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
repo_name = os.environ.get("REPO_NAME", "repo")
primary_language = os.environ.get("PRIMARY_LANGUAGE", "")
file_count = os.environ.get("FILE_COUNT", "0")
date = os.environ.get("DATE", "")

template_path = Path("references/latex-template/main.tex")
tex_path = work_dir / f"{repo_name}-manual.tex"
body_path = work_dir / "manual-body.tex"

template = template_path.read_text(encoding="utf-8", errors="ignore")
body = body_path.read_text(encoding="utf-8", errors="ignore")

LATEX_ESCAPES = {
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

def latex_escape(s):
    return "".join(LATEX_ESCAPES.get(c, c) for c in s)

title = f"{repo_name} 仓库手册指南"
replacements = {
    "{TITLE}": latex_escape(title),
    "{REPO_NAME}": latex_escape(repo_name),
    "{PRIMARY_LANGUAGE}": latex_escape(primary_language),
    "{FILE_COUNT}": latex_escape(file_count),
    "{DATE}": latex_escape(date),
    "{CONTENT}": body,
}

# 按占位符长度降序替换，避免短占位符干扰长的
for placeholder, value in sorted(replacements.items(), key=lambda x: -len(x[0])):
    template = template.replace(placeholder, value)

tex_path.write_text(template, encoding="utf-8")
```

```bash
# 如果不在 RepoGuide 仓库根目录，先定位模板再执行 Python
# cp "references/latex-template/main.tex" "$WORK_DIR/${REPO_NAME}-manual.tex"
```

### 步骤 6: 编译 PDF

```bash
cd "$WORK_DIR"
xelatex -interaction=nonstopmode "${REPO_NAME}-manual.tex"
xelatex -interaction=nonstopmode "${REPO_NAME}-manual.tex"
```

### 步骤 7: 复制到用户目录

```bash
# PDF
if [ -f "$WORK_DIR/${REPO_NAME}-manual.pdf" ]; then
  cp "$WORK_DIR/${REPO_NAME}-manual.pdf" "$PWD/${REPO_NAME}-manual.pdf"
fi

# HTML（降级时生成）
if [ -f "$WORK_DIR/${REPO_NAME}-manual.html" ]; then
  cp "$WORK_DIR/${REPO_NAME}-manual.html" "$PWD/${REPO_NAME}-manual.html"
fi

# Markdown（始终保留）
cp "$WORK_DIR/manual.md" "$PWD/${REPO_NAME}-manual.md"
```

## 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| xelatex 找不到 ctex 宏包 | 未安装中文 LaTeX 环境 | 安装 TeX Live / MiKTeX / TinyTeX 完整版 |
| 中文显示为方框 / 乱码 | 系统缺少 CJK 字体 | Windows 用 SimSun/SimHei/Microsoft YaHei；macOS 用 PingFang SC；Linux 用 fonts-noto-cjk |
| 图片不显示 | 图片路径错误或格式不支持 | 统一复制到 `images/`；优先 PNG/PDF；SVG 需预转 |
| mermaid 图丢失 | mermaid-cli 未安装 | 保留 mermaid 文本代码块或转 PNG |
| 代码块换行截断 | listings 未开启 breaklines | 模板已默认开启 `breaklines=true` |
| pandoc 转换后中文异常 | pandoc 默认字体不兼容 | 仅把 pandoc 当辅助，最终用 xelatex 编译 |
| PDF 目录不存在 | 只编译一次 | xelatex 编译两次以生成正确目录和交叉引用 |

## 输出

- `<cwd>/<repo_name>-manual.pdf`（需要 xelatex）
- `<cwd>/<repo_name>-manual.html`（xelatex 不可用时降级输出）
- `<cwd>/<repo_name>-manual.md`（中间产物，默认保留）
