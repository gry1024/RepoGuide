---
name: repoguide-tool-image-handler
description: RepoGuide 图像处理工具：按区域裁剪论文图、过滤碎片、graphviz 渲染架构总览图、扫描仓库图片，全部以代码片段写在 md 中由 agent 执行。
---

# RepoGuide · 图像处理

## 设计原则

1. **论文图按区域裁剪**：不再用 `get_images` 抽裸 raster（会得到碎片/满页图）。改用 `page.get_image_info()` 拿到每张图在页面上的 bbox，再以该 bbox 为 clip 用 `page.get_pixmap(clip=rect, dpi=200)` 渲染，得到完整且尺寸合适的图。
2. **过滤碎片**：丢弃面积过小（如 < 80×80）的图标/公式片段；合并同页距离很近的多个 bbox（同一张图被切片的情况）。
3. **架构总览图用 graphviz**：从 `analysis_arch.json.architecture_overview_dot` 读取 DOT，调用系统 `dot` 命令生成 `architecture_overview.png`（不依赖 mermaid-cli）。
4. **图片统一放 `$WORK_DIR/images/`**，手册用相对路径引用。

## 依赖

- `PyMuPDF`（fitz）—— 已确认可用
- `Pillow` —— 已确认可用
- 系统 `dot`（graphviz）—— 已确认可用；若不可用则跳过架构图并记录 limitation

## 1. 按区域裁剪论文图（核心改进）

```python
# REPOGUIDE_PAPER_FIGURE_EXTRACT_START
import os
import json
from pathlib import Path
import fitz  # PyMuPDF

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
pdf_path = work_dir / "paper.pdf"
out_dir = work_dir / "images"
out_dir.mkdir(parents=True, exist_ok=True)

MIN_W, MIN_H = 80, 80          # 过滤小图标/公式碎片
MERGE_GAP = 12                 # 同页 bbox 间距 ≤ 此值则合并（pt）
DPI = 200                      # 渲染分辨率，清晰且不过大

def union(a, b):
    return fitz.Rect(min(a.x0, b.x0), min(a.y0, b.y0), max(a.x1, b.x1), max(a.y1, b.y1))

def close(a, b, gap):
    return (abs(a.x0 - b.x0) < gap and a.y1 >= b.y0 - gap and a.y0 <= b.y1 + gap) or \
           (abs(a.y0 - b.y0) < gap and a.x1 >= b.x0 - gap and a.x0 <= b.x1 + gap) or \
           (a.intersects(b))

extracted = []
if pdf_path.exists():
    doc = fitz.open(pdf_path)
    for pno in range(len(doc)):
        page = doc[pno]
        info = page.get_image_info(xrefs=True)
        rects = []
        for im in info:
            bb = im.get("bbox")
            if not bb:
                continue
            r = fitz.Rect(bb)
            if r.width < MIN_W or r.height < MIN_H:
                continue
            rects.append(r)
        # 合并相近 bbox
        merged = []
        changed = True
        pool = rects[:]
        while pool:
            cur = pool.pop(0)
            again = True
            while again:
                again = False
                leftover = []
                for r in pool:
                    if close(cur, r, MERGE_GAP):
                        cur = union(cur, r)
                        again = True
                    else:
                        leftover.append(r)
                pool = leftover
            merged.append(cur)
        for idx, r in enumerate(merged, start=1):
            if r.width < MIN_W or r.height < MIN_H:
                continue
            clip = r & page.rect  # 限制在页内
            pix = page.get_pixmap(clip=clip, dpi=DPI)
            name = f"paper_p{pno+1}_img{idx}.png"
            pix.save(str(out_dir / name))
            extracted.append({"path": f"images/{name}", "page": pno+1,
                              "caption": f"论文第 {pno+1} 页图 {idx}",
                              "width": pix.width, "height": pix.height})
    doc.close()
print(json.dumps(extracted, ensure_ascii=False, indent=2))
# REPOGUIDE_PAPER_FIGURE_EXTRACT_END
```

要点：
- `get_image_info` 返回每张嵌入图在页面的 bbox，比 `get_images` 更适合定位。
- 用 bbox 作 clip 渲染，得到的是"图所在区域"而非"原始嵌入位图"，避免巨型/碎片。
- `MERGE_GAP` 合并同图被切片的情况。

## 2. 扫描仓库图片资源

```python
import os
from pathlib import Path

REPO_PATH = Path(os.environ.get("REPO_PATH", "_repoguide/repo")).resolve()
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

repo_figs = []
for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.gif", "*.webp"):
    for f in REPO_PATH.rglob(ext):
        if any(p in f.parts for p in IGNORE_DIRS):
            continue
        repo_figs.append({"path": f.relative_to(REPO_PATH).as_posix(),
                          "type": f.suffix.lstrip("."), "size": f.stat().st_size})
```

## 3. graphviz 渲染架构总览图（替代 mermaid）

