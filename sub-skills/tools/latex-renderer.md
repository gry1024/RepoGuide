---
name: repoguide-tool-latex-renderer
description: RepoGuide 的 LaTeX / xelatex PDF 渲染方法：数学公式感知的 Markdown→LaTeX 转换、自适应图片尺寸、中文 PDF。全部以代码片段写在 md 中由 agent 执行。
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

> **多页 HTML + 侧边导航 + Apple 极简风格**（P0-1 改造）。
> - deep 模式：按概念分页（`index.html` + 每个概念一个 `concept-<id>.html`），侧边导航按 `reading_path` 排序。
> - standard 模式：单页 `index.html`，侧边导航为目录锚点。
> - `<details>` 折叠区默认收起；blockquote 正确渲染；图片自适应；KaTeX 渲染公式。
> - 风格遵循 Apple 极简：#FBFBFD 背景、#1D1D1F 正文、#86868B 次要文本、克制强调色、微圆角、无投影。

```python
# REPOGUIDE_HTML_RENDER_START
import os, re, json
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
repo_name = os.environ.get("REPO_NAME", "repo")
md_path = work_dir / "manual.md"
html_dir = work_dir / "html"
html_dir.mkdir(parents=True, exist_ok=True)

# 读取概念层数据（决定是否分页 + 侧边导航顺序）
concepts_path = work_dir / "analysis_concepts.json"
HAS_CONCEPTS = concepts_path.exists()
concepts_data = {}
if HAS_CONCEPTS:
    try:
        concepts_data = json.loads(concepts_path.read_text(encoding="utf-8"))
    except Exception:
        HAS_CONCEPTS = False
        concepts_data = {}

depth = os.environ.get("DEPTH_OVERRIDE", "")
if not depth:
    try:
        depth = json.loads((work_dir / "profile.json").read_text(encoding="utf-8")).get("depth", "standard")
    except Exception:
        depth = "standard"
IS_DEEP = depth == "deep"

# 读取 manual.md
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
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img src="../{escape_html(m.group(2))}" alt="{escape_html(m.group(1))}">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{escape_html(m.group(2))}">{escape_html(m.group(1))}</a>', s)
    s = s.replace("\x00MATH\x01", '<span class="math">\\(').replace("\x02MATH\x00", '\\)</span>')
    return s

def parse_block(lines, i):
    """解析一个块级元素，返回 (html_str, next_i)。"""
    line = lines[i]
    s = line.strip()
    # 块级数学 $$...$$
    if s.startswith("$$"):
        math_lines = [s[2:]]
        if s.endswith("$$") and len(s) > 2:
            return f'<div class="math">\\[{escape_html(" ".join(math_lines))}\\]</div>', i + 1
        i += 1
        while i < len(lines) and not lines[i].strip().endswith("$$"):
            math_lines.append(lines[i]); i += 1
        if i < len(lines):
            math_lines.append(lines[i].rstrip()[:-2]); i += 1
        return f'<div class="math">\\[{escape_html(" ".join(math_lines))}\\]</div>', i
    # 代码块
    if s.startswith("```"):
        i += 1
        code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i]); i += 1
        i += 1
        return f"<pre><code>{escape_html(chr(10).join(code))}</code></pre>", i
    # HTML 锚点（<a id=...>）原样保留
    if s.startswith("<a id=") and "</a>" in s:
        return s, i + 1
    # 标题
    if s.startswith("#"):
        level = len(s) - len(s.lstrip("#"))
        if level <= 6 and s[level:].startswith(" "):
            title = s[level+1:].strip()
            anchor = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title.lower()).strip('-')
            return f'<h{level} id="{anchor}">{inline(title)}</h{level}>', i + 1
    # 分割线
    if s in ("---", "***", "___"):
        return "<hr>", i + 1
    # 空行
    if not s:
        return "", i + 1
    # blockquote（P1-5：正确渲染 > 引用）
    if s.startswith(">"):
        items = [s[1:].strip()]; i += 1
        while i < len(lines) and lines[i].strip().startswith(">"):
            items.append(lines[i].strip()[1:].strip()); i += 1
        return f"<blockquote>{inline(' '.join(items))}</blockquote>", i
    # 无序列表
    if s.startswith(("- ", "* ", "+ ")):
        items = [s[2:]]; i += 1
        while i < len(lines) and lines[i].strip().startswith(("- ", "* ", "+ ")):
            items.append(lines[i].strip()[2:]); i += 1
        ul = "<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>"
        return ul, i
    # 表格
    if s.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append(lines[i].strip()); i += 1
        if len(rows) >= 2:
            tbl = ['<div class="table-wrap"><table>']
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
            return "".join(tbl), i
        return "", i
    # <details> 折叠区（原样保留，内部内容递归解析）
    if s == "<details>":
        inner = []; i += 1
        while i < len(lines) and lines[i].strip() != "</details>":
            html_str, i = parse_block(lines, i)
            if html_str:
                inner.append(html_str)
        if i < len(lines):
            i += 1  # skip </details>
        return "<details>" + "".join(inner) + "</details>", i
    if s.startswith("<summary>") and s.endswith("</summary>"):
        return s, i + 1
    # 段落
    para = [line]; i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#","```","|","- ","* ","$$",">","<details>","<summary>","<a id=")):
        para.append(lines[i]); i += 1
    return f"<p>{inline(' '.join(para))}</p>", i

