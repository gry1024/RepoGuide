---
name: repoguide-task-phase-2-5
description: RepoGuide Phase 2.5：图片处理。按区域裁剪论文图、graphviz 渲染架构总览图、扫描仓库图片、生成 image-manifest.json。
---

# Phase 2.5: 图片处理

## 执行方式

创建 **image-handler** agent 执行本 Phase。

引用 `sub-skills/tools/image-handler.md`。

```
输入: $WORK_DIR/profile.json + analysis_arch.json + paper.pdf(可选)
输出: $WORK_DIR/images/ + image-manifest.json
```

## 任务（按顺序执行 image-handler.md 中的代码片段）

1. **按区域裁剪论文图**（`REPOGUIDE_PAPER_FIGURE_EXTRACT_START` 段）：仅当 `paper.pdf` 存在。用 `get_image_info` 的 bbox 作 clip 渲染，过滤 < 80×80 的碎片，合并相近 bbox。
2. **渲染架构总览图**（`REPOGUIDE_GRAPHVIZ_RENDER_START` 段）：从 `analysis_arch.json.architecture_overview_dot` 读取 DOT，调用系统 `dot` 生成 `images/architecture_overview.png`。
3. **扫描仓库图片**（第 2 节代码）：扫描仓库内 `img/`、`docs/` 等目录的图片资源，复制关键图到 `images/repo_*.png`。
4. **图片优化**（`REPOGUIDE_IMAGE_OPTIMIZE_START` 段）：用 Pillow 限制最大宽 1800 / 高 2200，控制 PDF 体积。
5. **manifest 对账**（`REPOGUIDE_IMAGE_MANIFEST_RECONCILE_START` 段）：扫描 `images/` 目录，分类到 `paper_figures` / `repo_figures` / `generated_diagrams`，输出 `image-manifest.json`。

## 输出 JSON（image-manifest.json）

```json
{
  "paper_figures": [
    {"path": "images/paper_p5_img1.png", "page": 5, "caption": "论文第 5 页图 1", "size": 12345}
  ],
  "repo_figures": [
    {"path": "images/repo_001.png", "type": "png", "size": 1234}
  ],
  "generated_diagrams": [
    {"path": "images/architecture_overview.png", "source": "graphviz", "caption": "架构总览图"}
  ],
  "limitations": []
}
```

## 触发条件

- 当 `profile.json.paper_found == true` 或 `analysis_arch.json` 含 `architecture_overview_dot` 时执行。
- 无图片资源且无图可渲染时，生成空 manifest（四字段均为空列表）。

## 输出校验

```python
validate_json(
    "$WORK_DIR/image-manifest.json",
    required_fields=["paper_figures", "repo_figures", "generated_diagrams", "limitations"],
)
```

## 下一 Phase

完成后进入 [phase-3-paper.md](phase-3-paper.md)（如 paper_found 为 true），否则进入 [phase-4-writer.md](phase-4-writer.md)。
