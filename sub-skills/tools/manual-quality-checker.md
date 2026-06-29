---
name: repoguide-tool-manual-quality-checker
description: RepoGuide 手册质量验收工具：检查全中文约束、目录树注释率与基础产物完整性，全部以代码片段写在 md 中由 agent 执行。
---

# RepoGuide · 手册质量验收

## 使用场景

Phase 4 写入 `$WORK_DIR/manual.md` 后执行本工具。它不替代 writer 的判断，只负责把容易遗漏的硬约束变成可重复检查：

- 面向读者的正文不得出现英文整句。
- 代码块、命令、路径、公式与专有名词允许保留原文。
- 注释化目录树中大多数非空行必须含 ` # ` 中文用途注释。

## 英文整句扫描

```python
import re


ENGLISH_SENTENCE_RE = re.compile(
    r"\b[A-Za-z][A-Za-z0-9'/-]*"
    r"(?:\s+[A-Za-z][A-Za-z0-9'/-]*){3,}"
    r"[.!?]?"
)


def _strip_inline_exemptions(line: str) -> str:
    """移除代码、链接、图片等允许保留英文的片段。"""
    line = re.sub(r"`[^`]*`", " ", line)
    line = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", line)
    line = re.sub(r"\[[^\]]*\]\([^)]+\)", " ", line)
    line = re.sub(r"https?://\S+", " ", line)
    return line


def find_english_sentence_violations(markdown: str):
    """
    返回正文中的英文整句疑似违规项。
    每项包含 line、text，供 writer 改写为中文后重新检查。
    """
    violations = []
    in_fence = False

    for line_no, raw in enumerate(markdown.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if stripped.startswith("$$"):
            continue

        checked = _strip_inline_exemptions(raw)
        for match in ENGLISH_SENTENCE_RE.finditer(checked):
            text = match.group(0).strip()
            if text:
                violations.append({"line": line_no, "text": text})

    return violations
```

## 面向读者的内部说明泄漏扫描

最终手册是给读者看的，不得把 writer/schema/排版策略说明直接写进正文。

```python
READER_FACING_META_PHRASES = [
    "卡片式",
    "每个核心文件一张卡片",
    "每个核心文件一张\"卡片\"",
    "标题带一句话职责",
    "类清单（行内）",
    "函数签名+职责+参数+关键逻辑",
    "key_logic",
]


def find_reader_facing_meta_violations(markdown: str):
    violations = []
    in_fence = False

    for line_no, raw in enumerate(markdown.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for phrase in READER_FACING_META_PHRASES:
            if phrase in raw:
                violations.append({"line": line_no, "text": phrase})

    return violations
```

## 注释化目录树检查

```python
def annotated_tree_comment_ratio(tree_text: str) -> float:
    lines = [line for line in tree_text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    annotated = [line for line in lines if " # " in line]
    return len(annotated) / len(lines)
```

## Phase 4 验收用法

```python
from pathlib import Path


manual_path = Path("$WORK_DIR/manual.md")
manual = manual_path.read_text(encoding="utf-8")
violations = find_english_sentence_violations(manual)
if violations:
    raise SystemExit(
        "手册存在英文整句，请改写为中文后重试: "
        + "; ".join(f"line {v['line']}: {v['text']}" for v in violations[:20])
    )
meta_violations = find_reader_facing_meta_violations(manual)
if meta_violations:
    raise SystemExit(
        "手册泄漏了面向 writer 的内部说明，请删除或改写: "
        + "; ".join(f"line {v['line']}: {v['text']}" for v in meta_violations[:20])
    )
```

## 处理建议

- 英文章节标题改写为中文，并在括号中保留必要专有名词。
- 英文图题改写为中文，如 `Figure 1` 写成 `图 1`。
- 论文标题、代码标识符、命令、路径、公式不强制翻译。