# ===== 将 manual.md 切分为块列表，记录标题层级用于侧边导航 =====
lines = text.splitlines()
blocks = []  # [(html_str, heading_info_or_None)]
i = 0
while i < len(lines):
    start_i = i
    html_str, i = parse_block(lines, i)
    # 检测是否是标题块
    orig = lines[start_i].strip() if start_i < len(lines) else ""
    heading_info = None
    if orig.startswith("#"):
        level = len(orig) - len(orig.lstrip("#"))
        if level <= 6 and orig[level:].startswith(" "):
            title = orig[level+1:].strip()
            heading_info = {"level": level, "title": title, "line": start_i}
    blocks.append((html_str, heading_info))

# ===== 侧边导航构建 =====
# 概念页导航（deep 分页模式）
concept_nav = []  # [{"id","name","file","order}]
if HAS_CONCEPTS and IS_DEEP:
    reading_path = concepts_data.get("reading_path", [])
    concepts_by_id = {c["id"]: c for c in concepts_data.get("concepts", [])}
    for cid in reading_path:
        c = concepts_by_id.get(cid, {})
        concept_nav.append({
            "id": cid,
            "name": c.get("name", cid),
            "file": f"concept-{cid}.html",
            "order": c.get("teaching_order", 0),
        })

# 单页模式：从标题提取目录
toc_nav = []
for _, h in blocks:
    if h and h["level"] <= 3:
        toc_nav.append(h)

# ===== Apple 极简风格 CSS =====
CSS = """
:root { --bg: #FBFBFD; --text: #1D1D1F; --muted: #86868B; --accent: #0071e3; --border: #d2d2d7; --code-bg: #f5f5f7; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "SF Pro Display", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif; margin: 0; background: var(--bg); color: var(--text); line-height: 1.6; font-weight: 400; }
.layout { display: flex; min-height: 100vh; }
.sidebar { width: 260px; flex-shrink: 0; background: var(--bg); border-right: 1px solid var(--border); position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 2rem 1.25rem; }
.sidebar h2 { font-size: 1.05rem; font-weight: 600; margin: 0 0 1rem; color: var(--text); }
.sidebar a { display: block; color: var(--muted); text-decoration: none; font-size: 0.85rem; padding: 0.35rem 0.5rem; border-radius: 6px; transition: all 0.15s; }
.sidebar a:hover { color: var(--text); background: var(--code-bg); }
.sidebar a.active { color: var(--accent); font-weight: 500; }
.sidebar .nav-order { display: inline-block; width: 1.5rem; color: var(--muted); font-variant-numeric: tabular-nums; }
.sidebar .nav-section { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 1.25rem 0 0.5rem; font-weight: 600; }
.content { flex: 1; max-width: 820px; margin: 0 auto; padding: 3rem 2.5rem; }
h1 { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; margin-top: 0; }
h2 { font-size: 1.5rem; font-weight: 600; letter-spacing: -0.01em; margin-top: 2.5rem; padding-bottom: 0.4rem; border-bottom: 1px solid var(--border); }
h3 { font-size: 1.2rem; font-weight: 600; margin-top: 2rem; }
h4 { font-size: 1.05rem; font-weight: 600; margin-top: 1.5rem; }
h5 { font-size: 0.95rem; font-weight: 600; margin-top: 1.2rem; }
p { font-size: 0.95rem; color: var(--text); }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
strong { font-weight: 600; }
code { font-family: "SF Mono", Consolas, Monaco, monospace; font-size: 0.85em; background: var(--code-bg); padding: 0.15em 0.35em; border-radius: 4px; }
pre { background: var(--code-bg); padding: 1rem 1.25rem; border-radius: 10px; overflow-x: auto; margin: 1rem 0; }
pre code { background: none; padding: 0; font-size: 0.85rem; line-height: 1.5; }
.table-wrap { width: 100%; overflow-x: auto; margin: 1.25rem 0; }
table { border-collapse: collapse; width: max-content; min-width: 100%; font-size: 0.88rem; }
th, td { border-bottom: 1px solid var(--border); padding: 0.6rem 0.9rem; text-align: left; }
th { font-weight: 600; color: var(--muted); border-bottom: 2px solid var(--border); }
tr:last-child td { border-bottom: none; }
img { max-width: 100%; height: auto; border-radius: 8px; display: block; margin: 1.25rem auto; }
blockquote { border-left: 3px solid var(--accent); margin: 1.25rem 0; padding: 0.5rem 1.25rem; color: var(--muted); background: none; }
blockquote strong { color: var(--text); }
hr { border: none; border-top: 1px solid var(--border); margin: 2.5rem 0; }
details { margin: 1rem 0; border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 1rem; }
summary { cursor: pointer; font-weight: 500; color: var(--accent); padding: 0.25rem 0; }
details[open] summary { margin-bottom: 0.5rem; }
.math { margin: 1rem 0; text-align: center; }
.nav-footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 0.85rem; }
.nav-footer a { color: var(--accent); }
@media (max-width: 768px) { .sidebar { display: none; } .content { padding: 1.5rem; } }
"""

