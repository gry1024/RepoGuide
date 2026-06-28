---
name: repoguide-tool-latex-renderer
description: RepoGuide 的 LaTeX / xelatex PDF 渲染方法：数学公式感知的 Markdown→LaTeX 转换、自适应图片尺寸、精美中文 PDF。全部以代码片段写在 md 中由 agent 执行。
---

# RepoGuide · LaTeX PDF 渲染

## 设计原则

1. **必须用 xelatex 编译**：pandoc 仅作辅助，最终 PDF 由 xelatex 生成。
2. **数学公式感知转换（关键修复）**：`$...$` / `$$...$$` / `\[...\]` 数学段在转义时必须**原样保留**，不得把 `$` 转义为 `\$`、不得把 `^`/`_` 转义。这是过去"公式渲染失败"的根因。
3. **图片自适应尺寸**：统一 `\includegraphics[width=\linewidth,height=0.75\textheight,keepaspectratio]`，小图不放大、大图不溢出。
4. **中文必须正确渲染**：`ctex` 文档类 + 系统 CJK 字体。
5. **产物命名带仓库名**：`<repo_name>-manual.pdf`。
6. **不得把 pandoc 作为主转换器**：pandoc 可用于诊断或兜底，但主路径必须使用本文的 Markdown→LaTeX 转换器，避免目录、宽表、图片尺寸被黑箱输出破坏。
7. **目录、图、表必须可验收**：目录由 renderer 从 Markdown 标题生成，不依赖空 `.toc`；宽表统一包裹 `adjustbox`；HTML 表格必须横向滚动，图片必须完整显示。

## 依赖

- TeX Live / MiKTeX / TinyTeX（含 `xelatex`、`fontspec`、`ctex`、`amsmath`、`amssymb`、`mathtools`、`tcolorbox`、`tikz/pgf`、`graphicx`、`caption`、`listings`、`adjustbox`、`booktabs`、`tabularx`、`titlesec`）
- 中文字体（Windows: 微软雅黑/宋体；macOS: 苹方；Linux: Noto CJK）
- 可选 `pandoc`

## 变量

- `$WORK_DIR`: `<cwd>/_repoguide/`
- `$REPO_NAME`: 仓库名（从 `profile.json` 读取）
- 最终产物前缀: `$REPO_NAME-manual`

## 执行代码

由 renderer agent 执行。

### 步骤 1: 检测 xelatex

```bash
which xelatex || echo "XELATEX_NOT_FOUND"
```

未找到则跳过 PDF，保留 Markdown 并降级渲染 HTML（步骤 1.5）。

