---
name: repoguide-tool-paper-fetcher
description: RepoGuide 的论文获取工具，支持 arXiv 链接解析与 PDF 下载。
---

# RepoGuide · 论文获取

## 输入类型

| 输入 | 处理方式 |
|------|----------|
| arXiv URL (`https://arxiv.org/abs/xxxx.xxxxx`) | 下载 PDF 到 `_repoguide/paper.pdf` |
| arXiv PDF URL (`https://arxiv.org/pdf/xxxx.xxxxx`) | 直接下载 |
| 本地 PDF 路径 | 复制到 `_repoguide/paper.pdf` |
| 本地 .tex 路径 | 直接使用 |

## arXiv 下载

```bash
# 从 abs 页面提取 PDF 链接后下载
ARXIV_ID="xxxx.xxxxx"
PDF_URL="https://arxiv.org/pdf/${ARXIV_ID}.pdf"
curl -L -o _repoguide/paper.pdf "$PDF_URL"
```

或用 Python：

```python
import urllib.request
import re

def fetch_arxiv(url: str, output: str = "_repoguide/paper.pdf"):
    arxiv_id = re.search(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+|[^/]+)", url).group(1)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    urllib.request.urlretrieve(pdf_url, output)
    return output
```

## 输出

- 论文 PDF 保存到 `_repoguide/paper.pdf`
- 在 `profile.json` 中设置 `paper_found: true`, `paper_path: _repoguide/paper.pdf`
