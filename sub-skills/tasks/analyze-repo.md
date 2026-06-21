---
name: repoguide-task-analyze-repo
description: RepoGuide 核心任务：分析代码仓库并生成 PDF 仓库手册指南。用户只需提供仓库地址和可选论文链接，Agent Team 自动完成全流程。
---

# RepoGuide · 仓库分析任务

## 触发条件

用户输入包含以下任一形式：

```
分析 https://github.com/owner/repo
快速分析 https://github.com/owner/repo
深度分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
分析这个仓库
分析 /path/to/repo
分析 <GitHub URL>，论文 https://arxiv.org/abs/xxxx.xxxxx
```

## 输入解析

1. 提取 GitHub URL（匹配 `https?://github\.[\w.-]+/[\w.-]+`）。
2. 提取 arXiv 链接（匹配 `https?://arxiv\.(?:org|pdf)/[\d.]+` 或本地 PDF/.tex 路径）。
3. 识别细致度：
   - 输入含"快速" → `fast`
   - 输入含"深度" → `deep`
   - 否则默认 → `standard`
4. 如果没有 URL 但有本地路径，使用本地路径。
5. 如果都没有，使用当前工作目录（必须是 git 仓库根）。
6. 如果无法确定 → 终止并报错，不追问。

### 细致度 3 档

| 档位 | 仓库分析 | 论文分析 | 是否询问 |
|------|----------|----------|----------|
| **fast** | 仅 README、顶层结构、入口文件 | 仅摘要与核心贡献 | 是 |
| **standard** | 核心模块、架构图、关键文件 | 主要章节、公式、算法、术语 | 是（默认） |
| **deep** | 全量核心代码、依赖链、完整目录树 | 逐章映射、实验-脚本对应、提取论文原图 | 是 |

执行前主 agent 向用户确认一次：

```
检测到仓库 <repo> 与论文 <arxiv>。
请选择分析细致度：
1) 快速 - 仅概览
2) 标准 - 核心模块 + 论文主要章节（默认）
3) 深度 - 全量代码 + 论文逐章映射
```

用户明确指定或回复档位后写入 `$WORK_DIR/profile.json` 的 `"depth": "fast|standard|deep"`。

## 工作目录

所有中间产物统一写入用户当前工作目录下的 `_repoguide/`，不写入被分析仓库内部：

```
<cwd>/_repoguide/
├── repo/                    (GitHub URL 克隆到此，本地路径时不存在)
├── profile.json
├── analysis_arch.json
├── analysis_code.json
├── analysis_paper.json      (可选)
├── analysis_map.json        (可选)
├── image-manifest.json      (可选)
├── images/                  (可选)
├── paper.pdf                (可选)
├── manual.md
├── <repo_name>-manual.pdf     (如 xelatex 可用)
└── <repo_name>-manual.html    (xelatex 不可用时降级)
```

最终手册复制到用户当前工作目录（假设仓库名为 `<repo_name>`）：

```
<cwd>/<repo_name>-manual.md
<cwd>/<repo_name>-manual.pdf   (如 xelatex 可用)
<cwd>/<repo_name>-manual.html (xelatex 不可用时降级)
```

## Phase 0: 输入归一化

主 agent 串行执行：

1. 检测 RUNTIME（引用 `sub-skills/runtime/_detect.md`）。
2. 解析用户输入，确定仓库引用和论文引用。
3. 确定工作目录：`$WORK_DIR = <cwd>/_repoguide/`，并创建该目录。
4. 调用 `sub-skills/tools/repo-normalizer.md` 归一化仓库路径 → `$REPO_PATH`。
   - 本地路径 / 当前目录：直接使用，不克隆。
   - GitHub URL：默认浅克隆到 `$WORK_DIR/repo/`。
   - 远程模式：使用 GitHub API 读取，写入 `$WORK_DIR/repo/` 和 `$WORK_DIR/github-tree.json`。
5. 如果用户提供了 arXiv 链接，调用 `sub-skills/tools/paper-fetcher.md` 下载论文 → `$WORK_DIR/paper.pdf`。

## Phase 1: 仓库画像

创建 **profiler** agent 执行：

```
输入: $REPO_PATH
输出: $WORK_DIR/profile.json

任务:
1. 按 sub-skills/tools/detect-stack.md 中的 Python 代码执行，生成基础画像
2. 扫描 README、LICENSE、顶层目录结构
3. 如果仓库内有 PDF/.tex 或 README 含 arxiv 链接，设置 paper_found=true
4. 将完整画像写入 profile.json

profile.json 必须包含:
{
  "repo_path": "...",
  "work_dir": "...",
  "repo_name": "...",
  "primary_language": "...",
  "all_languages": [...],
  "package_managers": [...],
  "entry_points": [...],
  "paper_found": bool,
  "paper_path": "..." | null,
  "depth": "fast|standard|deep",
  "file_count_total": int,
  "file_count_by_ext": {...},
  "module_candidates": [...],
  "core_files_seed": [...]
}
```

