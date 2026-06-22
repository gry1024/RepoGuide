---
name: repoguide-task-phase-2-5
description: RepoGuide Phase 2.5：图片处理。创建 image-handler agent，提取论文图片、扫描仓库图片、渲染 mermaid 图为 PNG/SVG。
---

# Phase 2.5: 图片处理

## 执行方式

创建 **image-handler** agent 执行本 Phase。

引用 `sub-skills/tools/image-handler.md`。

```
输入: $WORK_DIR/profile.json + analysis_arch.json + paper.pdf(可选)
输出: $WORK_DIR/images/ + image-manifest.json
```

## 任务

1. 如果存在论文 PDF，提取论文图片。
2. 扫描仓库图片资源。
3. 将 `analysis_arch.json` 中的 mermaid 图渲染为 PNG/SVG。
4. 为核心数据流生成补充示意图。
5. 输出 `image-manifest.json`。

## 输出 JSON

```json
{
  "paper_figures": [
    {"path": "...", "page": 3, "caption": "..."}
  ],
  "repo_figures": [
    {"path": "...", "type": "png", "size": 1234}
  ],
  "generated_diagrams": [
    {"path": "...", "source": "mermaid", "caption": "..."}
  ],
  "limitations": []
}
```

## 触发条件

- 当 `profile.json.paper_found == true` 或 `analysis_arch.json` 包含 mermaid 图时执行。
- 无图片资源且无图可渲染时，可跳过并生成空 manifest。

## 输出校验

使用 `_index.md` 中的 `validate_json` 校验 `$WORK_DIR/image-manifest.json`：

```python
validate_json(
    "$WORK_DIR/image-manifest.json",
    required_fields=["paper_figures", "repo_figures", "generated_diagrams", "limitations"],
)
```

若 manifest 为空（无图片可处理），允许四个字段均为空列表。

## 下一 Phase

完成后进入 [phase-3-paper.md](phase-3-paper.md)（如 paper_found 为 true），否则进入 [phase-4-writer.md](phase-4-writer.md)。