KATEX = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\\\(',right:'\\\\)',display:false},{left:'\\\\[',right:'\\\\]',display:true}]});"></script>
"""

def build_sidebar(active_id=None, active_href=None):
    """构建侧边导航 HTML。"""
    parts = [f'<aside class="sidebar">', f'<h2>{repo_name}</h2>']
    if HAS_CONCEPTS and IS_DEEP and concept_nav:
        # deep 分页模式：按 reading_path 排列概念
        parts.append('<div class="nav-section">推荐阅读路径</div>')
        for item in concept_nav:
            cls = " active" if item["id"] == active_id else ""
            parts.append(f'<a href="{item["file"]}" class="{cls}"><span class="nav-order">{item["order"]}.</span>{item["name"]}</a>')
        parts.append(f'<a href="index.html" class="{"" if active_href != "index.html" else "active"}"><span class="nav-order">★</span>总览与附录</a>')
    else:
        # 单页模式：从标题提取目录
        parts.append('<div class="nav-section">目录</div>')
        for h in toc_nav:
            indent = "  " * (h["level"] - 1)
            title = h["title"]
            # 生成锚点
            anchor = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title.lower()).strip('-')
            parts.append(f'<a href="#{anchor}">{indent}{title}</a>')
    parts.append('</aside>')
    return "\n".join(parts)

def build_page(title, body_html, sidebar_html, prev_link="", next_link=""):
    """组装完整 HTML 页面。"""
    nav_footer = ""
    if prev_link or next_link:
        nav_footer = '<div class="nav-footer">'
        nav_footer += prev_link or "<span></span>"
        nav_footer += next_link or "<span></span>"
        nav_footer += "</div>"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{KATEX}
<style>{CSS}</style>
</head><body>
<div class="layout">
{sidebar_html}
<main class="content">
{body_html}
{nav_footer}
</main>
</div>
</body></html>"""

# ===== 分页策略 =====
# deep + 概念层：每个概念卡片单独一页，其余内容归入 index.html
# 否则：单页 index.html