## Phase 2: 并行深度分析

引用 `sub-skills/runtime/create-agent.md` 并行创建以下 agents：

### agent: architect

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_arch.json

任务:
1. 读取 profile.json（注意 `depth` 字段）
2. 从 entry_points 出发，沿 import/include 反向追溯模块依赖
3. 生成 mermaid 模块依赖图（graph TD 或 graph LR）
4. 跟踪主要函数调用链，生成 mermaid 数据流图
5. 列出关键状态点
6. 推断 3-5 个关键设计决策
7. 若 `depth == deep`，额外输出完整目录树 `directory_tree`（见下方格式）

按 `depth` 调整范围：
- fast: 只分析顶层模块与入口关系，mermaid 图不超过 8 个节点
- standard: 分析核心模块依赖与主要调用链
- deep: 完整模块依赖、数据流、目录树、所有关键状态点

输出 JSON:
{
  "module_dependency_graph": "mermaid string",
  "data_flow_graph": "mermaid string",
  "key_state_points": [{"name": "...", "description": "...", "file": "...", "line": int}],
  "design_decisions": [{"decision": "...", "evidence": "file:line", "reasoning": "..."}],
  "directory_tree": "字符串形式的目录树，仅在 depth==deep 时必填",
  "limitation_notes": []
}
```

### agent: code-analyst

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_code.json

任务:
1. 读取 profile.json（注意 `depth` 字段）与 core_files_seed
2. 按 references/depth-rules.md 和 `depth` 判定核心文件与周边文件：
   - fast: 只读取 entry_points + README 中提到的文件
   - standard: 读取核心模块文件
   - deep: 读取所有核心文件 + 测试/配置/脚本
3. 对每个核心文件完整 Read，提取：
   - 一句话作用
   - 类/函数/方法清单（签名 + 行号 + 作用）
   - 关键逻辑（3-10 行/函数）
   - 依赖关系
4. 对周边文件生成简略清单
5. 若 `depth == deep`，生成带注释的完整目录树 `directory_tree`

输出 JSON:
{
  "core_files": [
    {
      "path": "...",
      "one_liner": "...",
      "classes": [{"name": "...", "line": int, "signature": "...", "purpose": "..."}],
      "functions": [{"name": "...", "line": int, "signature": "...", "key_logic": "..."}],
      "dependencies": ["..."]
    }
  ],
  "peripheral_files": [{"path": "...", "importance": "high|medium|low", "one_liner": "..."}],
  "config_files": [{"path": "...", "purpose": "..."}],
  "scripts": [{"path": "...", "purpose": "..."}],
  "resources": [{"path": "...", "purpose": "..."}],
  "test_strategy": "一句话概括",
  "directory_tree": "字符串形式的目录树，仅在 depth==deep 时必填",
  "limitation_notes": []
}
```

## Phase 2.5: 图片处理（可选）

创建 **image-handler** agent 执行：

引用 `sub-skills/tools/image-handler.md`。

```
输入: $WORK_DIR/profile.json + analysis_arch.json + paper.pdf(可选)
输出: $WORK_DIR/images/ + image-manifest.json

任务:
1. 如果存在论文 PDF，提取论文图片
2. 扫描仓库图片资源
3. 将 analysis_arch.json 中的 mermaid 图渲染为 PNG/SVG
4. 为核心数据流生成补充示意图
5. 输出 image-manifest.json

image-manifest.json:
{
  "paper_figures": [{"path": "...", "page": 3, "caption": "..."}],
  "repo_figures": [{"path": "...", "type": "png", "size": 1234}],
  "generated_diagrams": [{"path": "...", "source": "mermaid", "caption": "..."}],
  "limitations": []
}
```

## Phase 3: 论文解析与映射（可选）

仅当 `profile.json.paper_found == true` 时执行。

### agent: paper-analyst

引用 `sub-skills/tools/pdf-reader.md`。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_paper.json

任务:
1. 读取 paper_path（PDF 或 .tex）
2. 提取标题、作者、摘要、核心贡献
3. 提取章节结构（最多 5 级）
4. 提取关键公式（LaTeX）和算法伪代码
5. 提取关键术语表

