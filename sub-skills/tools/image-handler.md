---
name: repoguide-tool-image-handler
description: RepoGuide 的图像处理工具方法：从论文/仓库提取图片、生成架构图、嵌入 Markdown 与 LaTeX PDF，全部以代码片段写在 md 中由 agent 执行。
---

# RepoGuide · 图像处理

## 能力范围

| 能力 | 场景 |
|------|------|
| 从论文 PDF 提取图片 | 论文中的模型图、流程图、实验图 |
| 扫描仓库图片资源 | README 配图、文档图、架构图 |
| 文本/代码转架构图 | 模块依赖图、数据流图、类图 |
| 图片格式转换 | PDF/PNG/SVG/WebP 互转 |
| 嵌入 Markdown | 手册正文引用图片 |
| 嵌入 LaTeX PDF | 使用 \includegraphics |

## 1. 从论文 PDF 提取图片

依赖：`pymupdf`

```python
import fitz  # PyMuPDF
from pathlib import Path

pdf_path = Path("_repoguide/paper.pdf")
output_dir = Path("_repoguide/images")
output_dir.mkdir(exist_ok=True)

doc = fitz.open(pdf_path)
extracted = []
for page_num in range(len(doc)):
    page = doc[page_num]
    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list, start=1):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n > 4:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        img_path = output_dir / f"paper_p{page_num+1}_img{img_index}.png"
        pix.save(img_path)
        extracted.append(str(img_path))

doc.close()
print(extracted)
```

提取后按论文章节/图号命名，并记录到 `analysis_paper.json` 的 `extracted_figures` 字段：

```json
{
  "extracted_figures": [
    {"path": "_repoguide/images/paper_p3_img1.png", "page": 3, "caption": "模型架构图"}
  ]
}
```

## 2. 扫描仓库图片资源

```python
from pathlib import Path

REPO_PATH = Path("/path/to/repo").resolve()
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

image_files = []
for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.gif", "*.webp"):
    for f in REPO_PATH.rglob(ext):
        if any(p in f.parts for p in IGNORE_DIRS):
            continue
        image_files.append({
            "path": f.relative_to(REPO_PATH).as_posix(),
            "type": f.suffix.lstrip("."),
            "size": f.stat().st_size,
        })

print(image_files)
```

重点记录：
- `docs/`、`assets/`、`images/`、`figures/` 目录下的图片
- README 中引用的图片
- 仓库自带的架构图、流程图

## 3. 从 Mermaid 文本生成图片

依赖：`mermaid-cli`（`npm install -g @mermaid-js/mermaid-cli`）

```bash
# 将 mermaid 保存为 .mmd 文件
cat > _repoguide/images/arch.mmd << 'EOF'
graph TD
    A[用户输入] --> B[RepoGuide Skill]
    B --> C[Profiler]
    B --> D[Architect]
    B --> E[Code Analyst]
EOF

# 生成 PNG
npx -y @mermaid-js/mermaid-cli mmdc -i _repoguide/images/arch.mmd \
  -o _repoguide/images/arch.png -b transparent

# 或生成 SVG
npx -y @mermaid-js/mermaid-cli mmdc -i _repoguide/images/arch.mmd \
  -o _repoguide/images/arch.svg -b transparent
```

如果 `mermaid-cli` 不可用，保留 mermaid 文本代码块，不强行生成图片。

## 4. 用 Python 生成自定义架构图

依赖：`graphviz`（需系统安装 graphviz）

```python
from graphviz import Digraph

dot = Digraph(comment='Architecture', format='png')
dot.attr(rankdir='LR')
dot.node('A', 'Input')
dot.node('B', 'Profiler')
dot.node('C', 'Analyzer')
dot.edges(['AB', 'BC'])
dot.render('_repoguide/images/arch_graphviz', view=False)
```

或用 matplotlib 绘制简单流程：

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(8, 4))
boxes = [(0.1, 0.4, 'Input'), (0.4, 0.4, 'Process'), (0.7, 0.4, 'Output')]
for x, y, label in boxes:
    ax.add_patch(mpatches.FancyBboxPatch((x, y), 0.15, 0.1, boxstyle="round,pad=0.02"))
    ax.text(x+0.075, y+0.05, label, ha='center', va='center')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
plt.savefig('_repoguide/images/flow_matplotlib.png', bbox_inches='tight')
```

## 5. 图片格式转换

依赖：`Pillow`

```python
from PIL import Image
from pathlib import Path

input_path = Path("_repoguide/images/input.webp")
output_path = Path("_repoguide/images/output.png")

img = Image.open(input_path)
if img.mode in ("RGBA", "P"):
    img = img.convert("RGB")
img.save(output_path)
```

LaTeX 推荐图片格式优先级：
1. PDF（矢量图最佳）
2. PNG（位图）
3. JPG（照片）
4. SVG（需额外包支持，优先转 PDF/PNG）

## 6. 嵌入 Markdown 手册

相对路径引用（以 `_repoguide/manual.md` 为基准）：

```markdown
### 系统架构

![系统架构图](images/arch.png)

> 图 1：模块依赖关系
```

图片统一放在 `_repoguide/images/`。

## 7. 嵌入 LaTeX PDF

在生成 `_repoguide/manual-body.tex` 时，把 Markdown 图片语法转换为：

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{images/arch.png}
  \caption{系统架构图}
  \label{fig:arch}
\end{figure}
```

渲染前确保图片已复制到 `_repoguide/images/`。

## 8. 自动生成图片任务

在 analyze-repo.md 的 Agent Team 中增加可选 agent：

```
agent: image-handler

输入: $REPO_PATH/_repoguide/profile.json + analysis_arch.json + paper.pdf(可选)
输出: $REPO_PATH/_repoguide/images/ + image-manifest.json

任务:
1. 如果存在论文 PDF，提取论文图片
2. 扫描仓库图片资源
3. 将 analysis_arch.json 中的 mermaid 图渲染为 PNG/SVG
4. 为核心数据流生成补充示意图
5. 输出 image-manifest.json

image-manifest.json:
{
  "paper_figures": [...],
  "repo_figures": [...],
  "generated_diagrams": [...],
  "limitations": []
}
```

## 9. 错误处理

| 错误 | 处理 |
|------|------|
| PDF 无图片 | 返回空列表 |
| mermaid-cli 未安装 | 保留 mermaid 文本，记录 limitation |
| graphviz 未安装 | 使用 matplotlib 或跳过 |
| 图片格式无法识别 | 跳过并记录 |

## 输出

- `_repoguide/images/` 目录
- `_repoguide/image-manifest.json`
- 手册中通过相对路径引用图片
- PDF 中通过 \includegraphics 嵌入图片