if HAS_CONCEPTS and IS_DEEP:
    # 找到 "## 四、核心概念导览" 和 "## 五、文件速览表" 的位置
    sec4_start = None
    sec5_start = None
    for idx, (_, h) in enumerate(blocks):
        if h and h["level"] == 2 and "核心概念导览" in h["title"]:
            sec4_start = idx
        if h and h["level"] == 2 and "文件速览表" in h["title"]:
            sec5_start = idx

    index_blocks = []
    concept_blocks = {}

    if sec4_start is not None and sec5_start is not None:
        index_blocks.extend(blocks[:sec4_start])
        idx = sec4_start + 1
        while idx < sec5_start:
            _, h = blocks[idx]
            if h and h["level"] == 3 and h["title"].startswith("概念 "):
                break
            index_blocks.append(blocks[idx])
            idx += 1
        reading_path = concepts_data.get("reading_path", [])
        concepts_by_id = {c["id"]: c for c in concepts_data.get("concepts", [])}
        current_concept_id = None
        current_blocks = []
        while idx < sec5_start:
            blk, h = blocks[idx]
            if h and h["level"] == 3 and h["title"].startswith("概念 "):
                if current_concept_id:
                    concept_blocks[current_concept_id] = current_blocks
                current_concept_id = None
                next_idx = len(concept_blocks)
                if next_idx < len(reading_path):
                    current_concept_id = reading_path[next_idx]
                current_blocks = []
            current_blocks.append(blocks[idx])
            idx += 1
        if current_concept_id:
            concept_blocks[current_concept_id] = current_blocks
        index_blocks.extend(blocks[sec5_start:])
    else:
        index_blocks = blocks

    # ===== 1. 生成 html/ 多页目录（deep 模式，浏览器分页浏览） =====
    index_body = "\n".join(b[0] for b in index_blocks if b[0])
    index_sidebar = build_sidebar(active_href="index.html")
    index_html = build_page(f"{repo_name} 仓库手册指南", index_body, index_sidebar)
    (html_dir / "index.html").write_bytes("\ufeff".encode("utf-8") + index_html.encode("utf-8"))

    for cid in concepts_data.get("reading_path", []):
        c = concepts_by_id.get(cid, {})
        cblocks = concept_blocks.get(cid, [])
        cbody = "\n".join(b[0] for b in cblocks if b[0])
        csidebar = build_sidebar(active_id=cid)
        path_idx = concepts_data.get("reading_path", []).index(cid)
        prev_link = ""
        next_link = ""
        if path_idx > 0:
            prev_cid = concepts_data["reading_path"][path_idx - 1]
            prev_name = concepts_by_id.get(prev_cid, {}).get("name", "")
            prev_link = f'<a href="concept-{prev_cid}.html">← {prev_name}</a>'
        if path_idx < len(concepts_data.get("reading_path", [])) - 1:
            next_cid = concepts_data["reading_path"][path_idx + 1]
            next_name = concepts_by_id.get(next_cid, {}).get("name", "")
            next_link = f'<a href="concept-{next_cid}.html">{next_name} →</a>'
        ctitle = f"概念 {c.get('teaching_order','')}：{c.get('name','')} - {repo_name}"
        chtml = build_page(ctitle, cbody, csidebar, prev_link, next_link)
        (html_dir / f"concept-{cid}.html").write_bytes("\ufeff".encode("utf-8") + chtml.encode("utf-8"))

    print(f"OK: deep multi-page, {1 + len(concept_blocks)} pages in {html_dir}")

    # ===== 2. 生成自包含单页 <repo_name>-manual.html（所有内容+锚点导航，兼容契约） =====
    all_body = "\n".join(b[0] for b in blocks if b[0])
    single_sidebar_parts = [f'<aside class="sidebar">', f'<h2>{repo_name}</h2>']
    single_sidebar_parts.append('<div class="nav-section">推荐阅读路径</div>')
    for cid in concepts_data.get("reading_path", []):
        c = concepts_by_id.get(cid, {})
        single_sidebar_parts.append(f'<a href="#concept-{cid}"><span class="nav-order">{c.get("teaching_order",0)}.</span>{c.get("name",cid)}</a>')
    single_sidebar_parts.append('<div class="nav-section">章节</div>')
    for h in toc_nav:
        if h["level"] == 2:
            anchor = re.sub(r'[^\w\u4e00-\u9fff]+', '-', h["title"].lower()).strip('-')
            single_sidebar_parts.append(f'<a href="#{anchor}">{h["title"]}</a>')
    single_sidebar_parts.append('</aside>')
    single_sidebar = "\n".join(single_sidebar_parts)
    single_html = build_page(f"{repo_name} 仓库手册指南", all_body, single_sidebar)
    single_path = work_dir / f"{repo_name}-manual.html"
    single_path.write_bytes("\ufeff".encode("utf-8") + single_html.encode("utf-8"))
    print(f"OK: single-page {single_path}")
else:
    # ===== standard 或无概念层：单页 =====
    body = "\n".join(b[0] for b in blocks if b[0])
    sidebar = build_sidebar()
    html = build_page(f"{repo_name} 仓库手册指南", body, sidebar)
    (html_dir / "index.html").write_bytes("\ufeff".encode("utf-8") + html.encode("utf-8"))
    print(f"OK: single page in {html_dir}")

    single_path = work_dir / f"{repo_name}-manual.html"
    single_path.write_bytes((html_dir / "index.html").read_bytes())
    print(f"OK: {single_path}")
# REPOGUIDE_HTML_RENDER_END
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

