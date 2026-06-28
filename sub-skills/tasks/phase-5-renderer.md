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
2. 渲染器必须使用 RepoGuide 自带 Markdown→LaTeX 转换逻辑，**不得把 pandoc 作为主转换器**。
3. 如果 xelatex 不可用，保留 Markdown 并降级渲染为 HTML，记录降级信息。
4. PDF 生成后必须做渲染抽检：用 `pdftoppm` 或 PyMuPDF 渲染封面、目录页、首个正文页和至少一个含图/表页面；目录页不得为空，图表不得裁切，正文不得出现乱码。

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

### PDF 视觉验收

```python
from pathlib import Path

pdf_path = Path("$WORK_DIR/<repo_name>-manual.pdf")
if pdf_path.exists():
    import fitz  # PyMuPDF；若不可用，可改用 pdftoppm 渲染抽检页

    doc = fitz.open(pdf_path)
    assert len(doc) >= 3, "PDF 页数过少，疑似渲染失败"
    sample_pages = sorted({0, 1, 2, min(len(doc) - 1, 8)})
    for page_no in sample_pages:
        text = doc[page_no].get_text().strip()
        assert text, f"第 {page_no + 1} 页为空，目录页不得为空"
        pix = doc[page_no].get_pixmap(matrix=fitz.Matrix(1.0, 1.0), alpha=False)
        assert pix.width > 100 and pix.height > 100, f"第 {page_no + 1} 页渲染尺寸异常"
    doc.close()
```

## 下一 Phase

完成后进入 [phase-6-output.md](phase-6-output.md)。