输出 JSON:
{
  "title": "...",
  "authors": [...],
  "abstract": "...",
  "core_contributions": [...],
  "section_tree": [{"level": int, "title": "..."}],
  "key_formulas": [{"latex": "...", "meaning": "..."}],
  "key_algorithms": [{"name": "...", "pseudocode": "..."}],
  "glossary": [{"term": "...", "description": "..."}],
  "limitation_notes": []
}
```

### agent: paper-code-mapper

```
输入: $WORK_DIR/analysis_paper.json + analysis_code.json
输出: $WORK_DIR/analysis_map.json

任务:
1. 读取论文解析结果和代码分析结果
2. 生成三层映射：
   - 层级 1: 论文章节 ↔ 代码模块
   - 层级 2: 论文公式/算法 ↔ 代码函数/类
   - 层级 3: 论文实验/表格 ↔ 评估脚本
3. 标注置信度

输出 JSON:
{
  "layer1_section_to_module": [{"section": "...", "module": "...", "confidence": "high|medium|low"}],
  "layer2_formula_to_function": [{"formula": "...", "function": "...", "file": "...", "line": int, "confidence": "..."}],
  "layer3_experiment_to_script": [{"experiment": "...", "script": "...", "file": "..."}],
  "glossary_mapping": [{"term": "...", "code_identifier": "..."}],
  "limitation_notes": []
}
```

## Phase 4: 手册组装

创建 **writer** agent 执行：

```
输入: $WORK_DIR/profile.json + analysis_*.json + image-manifest.json(可选)
输出: $WORK_DIR/manual.md

任务:
1. 读取所有分析产物
2. 如果存在 image-manifest.json，在第 3 层和第 5 层插入图片
3. 参考 references/manual-template.md 的五层结构
4. 主 agent 自己综合第 1 层（一句话总括 + 3 条命令 + 5 个关键文件）
5. 组装完整 Markdown 仓库手册指南
6. 写入 $WORK_DIR/manual.md
```

手册结构：

1. 第 0 层：元信息
2. 第 1 层：一句话总括 + 快速上手
3. 第 2 层：技术栈与依赖
4. 第 3 层：架构与数据流（含模块依赖图、数据流图、仓库/论文配图）
5. 第 4 层：核心代码详解
6. 第 5 层：论文-代码映射（可选，含论文原图）
7. 附录：文件清单、已知限制、生成信息

## Phase 5: PDF 渲染

创建 **renderer** agent 执行：

```
输入: $WORK_DIR/manual.md
输出: $WORK_DIR/<repo_name>-manual.pdf (优先)
       $WORK_DIR/<repo_name>-manual.html (xelatex 不可用时降级)
```
任务:
1. 按 sub-skills/tools/latex-renderer.md 中的代码片段，使用 xelatex 渲染 PDF
2. 如果 xelatex 不可用，保留 Markdown 并降级渲染为 HTML，记录降级信息
```

引用 `sub-skills/tools/latex-renderer.md`。

## Phase 6: 输出到用户工作目录

主 agent 串行执行：

1. 将 `$WORK_DIR/manual.md` 复制到 `<cwd>/<repo_name>-manual.md`。
2. 如果 PDF 生成成功，复制到 `<cwd>/<repo_name>-manual.pdf`。
3. 如果 PDF 未生成但 HTML 已生成，复制到 `<cwd>/<repo_name>-manual.html`。
4. 输出摘要。

## 进度反馈

- `📋 Phase 0/6: 输入归一化...`
- `🤖 创建 profiler agent...`
- `🤖 并行创建 architect / code-analyst...`
- `🤖 创建 image-handler...` (可选)
- `🤖 创建 paper-analyst / paper-code-mapper...` (可选)
- `🤖 创建 writer agent...`
- `🤖 创建 renderer agent...`
- `✅ Done in <duration>`

## 错误处理

| 错误 | 处理 |
|------|------|
| 仓库 URL 失效 / 为空 | 立即终止，无手册 |
| 单文件分析失败 | 跳过，写入 limitation_notes |
| 论文 PDF 损坏 / 无法解析 | 跳过第 5 层 |
| xelatex 不可用 | 保留 Markdown 并降级渲染 HTML，提示用户 |
| Agent 工具不可用 | 主 agent 串行执行各 phase |

## 输出模板

```
✅ RepoGuide 仓库手册生成完成

📊 统计:
- 仓库: <repo_name>
- 主语言: <primary_language>
- 文件总数: <file_count_total>
- 论文: <found|not found>
- 执行模式: <claude-team|kimi-team|codex-subagent|serial>
- 总耗时: <duration>

📄 产物文件:
- Markdown: <absolute path>/<repo_name>-manual.md
- PDF: <absolute path>/<repo_name>-manual.pdf (如 xelatex 可用)
- HTML: <absolute path>/<repo_name>-manual.html (xelatex 不可用时降级生成)

🎯 一句话总结: <从第 1 层提取>
```