### 步骤 1.5: 降级渲染 HTML（xelatex 不可用时）

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
    # 保护行内数学 $...$
    s = re.sub(r"\$([^$]+)\$", lambda m: f"\x00MATH\x01{escape_html(m.group(1))}\x02MATH\x00", s)
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{escape_html(m.group(1))}</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: f"<strong>{escape_html(m.group(1))}</strong>", s)
    s = re.sub(r"\*(.+?)\*", lambda m: f"<em>{escape_html(m.group(1))}</em>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img src="{escape_html(m.group(2))}" alt="{escape_html(m.group(1))}" style="max-width:100%;height:auto">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{escape_html(m.group(2))}">{escape_html(m.group(1))}</a>', s)
    s = s.replace("\x00MATH\x01", '<span class="math">\\(').replace("\x02MATH\x00", '\\)</span>')
    return s

lines = text.splitlines()
body = []
i = 0
while i < len(lines):
    line = lines[i]
    s = line.strip()
    # 块级数学 $$...$$
    if s.startswith("$$"):
        math_lines = [s[2:]]
        if s.endswith("$$") and len(s) > 2:
            pass
        else:
            i += 1
            while i < len(lines) and not lines[i].strip().endswith("$$"):
                math_lines.append(lines[i]); i += 1
            if i < len(lines):
                math_lines.append(lines[i].rstrip()[:-2]); i += 1
        body.append(f'<div class="math">\\[{escape_html(" ".join(math_lines))}\\]</div>')
        continue
    if s.startswith("```"):
        i += 1
        code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i]); i += 1
        body.append(f"<pre><code>{escape_html(chr(10).join(code))}</code></pre>")
        i += 1; continue
    if s.startswith("#"):
        level = len(s) - len(s.lstrip("#"))
        if level <= 6 and s[level:].startswith(" "):
            body.append(f"<h{level}>{inline(s[level+1:].strip())}</h{level}>")
            i += 1; continue
    if s in ("---", "***", "___"):
        body.append("<hr>"); i += 1; continue
    if not s:
        i += 1; continue
    if s.startswith(("- ", "* ", "+ ")):
        items = [s[2:]]; i += 1
        while i < len(lines) and lines[i].strip().startswith(("- ", "* ", "+ ")):
            items.append(lines[i].strip()[2:]); i += 1
        body.append("<ul>")
        for item in items:
            body.append(f"<li>{inline(item)}</li>")
        body.append("</ul>"); continue
    if s.startswith("|"):
        tbl = ['<div class="table-wrap"><table>']; i += 0
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append(lines[i].strip()); i += 1
        if len(rows) >= 2:
            tbl.append("<tr>")
            for c in rows[0].split("|")[1:-1]:
                tbl.append(f"<th>{inline(c.strip())}</th>")
            tbl.append("</tr>")
            for r in rows[2:]:
                tbl.append("<tr>")
                for c in r.split("|")[1:-1]:
                    tbl.append(f"<td>{inline(c.strip())}</td>")
                tbl.append("</tr>")
        tbl.append("</table></div>")
        body.extend(tbl); continue
    para = [line]; i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#","```","|","- ","* ","$$")):
        para.append(lines[i]); i += 1
    body.append(f"<p>{inline(' '.join(para))}</p>")

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{repo_name} 仓库手册指南</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'\\\\(',right:'\\\\)',display:false}},{{left:'\\\\[',right:'\\\\]',display:true}}]}});"></script>
<style>
body {{ font-family: -apple-system, "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif; max-width: 920px; margin: 0 auto; padding: 2rem; line-height: 1.75; color: #24292f; }}
h1,h2,h3,h4 {{ color: #0b3d91; margin-top: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
pre {{ background: #f6f8fa; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
code {{ font-family: Consolas, Monaco, monospace; font-size: .92em; }}
.table-wrap {{ width: 100%; overflow-x: auto; margin: 1em 0; }}
table {{ border-collapse: collapse; width: max-content; min-width: 100%; margin: 0; }}
th, td {{ border: 1px solid #d0d7de; padding: .5em .7em; text-align: left; }}
th {{ background: #eef2f7; }}
img {{ max-width: 100%; max-height: 82vh; height: auto; object-fit: contain; display: block; margin: 1em auto; }}
blockquote {{ border-left: 4px solid #0b3d91; margin: 1em 0; padding: .5em 1em; background: #f6f8fa; color: #444; }}
</style></head><body>
{chr(10).join(body)}
</body></html>"""
html_path.write_bytes("\ufeff".encode("utf-8") + html.encode("utf-8"))
```

### 步骤 2: 读取元数据

```python
import os, json
from pathlib import Path
from datetime import datetime

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
profile = json.loads((work_dir / "profile.json").read_text(encoding="utf-8"))
repo_name = profile["repo_name"]
primary_language = profile.get("primary_language", "")
file_count_total = profile.get("file_count_total", 0)
date = profile.get("generated_at") or datetime.now().strftime("%Y-%m-%d")
print(f"REPO_NAME={repo_name}\nPRIMARY_LANGUAGE={primary_language}\nFILE_COUNT={file_count_total}\nDATE={date}")
```

### 步骤 2.5: 图片路径标准化

把 `manual.md` 里引用的本地图片统一复制到 `$WORK_DIR/images/`，路径改为 `images/xxx.png`。

```python
import os, re, shutil
from pathlib import Path
from PIL import Image

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
img_dir = work_dir / "images"; img_dir.mkdir(exist_ok=True)
md_path = work_dir / "manual.md"
md_text = md_path.read_text(encoding="utf-8", errors="ignore")
counter = 0

def normalize_image(m):
    global counter
    alt = m.group(1).strip() or "图"
    src = m.group(2).strip()
    if src.startswith(("http://", "https://")):
        return f"![{alt}]({src})"
    original = Path(src)
    resolved = original if original.is_absolute() else (work_dir / original)
    if not resolved.exists():
        repo_path = Path(os.environ.get("REPO_PATH", work_dir / "repo"))
        resolved = repo_path / original
    if resolved.exists():
        counter += 1
        new_name = f"fig_{counter:03d}.png"
        dst = img_dir / new_name
        try:
            with Image.open(resolved) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                # 限制尺寸
                max_w, max_h = 1800, 2200
                if img.width > max_w or img.height > max_h:
                    scale = min(max_w/img.width, max_h/img.height)
                    img = img.resize((int(img.width*scale), int(img.height*scale)), Image.Resampling.LANCZOS)
                img.save(dst, "PNG", optimize=True)
        except Exception:
            shutil.copy2(resolved, dst)
        return f"![{alt}](images/{new_name})"
    return f"![{alt}]({src})"

new_md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", normalize_image, md_text)
md_path.write_text(new_md_text, encoding="utf-8")
```

### 步骤 2.8: 生成稳定目录页（不依赖空 `.toc`）

renderer 必须从 Markdown 标题直接生成目录页。这样即使 LaTeX 的 `.toc` 没写入，PDF 也不会出现空目录。

```python
# REPOGUIDE_RENDERER_TOC_START
import re

def is_report_title(level: int, title: str) -> bool:
    return level == 1 and "仓库手册指南" in title

def detect_heading_offset(markdown: str) -> int:
    in_fence = False
    for raw in markdown.splitlines():
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", raw)
        if not m:
            continue
        level = len(m.group(1))
        title = re.sub(r"`([^`]+)`", r"\1", m.group(2)).strip()
        return 1 if is_report_title(level, title) else 0
    return 0

def extract_markdown_headings(markdown: str, max_level: int = 2):
    headings = []
    heading_offset = detect_heading_offset(markdown)
    in_fence = False
    for raw in markdown.splitlines():
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", raw)
        if not m:
            continue
        level = len(m.group(1))
        title = re.sub(r"`([^`]+)`", r"\1", m.group(2)).strip()
        if heading_offset and is_report_title(level, title):
            continue
        effective_level = max(1, level - heading_offset)
        if effective_level > 1 and ("—" in title or len(title) > 44):
            continue
        if effective_level <= max_level:
            headings.append({"level": effective_level, "title": title})
    return headings

def build_manual_toc(markdown: str):
    lines = ["\\begin{repoguidetoc}"]
    for item in extract_markdown_headings(markdown):
        cmd = "tocmajor" if item["level"] == 1 else "tocminor"
        lines.append(f"\\{cmd}{{{inline(item['title'])}}}")
    lines.append("\\end{repoguidetoc}")
    return "\n".join(lines)
# REPOGUIDE_RENDERER_TOC_END
```

### 步骤 3: 数学公式感知的 Markdown→LaTeX 转换（关键修复）

宽表合同：生成的 LaTeX 必须包含 `begin{adjustbox}{max width=\textwidth}`，并用 `tabularx` 的 `Y` 列自动换行。

```python
import os, re
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
md_path = work_dir / "manual.md"
out_path = work_dir / "manual-body.tex"

text = md_path.read_text(encoding="utf-8", errors="ignore")
if text.startswith("---"):
    parts = text.split("---", 2)
    if len(parts) >= 3:
        text = parts[2]

# 非数学区的 LaTeX 转义（注意：$ 不在此表中，单独处理）
TEXT_ESCAPES = {
    "\\": "\\textbackslash{}",
    "{": "\\{", "}": "\\}",
    "&": "\\&", "#": "\\#", "%": "\\%",
    "_": "\\_", "$": "\\$",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
    "<": "\\textless{}", ">": "\\textgreater{}",
    "→": "\\ensuremath{\\rightarrow}",
    "←": "\\ensuremath{\\leftarrow}",
    "↔": "\\ensuremath{\\leftrightarrow}",
    "⇒": "\\ensuremath{\\Rightarrow}",
    "≤": "\\ensuremath{\\leq}",
    "≥": "\\ensuremath{\\geq}",
    "≈": "\\ensuremath{\\approx}",
    "≠": "\\ensuremath{\\neq}",
    "×": "\\ensuremath{\\times}",
    "±": "\\ensuremath{\\pm}",
    "α": "\\ensuremath{\\alpha}",
    "β": "\\ensuremath{\\beta}",
    "γ": "\\ensuremath{\\gamma}",
    "δ": "\\ensuremath{\\delta}",
    "λ": "\\ensuremath{\\lambda}",
    "μ": "\\ensuremath{\\mu}",
    "σ": "\\ensuremath{\\sigma}",
    "τ": "\\ensuremath{\\tau}",
    "ρ": "\\ensuremath{\\rho}",
    "π": "\\ensuremath{\\pi}",
    "θ": "\\ensuremath{\\theta}",
    "Δ": "\\ensuremath{\\Delta}",
    "Σ": "\\ensuremath{\\Sigma}",
    "Ω": "\\ensuremath{\\Omega}",
}
# 数学区内不转义任何字符（保留 ^ _ $ 原样）

def escape_text(s):
    return "".join(TEXT_ESCAPES.get(c, c) for c in s)

def inline(s):
    # 所有 LaTeX 片段都先占位，普通文本整体转义后再还原，避免命令被二次转义。
    fragments = []
    def stash(fragment):
        token = f"\x00LATEX{len(fragments)}\x00"
        fragments.append((token, fragment))
        return token

    s = re.sub(r"`([^`]+)`", lambda m: stash(f"\\texttt{{{escape_text(m.group(1))}}}"), s)
    s = re.sub(r"\$([^$\n]+)\$", lambda m: stash(f"\\({m.group(1)}\\)"), s)
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: stash(f"\\href{{{escape_text(m.group(2))}}}{{{escape_text(m.group(1))}}}"),
        s,
    )
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: stash(f"\\textbf{{{escape_text(m.group(1))}}}"), s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", lambda m: stash(f"\\textit{{{escape_text(m.group(1))}}}"), s)

    rendered = escape_text(s)
    for token, fragment in fragments:
        rendered = rendered.replace(token, fragment)
    return rendered

def figure_env(alt, src):
    alt = inline(alt) or "图"
    if src.startswith(("http://", "https://")):
        return (f"\\begin{{figure}}[htbp]\n  \\centering\n"
                f"  \\fbox{{\\parbox{{0.8\\textwidth}}{{\\centering [{alt}]}}}}\n"
                f"  \\caption{{{alt}}}\n\\end{{figure}}")
    # 自适应尺寸：不溢出，小图不放大
    return (f"\\begin{{figure}}[htbp]\n  \\centering\n"
            f"  \\includegraphics[width=\\linewidth,height=0.75\\textheight,keepaspectratio]{{\\detokenize{{{src}}}}}\n"
            f"  \\caption{{{alt}}}\n\\end{{figure}}")

def parse_table(lines, start):
    header = lines[start].strip()
    sep = lines[start+1].strip() if start+1 < len(lines) else ""
    if not sep or "-" not in sep or not all(c in "-|: " for c in sep):
        return None, start
    cols = header.split("|")[1:-1]
    n = len(cols)
    # REPOGUIDE_RENDERER_SAFE_TABLE_START
    col_spec = "Y" * max(n, 1)
    out = [
        "\\begin{center}",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabularx}{\\textwidth}{" + col_spec + "}",
        "\\toprule",
        " & ".join(inline(c.strip()) for c in cols) + " \\\\",
        "\\midrule",
    ]
    i = start+2
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = lines[i].strip().split("|")[1:-1]
        row = row[:n] + [""]*(n-len(row))
        out.append(" & ".join(inline(c.strip()) for c in row) + " \\\\")
        i += 1
    out += ["\\bottomrule", "\\end{tabularx}", "\\end{adjustbox}", "\\end{center}"]
    # REPOGUIDE_RENDERER_SAFE_TABLE_END
    return out, i

lines = text.splitlines()
heading_offset = detect_heading_offset(text) if "detect_heading_offset" in globals() else 0
out = []
i = 0
while i < len(lines):
    line = lines[i]; s = line.strip()

    # 块级数学 $$...$$
    if s.startswith("$$"):
        if s.endswith("$$") and len(s) > 2:
            math = s[2:-2].strip()
            out.append(f"\\[{math}\\]")
            i += 1; continue
        math_lines = [s[2:]]
        i += 1
        while i < len(lines) and not lines[i].strip().endswith("$$"):
            math_lines.append(lines[i]); i += 1
        if i < len(lines):
            math_lines.append(lines[i].rstrip()[:-2]); i += 1
        out.append(f"\\[{' '.join(m for m in math_lines if m).strip()}\\]")
        continue

    # 代码块
    if s.startswith("```"):
        lang = s[3:].strip()
        i += 1; code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i]); i += 1
        lang_map = {"python":"Python","py":"Python","bash":"bash","sh":"bash",
                    "javascript":"JavaScript","js":"JavaScript","text":"{}","dot":"{}"}
        lstlang = lang_map.get(lang, lang or "{}")
        out.append(f"\\begin{{lstlisting}}[language={lstlang}]")
        out.append("\n".join(code))  # 代码内容不转义（listings 原样处理）
        out.append("\\end{lstlisting}")
        i += 1; continue

    if s.startswith("#"):
        level = len(s) - len(s.lstrip("#"))
        if level <= 6 and s[level:].startswith(" "):
            title = s[level+1:].strip()
            if heading_offset and "is_report_title" in globals() and is_report_title(level, title):
                i += 1; continue
            effective_level = max(1, level - heading_offset)
            cmd = ["\\section","\\subsection","\\subsubsection","\\paragraph","\\subparagraph","\\subparagraph"][min(effective_level-1,5)]
            out.append(f"{cmd}{{{inline(title)}}}")
            i += 1; continue

    if s.startswith("|"):
        tbl, ni = parse_table(lines, i)
        if tbl:
            out.extend(tbl); i = ni; continue

    if s in ("---","***","___"):
        out.append("\\par\\noindent\\rule{\\textwidth}{0.4pt}"); i += 1; continue
    if not s:
        out.append(""); i += 1; continue
    if s.startswith("!["):
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            out.append(figure_env(m.group(1), m.group(2))); i += 1; continue
    if s.startswith(">"):
        quotes = []
        while i < len(lines) and lines[i].strip().startswith(">"):
            quotes.append(lines[i].strip()[1:].strip())
            i += 1
        out.append("\\begin{tcolorbox}[notebox]")
        out.append(inline(" ".join(q for q in quotes if q)))
        out.append("\\end{tcolorbox}")
        continue
    if s.startswith(("- ","* ","+ ")):
        items=[s[2:]]; i+=1
        while i<len(lines) and lines[i].strip().startswith(("- ","* ","+ ")):
            items.append(lines[i].strip()[2:]); i+=1
        out.append("\\begin{itemize}")
        for it in items: out.append(f"  \\item {inline(it)}")
        out.append("\\end{itemize}"); continue
    if re.match(r"^\d+\.\s", s):
        items=[re.sub(r"^\d+\.\s","",s)]; i+=1
        while i<len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
            items.append(re.sub(r"^\d+\.\s","",lines[i].strip())); i+=1
        out.append("\\begin{enumerate}")
        for it in items: out.append(f"  \\item {inline(it)}")
        out.append("\\end{enumerate}"); continue

    para=[line]; i+=1
    while (
        i < len(lines)
        and lines[i].strip()
        and not lines[i].strip().startswith(("#", "```", "|", "- ", "* ", "+ ", "$$", "![", ">"))
        and not re.match(r"^\d+\.\s", lines[i].strip())
    ):
        para.append(lines[i]); i+=1
    out.append(inline(" ".join(para)))

body_tex = "\n".join(out)
if "build_manual_toc" in globals():
    body_tex = build_manual_toc(text) + "\n\\newpage\n\n" + body_tex
out_path.write_text(body_tex, encoding="utf-8")
```

**与旧版的区别（修复点）**：
- 不再把 `$` 转义为 `\$`；数学段被占位符保护后原样输出为 `\(...\)` / `\[...\]`。
- 数学段内 `^`、`_` 不转义，公式正常渲染。
- 图片用 `width=\linewidth,height=0.75\textheight,keepaspectratio`，小图不放大、大图不溢出。

### 步骤 4: 填充模板

从 `references/latex-template/main.tex` 复制到 `$WORK_DIR/<repo_name>-manual.tex`，替换占位符（值须 LaTeX 转义，`{CONTENT}` 除外）。

```python
import os
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
repo_name = os.environ.get("REPO_NAME", "repo")
primary_language = os.environ.get("PRIMARY_LANGUAGE", "")
file_count = os.environ.get("FILE_COUNT", "0")
date = os.environ.get("DATE", "")

template_path = Path("references/latex-template/main.tex")
tex_path = work_dir / f"{repo_name}-manual.tex"
body = (work_dir / "manual-body.tex").read_text(encoding="utf-8", errors="ignore")
template = template_path.read_text(encoding="utf-8", errors="ignore")

LATEX_ESC = {"\\":"\\textbackslash{}","{":"\\{","}":"\\}","$":"\\$","&":"\\&","#":"\\#","_":"\\_","%":"\\%","~":"\\textasciitilde{}","^":"\\textasciicircum{}"}
def esc(s): return "".join(LATEX_ESC.get(c,c) for c in s)

for ph, val in sorted({
    "{TITLE}": esc(f"{repo_name} 仓库手册指南"),
    "{REPO_NAME}": esc(repo_name),
    "{PRIMARY_LANGUAGE}": esc(primary_language),
    "{FILE_COUNT}": esc(str(file_count)),
    "{DATE}": esc(date),
    "{CONTENT}": body,
}.items(), key=lambda x: -len(x[0])):
    template = template.replace(ph, val)
tex_path.write_text(template, encoding="utf-8")
```

### 步骤 5: 编译 PDF（两次以生成目录）

```bash
cd "$WORK_DIR"
xelatex -interaction=nonstopmode "${REPO_NAME}-manual.tex"
xelatex -interaction=nonstopmode "${REPO_NAME}-manual.tex"
```

### 步骤 6: 复制到用户目录

```bash
[ -f "$WORK_DIR/${REPO_NAME}-manual.pdf" ] && cp "$WORK_DIR/${REPO_NAME}-manual.pdf" "$PWD/"
[ -f "$WORK_DIR/${REPO_NAME}-manual.html" ] && cp "$WORK_DIR/${REPO_NAME}-manual.html" "$PWD/"
cp "$WORK_DIR/manual.md" "$PWD/${REPO_NAME}-manual.md"
```

## 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| 公式渲染失败 | 旧版把 `$`→`\$`、`^`/`_` 转义 | 数学段占位符保护，原样输出 `\(...\)`/`\[...\]` |
| 图片太大撑破页面 | 固定 `width=0.85\textwidth` | 改 `width=\linewidth,height=0.75\textheight,keepaspectratio` |
| 论文图碎片 | 用 `get_images` 抽裸 raster | 改用 `get_image_info` bbox + clip 渲染（见 image-handler） |
| 中文乱码 | 缺 CJK 字体 | ctex + 系统字体 |
| PDF 无目录 | 依赖空 `.toc` 或只编译一次 | renderer 从 Markdown 标题生成稳定目录页，并保留 xelatex 两次编译 |
| 目录/表格编译失败 | 文件名、方法名、Windows 路径里的 `_` 未转义 | 普通文本统一转义，代码片段先保护再处理数学 |
| 宽表/图片只显示一部分 | 固定表格或图片尺寸超过版心 | 表格包裹 `adjustbox`，图片设置宽高上限并保持比例 |

## 输出

- `<cwd>/<repo_name>-manual.pdf`（需 xelatex）
- `<cwd>/<repo_name>-manual.html`（xelatex 不可用时降级）
- `<cwd>/<repo_name>-manual.md`
