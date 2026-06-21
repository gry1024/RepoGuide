---
name: repoguide-tool-pdf-reader
description: RepoGuide 的 PDF 解析工具方法，支持论文 PDF 文本/表格/图片提取。
---

# RepoGuide · PDF Reader

## 依赖

```bash
pip install pymupdf pdfplumber
```

## 快速读取

```python
import fitz  # PyMuPDF

def read_pdf(pdf_path, pages=None):
    doc = fitz.open(pdf_path)
    result = {"total_pages": len(doc), "text": {}}
    page_range = pages if pages is not None else range(len(doc))
    for i in page_range:
        if 0 <= i < len(doc):
            result["text"][i + 1] = doc[i].get_text()
    doc.close()
    return result
```

## 表格提取

```python
import pdfplumber

def extract_tables(pdf_path, pages=None):
    result = {}
    with pdfplumber.open(pdf_path) as pdf:
        page_range = pages if pages is not None else range(len(pdf.pages))
        for i in page_range:
            if 0 <= i < len(pdf.pages):
                tables = pdf.pages[i].extract_tables()
                if tables:
                    result[i + 1] = tables
    return result
```

## 使用场景

- 论文 PDF：提取标题、作者、摘要、章节、公式、算法、术语。
- 仓库内 PDF：作为论文来源检测后的输入。

## 注意事项

- 扫描版 PDF 需先 OCR，无法直接提取文本时标注到 limitation_notes。
- 大文件分页读取，避免内存溢出。
