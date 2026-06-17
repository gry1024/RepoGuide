---
name: RepoGuide
description: |
  端到端分析任意代码仓库（本地路径或 GitHub URL），自动产出含架构、数据流、
  核心代码详解、论文-代码映射（条件性）的自顶向下五层结构 Markdown + PDF 报告。
  使用方式：用户说"使用 RepoGuide skill 帮我分析仓库结构"或"使用 RepoGuide skill 分析 <GitHub URL>"，
  触发后端到端完成，不向用户追问。
version: 0.1.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# RepoGuide · 代码仓库分析 Skill

## 触发条件

用户输入满足以下任一形式时自动触发本 skill：

1. **本地路径**: "使用 RepoGuide skill 帮我分析 /path/to/repo"
2. **GitHub URL**: "使用 RepoGuide skill 分析 https://github.com/owner/repo"
3. **隐式当前目录**: 在某个 git 仓库根目录下说 "使用 RepoGuide skill 帮我分析仓库结构"

## 输入解析

按以下优先级从用户输入中提取仓库引用：

1. 显式给出的本地路径（绝对或相对）
2. 显式给出的 GitHub URL（匹配 `https?://github\.com/[\w.-]+/[\w.-]+`）
3. 当前工作目录（必须是 git 仓库根）

如果无法确定 → 终止并输出明确错误信息（不要追问）。

## Phase 0: 输入归一化

**本 Phase 串行执行，由主 agent 完成。**

- 本地路径: 验证 `ls` 存在 → 直接使用
- GitHub URL: 调用 `bash scripts/clone-if-url.sh <url> /tmp/repoguide-<hash>`（hash 取 url 末段的 md5 前 8 位）
- 当前目录: 检测 `.git/` 存在 → 直接使用

输出归一化结果：`$REPO_PATH` （绝对路径）。

## Phase 1: 探查 (主 agent 串行)

**目的**: 产出仓库画像，喂给 Phase 2 的 subagent。

执行步骤（每步都要真实读取，禁止猜测）：

1. **目录树扫描**: 用 `Bash` 跑 `find $REPO_PATH -maxdepth 4 -type d | head -100` + 过滤掉 `.git/`, `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`
2. **技术栈识别**: 调用 `python scripts/detect-stack.py $REPO_PATH`，读取 stdout JSON
3. **论文检测**: `glob $REPO_PATH/{*.pdf,*.tex,paper*,paper*,README*}` + 扫 README 中 arxiv 链接
4. **入口识别**: 根据 detect-stack 输出的 `primary_language` 调用对应入口识别（见 `references/language-profiles.md`）
5. **写仓库画像**: 用 `Write` 工具写到 `$REPO_PATH/_repoguide/profile.json`，内容包含：
   ```json
   {
     "repo_path": "...",
     "repo_name": "...",
     "primary_language": "python|js|ts|java|go|rust",
     "all_languages": ["..."],
     "package_managers": ["..."],
     "entry_points": ["path/to/main.py", ...],
     "paper_found": true|false,
     "paper_path": "..." | null,
     "file_count_total": int,
     "file_count_by_ext": {"py": int, ...},
     "module_candidates": ["path/to/module_a", ...],
     "core_files_seed": ["path/to/core_a", ...]
   }
   ```

## Phase 2: 并行深度分析 (派 4 个 subagent)

**关键约束**: 4 个 subagent 互不依赖，必须**并行派发**（同一个消息里调用 4 次 Agent 工具）。

**Subagent 派发模板**（每个 subagent 都用 `subagent_type=general-purpose`）：

### Subagent A · 架构与数据流

prompt:
```
你是 RepoGuide skill 的架构与数据流分析 subagent。
你的输入: $REPO_PATH 下的 _repoguide/profile.json (请先 Read 读取)
你的输出: 写到 $REPO_PATH/_repoguide/analysis_a.json

你的任务:
1. Read profile.json
2. 从 entry_points 出发，沿 import/include 反向追溯模块依赖，生成 mermaid 模块依赖图
3. 从第一个 entry_point 出发，跟踪主要函数调用链（最多 3 层深度），生成 mermaid 数据流图（标注数据形态）
4. 列出关键状态点（数据被持久化/转换/分支的位置）
5. 推断 3-5 个关键设计决策（基于代码事实，不要编造）

输出 JSON 结构:
{
  "module_dependency_graph": "mermaid string",
  "data_flow_graph": "mermaid string",
  "key_state_points": ["...", ...],
  "design_decisions": [{"decision": "...", "evidence": "file:line"}]
}
```

### Subagent B · 核心代码详解

prompt:
```
你是 RepoGuide skill 的核心代码详解 subagent。
你的输入: $REPO_PATH 下的 _repoguide/profile.json
你的输出: 写到 $REPO_PATH/_repoguide/analysis_b.json

你的任务:
1. Read profile.json，读取 core_files_seed 列表
2. 对每个核心文件，Read 整个文件，提取:
   - 一句话作用
   - 类/函数/方法清单 (签名 + 行号 + 一句话作用)
   - 关键逻辑 (3-10 行/函数)
   - 入参出参/副作用
   - 依赖关系 (该文件 import 哪些其他文件)
3. 对其他文件做"重要度"判断: 高/中/低 + 一句话作用
4. 智能分层规则见 references/depth-rules.md

输出 JSON 结构:
{
  "core_files": [
    {
      "path": "...",
      "one_liner": "...",
      "classes": [{"name": "...", "line": int, "signature": "...", "purpose": "..."}],
      "functions": [{"name": "...", "line": int, "signature": "...", "key_logic": "..."}],
      "dependencies": ["other/file.py", ...]
    }
  ],
  "peripheral_files": [{"path": "...", "importance": "high|medium|low", "one_liner": "..."}],
  "config_files": [{"path": "...", "purpose": "..."}],
  "test_strategy": "一句话概括"
}
```

