---
name: repoguide-task-phase-5
description: RepoGuide Phase 5：PDF 渲染。创建 renderer agent，使用 xelatex 渲染 PDF，不可用时降级为 HTML。
---

# Phase 5: PDF 渲染

## 执行方式

创建 **renderer** agent 执行本 Phase。

引用 `sub-skills/tools/latex-renderer.md`。

```
输入: $WORK_DIR/manual.md
输出: $WORK_DIR/<repo_name>-manual.pdf (优先)
       $WORK_DIR/<repo_name>-manual.html (xelatex 不可用时降级)
```

## 任务

1. 按 `sub-skills/tools/latex-renderer.md` 中的代码片段，使用 xelatex 渲染 PDF。
2. 如果 xelatex 不可用，保留 Markdown 并降级渲染为 HTML，记录降级信息。

## 输出

- `$WORK_DIR/<repo_name>-manual.pdf`（xelatex 可用时）
- `$WORK_DIR/<repo_name>-manual.html`（xelatex 不可用时）

## 输出校验

使用 `_index.md` 中的 `validate_file_exists` 校验产物：

```python
# PDF 优先
ok_pdf, _ = validate_file_exists("$WORK_DIR/<repo_name>-manual.pdf", min_bytes=1024)
# 或 HTML 降级
ok_html, _ = validate_file_exists("$WORK_DIR/<repo_name>-manual.html", min_bytes=1024)
# Markdown 始终保留
ok_md, _ = validate_file_exists("$WORK_DIR/manual.md", min_bytes=100)

assert ok_pdf or ok_html or ok_md, "至少保留一种产物"
```

## 下一 Phase

完成后进入 [phase-6-output.md](phase-6-output.md)。