```python
# REPOGUIDE_GRAPHVIZ_RENDER_START
import os, json, subprocess
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
out_dir = work_dir / "images"
out_dir.mkdir(parents=True, exist_ok=True)

arch = json.loads((work_dir / "analysis_arch.json").read_text(encoding="utf-8"))
dot_src = arch.get("architecture_overview_dot", "")
generated = []

if dot_src and dot_src.strip().startswith("digraph"):
    dot_path = work_dir / "architecture_overview.dot"
    png_path = out_dir / "architecture_overview.png"
    dot_path.write_text(dot_src, encoding="utf-8")
    try:
        subprocess.run(
            ["dot", "-Tpng", "-Gdpi=150", "-o", str(png_path), str(dot_path)],
            check=True, capture_output=True, timeout=120,
        )
        if png_path.exists():
            generated.append({"path": "images/architecture_overview.png",
                              "source": "graphviz", "caption": "架构总览图"})
        else:
            generated.append({"path": "", "source": "graphviz", "caption": "架构总览图渲染失败"})
    except Exception as e:
        generated.append({"path": "", "source": "graphviz",
                          "caption": f"架构总览图渲染失败：{e}"})
else:
    generated.append({"path": "", "source": "graphviz", "caption": "缺少 architecture_overview_dot"})

print(json.dumps(generated, ensure_ascii=False, indent=2))
# REPOGUIDE_GRAPHVIZ_RENDER_END
```

## 4. manifest 对账（扫描 images/ 目录，分类已有图片）

```python
# REPOGUIDE_IMAGE_MANIFEST_RECONCILE_START
import os, json, re
from pathlib import Path

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
img_dir = work_dir / "images"
img_dir.mkdir(parents=True, exist_ok=True)

paper_figures, repo_figures, generated_diagrams = [], [], []
for f in sorted(img_dir.glob("*.png")):
    rel = f"images/{f.name}"
    size = f.stat().st_size
    if f.name.startswith("paper_p") and re.match(r"paper_p\d+_img\d+\.png", f.name):
        m = re.match(r"paper_p(\d+)_img(\d+)\.png", f.name)
        paper_figures.append({"path": rel, "page": int(m.group(1)),
                              "caption": f"论文第 {m.group(1)} 页图 {m.group(2)}", "size": size})
    elif f.name.startswith("repo_"):
        repo_figures.append({"path": rel, "type": "png", "size": size})
    elif f.name == "architecture_overview.png":
        generated_diagrams.append({"path": rel, "source": "graphviz", "caption": "架构总览图"})
    elif f.name.startswith("generated_"):
        generated_diagrams.append({"path": rel, "source": "graphviz", "caption": f.name[:-4]})

limitations = []
if not paper_figures and (work_dir / "paper.pdf").exists():
    limitations.append("论文原图未从 PDF 中提取。")
# 若已提取到论文图，移除历史遗留的"未提取"限制
limitations = [x for x in limitations if not paper_figures]

manifest = {
    "paper_figures": paper_figures,
    "repo_figures": repo_figures,
    "generated_diagrams": generated_diagrams,
    "limitations": limitations,
}
(work_dir / "image-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
# REPOGUIDE_IMAGE_MANIFEST_RECONCILE_END
```

## 5. 图片优化（控制 PDF 体积 + 保证清晰）

```python
# REPOGUIDE_IMAGE_OPTIMIZE_START
import os
from pathlib import Path
from PIL import Image

work_dir = Path(os.environ.get("WORK_DIR", "_repoguide"))
img_dir = work_dir / "images"
MAX_W = 1800          # 最大宽度，超出按比例缩放
MAX_H = 2200          # 最大高度，避免单图占满整页
QUALITY = 90

optimized_images = []
for f in sorted(img_dir.glob("*.png")):
    try:
        with Image.open(f) as im:
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            w, h = im.size
            scale = min(MAX_W / w, MAX_H / h, 1.0)
            if scale < 1.0:
                im = im.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
            im.save(f, "PNG", optimize=True)
            optimized_images.append(str(f.name))
    except Exception as e:
        print(f"skip {f.name}: {e}")
# REPOGUIDE_IMAGE_OPTIMIZE_END
```

## 6. 嵌入 Markdown / LaTeX

- Markdown：`![图注](images/xxx.png)`，相对路径。
- LaTeX：见 `latex-renderer.md`，统一 `\includegraphics[width=\linewidth,height=0.75\textheight,keepaspectratio]{images/xxx.png}`，自适应不溢出。

## 错误处理

| 错误 | 处理 |
|------|------|
| PDF 无图 | `paper_figures` 为空列表 |
| `dot` 不可用 | 跳过架构图，记录 limitation，手册改用数据流叙述 |
| 图片格式无法识别 | 跳过并记录 |

## 输出

- `$WORK_DIR/images/` 目录
- `$WORK_DIR/image-manifest.json`
- 手册通过相对路径引用图片