### Subagent C · 论文解析（仅当 paper_found=true 时派发）

prompt:
```
你是 RepoGuide skill 的论文解析 subagent。
你的输入: $REPO_PATH 下的 _repoguide/profile.json
你的输出: 写到 $REPO_PATH/_repoguide/analysis_c.json

你的任务:
1. Read profile.json，读取 paper_path
2. 用 Read 工具读 PDF (Read 支持 PDF 自动转文本，自动分页)。如果是 .tex，Read 整个文件
3. 提取:
   - 标题、作者、核心贡献
   - 章节结构 (最多 5 级)
   - 关键公式 (用 LaTeX 表示)
   - 关键算法伪代码
   - 关键术语 (glossary)

输出 JSON 结构:
{
  "title": "...",
  "authors": ["...", ...],
  "core_contributions": ["...", ...],
  "section_tree": [{"level": int, "title": "...", "line": int}],
  "key_formulas": [{"latex": "...", "meaning": "..."}],
  "key_algorithms": [{"name": "...", "pseudocode": "..."}],
  "glossary": [{"term": "...", "code_identifier": "..."}]
}
```

### Subagent D · 论文-代码映射（仅当 paper_found=true 且 C 完成时派发）

prompt:
```
你是 RepoGuide skill 的论文-代码映射 subagent。
你的输入: $REPO_PATH 下的 _repoguide/analysis_c.json 和 analysis_b.json
你的输出: 写到 $REPO_PATH/_repoguide/analysis_d.json

你的任务:
1. Read analysis_c.json (论文) 和 analysis_b.json (代码)
2. 生成三层映射:
   - 层级 1: 论文章节 ↔ 代码模块
   - 层级 2: 论文公式/算法 ↔ 代码函数/类
   - 层级 3: 论文实验/表格 ↔ 评估脚本

输出 JSON 结构:
{
  "layer1_section_to_module": [{"section": "...", "module": "...", "confidence": "high|medium|low"}],
  "layer2_formula_to_function": [{"formula": "...", "function": "...", "file": "...", "line": int}],
  "layer3_experiment_to_script": [{"experiment": "...", "script": "...", "file": "..."}],
  "limitation_notes": ["可能牵强的地方..."]
}
```

## Phase 3: 汇总与输出 (主 agent 串行)

执行步骤：

1. Read 所有 analysis_*.json
2. 读取 `references/report-template.md` 作为模板骨架
3. 按五层结构组装 Markdown 内容：
   - 第 0 层: 从 profile.json 提取元信息
   - 第 1 层: 主 agent 自己写（一句话总括 + 3 条命令 + 5 个关键文件）—— **这一层必须由主 agent 综合，不要让 subagent 写**
   - 第 2 层: 从 profile.json 提取
   - 第 3 层: 用 analysis_a.json 的 mermaid 图
   - 第 4 层: 用 analysis_b.json
   - 第 5 层: 用 analysis_c.json + analysis_d.json
   - 附录: 收集所有 subagent 报告的 "limitation_notes" 和 "known_issues"
4. 用 `Write` 工具写到 `$REPO_PATH/../repoguide-report.md`（报告保存在**当前用户工作目录**，不是仓库内）
5. 调用 `python scripts/generate-pdf.py repoguide-report.md` 生成 PDF（脚本会自动安装所需 Python 依赖；若安装失败则优雅降级，只保留 Markdown）
6. 在对话中输出报告摘要（每层一句话）+ 两个文件绝对路径

## 进度反馈规则

在 Phase 切换和 Subagent 启动时输出状态行，让用户知道进度：

- Phase 切换: `📋 Phase N/3: <description>...`
- Subagent 启动: `🤖 Subagent X: <description>`
- 完成: `✅ Done in <时长>`

## 错误处理

参见 spec 第 9 节。关键原则：能降级就降级，能跳过就跳过。报告永远尽力产出。

特别注意：
- 仓库路径不存在 / URL 失效 / 仓库为空 → 立即终止，无报告
- 单文件分析失败 → 跳过 + 已知限制附录
- 论文 PDF 损坏 → 第 5 层不出现
- md→pdf 失败 → 仍生成报告，对话中提示

## 内置默认策略

| 决策点 | 默认值 |
|--------|--------|
| 输出格式 | 一次性完整报告 |
| 论文来源 | 优先本地 PDF，否则扫 README/主页论文链接 |
| 报告结构 | 自顶向下五层（第 0-4 永远存在，第 5 条件性） |
| 粒度策略 | 智能分层（5 条规则 + 规模自适应） |
| 涉及语言 | Python/JS/TS/Java/Go/Rust 主支持，其他降级 L3 |
| 论文映射深度 | 中度（三层） |
| 执行架构 | 主 + 并行 subagent |
| 报告保存位置 | `<cwd>/repoguide-report.{md,pdf}` |
| 报告语言 | 与用户交互语言一致（默认中文） |

## 完成后输出模板

```
✅ RepoGuide 分析完成

📊 报告统计:
- 仓库: <repo_name>
- 主语言: <language>
- 文件总数: <int>
- 论文: <found|not found>
- 总耗时: <duration>

📄 产物文件:
- Markdown: <absolute path>
- PDF: <absolute path>

🎯 一句话总结: <从第 1 层提取>
```