def heading_anchor(line_no: int) -> str:
    return f"repoguide-heading-{line_no}"

def extract_markdown_headings(markdown: str, max_level: int = 2):
    headings = []
    heading_offset = detect_heading_offset(markdown)
    in_fence = False
    for line_no, raw in enumerate(markdown.splitlines(), start=1):
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
            headings.append({"level": effective_level, "title": title, "anchor": heading_anchor(line_no)})
    return headings

def build_manual_toc(markdown: str):
    lines = ["\\begin{repoguidetoc}"]
    for item in extract_markdown_headings(markdown):
        cmd = "tocmajor" if item["level"] == 1 else "tocminor"
        lines.append(f"\\{cmd}{{\\hyperlink{{{item['anchor']}}}{{{inline(item['title'])}}}}}")
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

CODE_LIKE_TOKEN = re.compile(r"[A-Za-z0-9\\][A-Za-z0-9_./:\\{}\[\](),+=^'-]{17,}")
BREAK_AFTER = {"_", "/", ".", "-", "\\", "{", "}", "[", "]", "(", ")", ",", "+", "="}

def escape_raw_text(s):
    return "".join(TEXT_ESCAPES.get(c, c) for c in s)

def escape_breakable_token(token):
    out = []
    for c in token:
        out.append(TEXT_ESCAPES.get(c, c))
        if c in BREAK_AFTER:
            out.append("\\allowbreak{}")
    return "".join(out)

def escape_text(s):
    out = []
    pos = 0
    for m in CODE_LIKE_TOKEN.finditer(s):
        token = m.group(0)
        out.append(escape_raw_text(s[pos:m.start()]))
        if any(ch in token for ch in BREAK_AFTER):
            out.append(escape_breakable_token(token))
        else:
            out.append(escape_raw_text(token))
        pos = m.end()
    out.append(escape_raw_text(s[pos:]))
    return "".join(out)

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
        lambda m: stash(f"\\href{{{escape_raw_text(m.group(2))}}}{{{escape_text(m.group(1))}}}"),
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
    rows = []
    i = start+2
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = lines[i].strip().split("|")[1:-1]
        rows.append(row[:n] + [""]*(n-len(row)))
        i += 1

    def rendered_row(row):
        return " & ".join(inline(c.strip()) for c in row) + " \\\\"

    def longtable_col_spec(count):
        count = max(count, 1)
        presets = {
            2: [0.34, 0.62],
            3: [0.30, 0.35, 0.31],
            4: [0.27, 0.30, 0.31, 0.10],
            5: [0.21, 0.22, 0.22, 0.21, 0.10],
        }
        fractions = presets.get(count, [0.96 / count] * count)
        cells = [
            f">{{\\raggedright\\arraybackslash}}p{{\\dimexpr{frac:.3f}\\textwidth-2\\tabcolsep\\relax}}"
            for frac in fractions
        ]
        return "@{}" + "".join(cells) + "@{}"

    long_table = len(rows) > 10 or any(len(c) > 90 for row in rows for c in row)
    # REPOGUIDE_RENDERER_SAFE_TABLE_START
    col_spec = "Y" * max(n, 1)
    header_row = rendered_row(cols)
    if long_table:
        long_spec = longtable_col_spec(n)
        out = [
            "\\begingroup",
            "\\footnotesize",
            "\\setlength{\\tabcolsep}{3pt}",
            "\\begin{longtable}{" + long_spec + "}",
            "\\toprule",
            header_row,
            "\\midrule",
            "\\endfirsthead",
            "\\toprule",
            header_row,
            "\\midrule",
            "\\endhead",
        ]
        out.extend(rendered_row(row) for row in rows)
        out += ["\\bottomrule", "\\end{longtable}", "\\endgroup"]
        return out, i

    out = [
        "\\begingroup",
        "\\footnotesize",
        "\\setlength{\\tabcolsep}{4pt}",
        "\\begin{center}",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabularx}{\\textwidth}{" + col_spec + "}",
        "\\toprule",
        header_row,
        "\\midrule",
    ]
    out.extend(rendered_row(row) for row in rows)
    out += ["\\bottomrule", "\\end{tabularx}", "\\end{adjustbox}", "\\end{center}", "\\endgroup"]
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
            anchor = heading_anchor(i + 1) if "heading_anchor" in globals() else f"repoguide-heading-{i + 1}"
            out.append(f"\\hypertarget{{{anchor}}}{{}}\n{cmd}{{{inline(title)}}}")
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
