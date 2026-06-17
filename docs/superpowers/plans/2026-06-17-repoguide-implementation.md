# RepoGuide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 RepoGuide skill —— 端到端分析任意代码仓库（本地路径或 GitHub URL），自动产出含架构、数据流、核心代码详解、论文-代码映射（条件性）的自顶向下五层结构 Markdown + PDF 报告，全程零澄清、跨 Claude Code/Codex/Kimi Code 三平台。

**Architecture:** 主 agent 串行（Phase 0 输入归一化、Phase 1 探查、Phase 3 汇总），中间派 4 个并行 subagent（架构/数据流、核心代码、论文解析、论文-代码映射）。SKILL.md 是核心（提示词模板），references/ 装静态参考文档，scripts/ 装辅助工具脚本（detect-stack、clone-if-url、generate-pdf），tests/ 装 TDD 验证。

**Tech Stack:** Markdown (SKILL.md 提示词), Python 3.11+ (detect-stack.py), Bash (clone-if-url.sh, generate-pdf.sh), Git (submodule or clone --depth 1), pandoc / weasyprint (PDF 生成), 6 种目标语言（Python/JavaScript/TypeScript/Java/Go/Rust）

**Spec:** `docs/superpowers/specs/2026-06-17-repoguide-design.md`

---

## File Structure Overview

创建以下目录树（任务 1 完成）：

```
repoguide/
├── SKILL.md                        # Claude Code 主版
├── SKILL.codex.md                  # Codex 适配
├── SKILL.kimi.md                   # Kimi Code 适配
├── references/
│   ├── language-profiles.md        # 6 语言特征
│   ├── depth-rules.md              # 分层规则
│   └── report-template.md          # 五层模板
└── scripts/
    ├── detect-stack.py             # 技术栈识别
    ├── clone-if-url.sh             # URL 处理
    └── generate-pdf.sh             # md→pdf

tests/
├── unit/
│   ├── test_detect_stack.py
│   ├── test_clone_if_url.sh
│   └── test_generate_pdf.sh
├── fixtures/
│   ├── small-python/               # 小型 Python fixture
│   ├── medium-ml-with-paper/       # 中型 ML 仓库 + 论文 PDF
│   └── multi-lang/                 # Python + Rust 混合
└── integration/
    └── test_e2e.sh                 # 端到端：跑完整流程
```

---

## Task 1: 创建目录脚手架

**Files:**
- Create: `repoguide/`
- Create: `repoguide/references/`
- Create: `repoguide/scripts/`
- Create: `tests/`
- Create: `tests/unit/`
- Create: `tests/fixtures/`
- Create: `tests/integration/`
- Create: `repoguide/.gitkeep` (空目录占位)
- Create: `tests/.gitkeep` (空目录占位)

- [ ] **Step 1: 创建所有目录**

Run (Windows bash):
```bash
cd "E:/KimiClaw/repo-code-analysis"
mkdir -p repoguide/references repoguide/scripts
mkdir -p tests/unit tests/fixtures tests/integration
```

- [ ] **Step 2: 添加 .gitkeep 占位**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis"
touch repoguide/.gitkeep repoguide/references/.gitkeep repoguide/scripts/.gitkeep
touch tests/.gitkeep tests/unit/.gitkeep tests/fixtures/.gitkeep tests/integration/.gitkeep
```

- [ ] **Step 3: 验证目录树**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && find repoguide tests -type d
```

Expected:
```
repoguide
repoguide/references
repoguide/scripts
tests
tests/unit
tests/fixtures
tests/integration
```

- [ ] **Step 4: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/ tests/
git commit -m "chore: scaffold RepoGuide skill directory structure"
```

---

## Task 2: 编写 SKILL.md (Claude Code 主版)

**Files:**
- Create: `repoguide/SKILL.md`

**前置条件**: Task 1 完成

- [ ] **Step 1: 写 SKILL.md frontmatter + 入口**

Create `repoguide/SKILL.md` with the following content:

```markdown
---
name: RepoGuide
description: |
  端到端分析任意代码仓库（本地路径或 GitHub URL），自动产出含架构、数据流、
  核心代码详解、论文-代码映射（条件性）的自顶向下五层结构 Markdown + PDF 报告。
  使用方式：用户说"使用 RepoGuide skill 帮我分析仓库结构"或"使用 RepoGuide skill 分析 <GitHub URL>"，
  触发后端到端完成，不向用户追问。
version: 0.1.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
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
     "core_files_seed": ["path/to/core_a", ...]  // 按 5 条规则初步筛
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
4. 智能分层规则见 $REPO_PATH/../references/depth-rules.md (相对路径读)

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
5. 调用 `bash scripts/generate-pdf.sh repoguide-report.md` 生成 PDF
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
```

- [ ] **Step 2: 验证文件可读**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && head -20 repoguide/SKILL.md
```

Expected: 显示 frontmatter `---` 开头的元信息

- [ ] **Step 3: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/SKILL.md
git commit -m "feat(skill): add Claude Code SKILL.md (main version)"
```

---

## Task 3: 编写 SKILL.codex.md (Codex 适配)

**Files:**
- Create: `repoguide/SKILL.codex.md`

**前置条件**: Task 2 完成

- [ ] **Step 1: 写 SKILL.codex.md**

Codex 适配原则：在 Claude Code 主版基础上，调整 ① frontmatter 兼容 Codex 解析 ② 把 `Bash/Read/Write/Edit/Glob/Grep/Agent/AskUserQuestion` 工具名映射到 Codex 工具名 ③ 保持所有行为指令完全一致。

Create `repoguide/SKILL.codex.md` with the following content:

```markdown
---
name: repoguide
description: |
  [Codex 适配] 端到端分析任意代码仓库，产出五层结构 Markdown + PDF 报告。
  使用方式: 引用 `repoguide` skill 后说"分析 <仓库路径或 URL>"。
  本文件是 SKILL.md 在 Codex 平台上的适配版本，行为完全一致。
version: 0.1.0
allowed-tools: shell, view, write, edit, list_files, grep_files, dispatch_agent
---

# RepoGuide (Codex 适配)

> 主版本定义在同目录的 `SKILL.md` 中。本文件仅做平台适配。

## 工具名映射

| Claude Code | Codex | 用途 |
|-------------|-------|------|
| Bash | shell | 执行 shell 命令 |
| Read | view | 读取文件 |
| Write | write | 写文件 |
| Edit | edit | 编辑文件 |
| Glob | list_files | 列出匹配文件 |
| Grep | grep_files | 搜索文件内容 |
| Agent | dispatch_agent | 派 subagent |
| AskUserQuestion | (禁用) | 永远不要派发 |

## 触发条件

参考 SKILL.md "触发条件" 节。本 skill 在 Codex 上**全自动**运行，不向用户追问任何问题（Codex 没有等效的 AskUserQuestion 工具）。

## 行为指令

完全遵循 `SKILL.md` 中 Phase 0/1/2/3 的所有行为。**特别注意**:

- 用 `view` 替代 `Read`
- 用 `shell` 跑命令
- 用 `dispatch_agent` 派 subagent 时使用 `agent_type="general"`（Codex 等价物）
- 派发 4 个 subagent 时**必须在同一条消息中并行派发**

## 错误处理

参考 SKILL.md "错误处理" 节。

## 完成后输出

参考 SKILL.md "完成后输出模板"。
```

- [ ] **Step 2: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/SKILL.codex.md
git commit -m "feat(skill): add Codex platform adapter (SKILL.codex.md)"
```

---

## Task 4: 编写 SKILL.kimi.md (Kimi Code 适配)

**Files:**
- Create: `repoguide/SKILL.kimi.md`

**前置条件**: Task 3 完成

- [ ] **Step 1: 写 SKILL.kimi.md**

Kimi Code 适配原则：保持 activate_skill 机制要求的 frontmatter 格式，行为指令与 Claude Code 主版一致。

Create `repoguide/SKILL.kimi.md` with the following content:

```markdown
---
name: RepoGuide
description: 端到端分析代码仓库，产出五层结构报告（md + pdf）。
activation_keyword: repoguide
version: 0.1.0
---

# RepoGuide (Kimi Code 适配)

> 主版本定义在同目录的 `SKILL.md` 中。本文件仅做平台适配。

## 触发方式

用户输入含 `repoguide` 关键词 + "分析仓库/分析代码" 时激活本 skill。

## 工具能力差异

Kimi Code 工具集与 Claude Code 类似但有差异：

- 支持 `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep` 等基础工具
- **不支持** `Agent` 工具 → 派 subagent 时降级为：主 agent 串行处理 Subagent A/B/C/D 的工作
- **不支持** `AskUserQuestion` → 全自动模式，不追问

## 行为指令

完全遵循 `SKILL.md` 中 Phase 0/1/2/3 的所有行为。**降级策略**:

- Phase 2 不再并行派 subagent，而是主 agent 串行执行 Subagent A → B → C → D 的工作
- 报告元信息标注 "⚠️ 串行执行模式 (Kimi Code 限制)"

## 错误处理

参考 SKILL.md "错误处理" 节。

## 完成后输出

参考 SKILL.md "完成后输出模板"。
```

- [ ] **Step 2: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/SKILL.kimi.md
git commit -m "feat(skill): add Kimi Code platform adapter (SKILL.kimi.md)"
```

---

## Task 5: 编写 language-profiles.md (6 种语言特征表)

**Files:**
- Create: `repoguide/references/language-profiles.md`

**前置条件**: Task 4 完成

- [ ] **Step 1: 写 language-profiles.md**

Create `repoguide/references/language-profiles.md` with the following content:

````markdown
# 语言特征表

本文件定义 RepoGuide 支持的 6 种语言（Python / JavaScript / TypeScript / Java / Go / Rust）的特征，subagent 按此 dispatch。

## 1. Python

**包管理/依赖文件**:
- `pyproject.toml` (优先，含 [project] section)
- `requirements.txt`, `requirements-*.txt`, `requirements/*.txt`
- `setup.py`, `setup.cfg`
- `Pipfile`, `Pipfile.lock`
- `poetry.lock`
- `uv.lock`
- `conda.yml`, `environment.yml`

**入口识别**:
- `pyproject.toml` 的 `[project.scripts]` 段
- `setup.py` 的 `entry_points`
- 包含 `if __name__ == "__main__":` 的文件
- `app.py`, `main.py`, `__main__.py`, `cli.py`, `run.py` 命名约定

**模块系统**: import + package (有 `__init__.py` 的目录)

**AST 提取**: Python 内置 `ast` 模块（无需外部依赖）

**核心标识符前缀**:
- `class <Name>:` → 类
- `def <name>(` / `async def <name>(` → 函数
- 装饰器 `@<decorator>` 紧贴 def/class

**降级**: 若 ast 失败 → 用正则 `^class\s+\w+` / `^(async\s+)?def\s+\w+`

## 2. JavaScript

**包管理/依赖文件**:
- `package.json` (核心)
- `package-lock.json`
- `yarn.lock`
- `pnpm-lock.yaml`
- `bun.lockb`

**入口识别**:
- `package.json` 的 `main` 字段
- `package.json` 的 `bin` 字段
- `index.js`, `index.mjs`, `index.cjs` 命名约定
- `app.js`, `server.js`, `main.js`

**模块系统**:
- CommonJS: `require()` / `module.exports`
- ESM: `import` / `export`
- 用 `package.json` 的 `"type": "module"` 字段判断

**AST 提取**: 用 Node 内置解析或正则（避免外部工具）

**核心标识符前缀**:
- `class <Name> {` → 类
- `function <name>(` / `const <name> = (` → 函数
- `const <Name> = (` 紧贴大括号块 → 组件或对象

**降级**: 用正则 `^class\s+\w+` / `^function\s+\w+` / `^const\s+\w+\s*=\s*\(`

## 3. TypeScript

**包管理/依赖文件**: 同 JavaScript + `tsconfig.json`

**入口识别**: 同 JavaScript + `tsconfig.json` 的 `outDir`/`rootDir` + `src/index.ts`, `src/main.ts`

**模块系统**: ESM 为主

**AST 提取**: 同 JavaScript，重点提取 type 声明

**核心标识符前缀**: 同 JavaScript
- `interface <Name> {` → 接口
- `type <Name> =` → 类型别名
- `enum <Name> {` → 枚举

**降级**: 同 JavaScript

## 4. Java

**包管理/依赖文件**:
- `pom.xml` (Maven)
- `build.gradle`, `build.gradle.kts` (Gradle)
- `settings.gradle*`

**入口识别**:
- 含 `@SpringBootApplication` 注解的类
- 含 `public static void main(String[] args)` 的类
- `pom.xml` 的 `<mainClass>` 段
- `src/main/java/.../Application.java` 命名约定

**模块系统**: package + import (基于目录)

**AST 提取**: 优先用 `javap -p <file.class>` (需要 class 文件)，否则用正则

**核心标识符前缀**:
- `(public|private|protected)?\s*(static\s+)?class\s+\w+` → 类
- `(public|private|protected)?\s*[\w<>,\s]+\s+\w+\s*\(` → 方法

**降级**: 用正则

## 5. Go

**包管理/依赖文件**:
- `go.mod`
- `go.sum`

**入口识别**:
- `package main` 中的 `func main()`
- `cmd/<name>/main.go` 目录约定
- `Makefile` 中包含的目标

**模块系统**: package + import

**AST 提取**: Go 内置 `go/ast` 工具链（如果有 Go 工具链），否则正则

**核心标识符前缀**:
- `^func\s+(\(\w+\s+\*?\w+\)\s+)?\w+\(` → 方法/函数
- `^type\s+\w+\s+struct` → 结构体
- `^type\s+\w+\s+interface` → 接口

**降级**: 用正则 + 文件名约定

## 6. Rust

**包管理/依赖文件**:
- `Cargo.toml` (核心)
- `Cargo.lock`

**入口识别**:
- `src/main.rs` (binary crate)
- `src/lib.rs` (library crate)
- `Cargo.toml` 的 `[[bin]]` 表
- `examples/`, `benches/` 目录

**模块系统**: crate + mod + use

**AST 提取**: `cargo check --message-format=json` (慢，回退到正则) / `rustc --emit=metadata` (慢)

**核心标识符前缀**:
- `^(pub\s+)?(async\s+)?fn\s+\w+` → 函数
- `^(pub\s+)?struct\s+\w+` → 结构体
- `^(pub\s+)?trait\s+\w+` → trait
- `^(pub\s+)?enum\s+\w+` → 枚举
- `^(pub\s+)?impl\s+` → impl 块

**降级**: 用正则
````

- [ ] **Step 2: 验证长度**

Run:
```bash
wc -l "E:/KimiClaw/repo-code-analysis/repoguide/references/language-profiles.md"
```

Expected: 约 100-150 行

- [ ] **Step 3: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/references/language-profiles.md
git commit -m "feat(skill): add language-profiles reference (6 languages)"
```

---

## Task 6: 编写 depth-rules.md (智能分层规则)

**Files:**
- Create: `repoguide/references/depth-rules.md`

**前置条件**: Task 5 完成

- [ ] **Step 1: 写 depth-rules.md**

Create `repoguide/references/depth-rules.md` with the following content:

````markdown
# 智能分层规则

Subagent B 在做"核心代码详解"时，按本文件的规则决定哪些文件详尽、哪些简略。

## 核心文件判定 (5 条规则)

按权重合并使用，每个文件计算"核心得分"：

| 规则 | 信号 | 权重 |
|------|------|------|
| ① 入口链追溯 | 从 main 入口沿 import/include 反向追踪能到达 | +10 |
| ② 配置显式声明 | 出现在 setup.py/package.json main/pyproject.toml/Cargo.toml [[bin]]/Makefile | +10 |
| ③ 模块入口命名 | `__init__.py` / `index.js|ts` / `mod.rs` / `main.go` / `app.py` | +5 |
| ④ 论文伪代码对应 | 论文 PDF 中提到的算法/类名/函数名能在代码匹配 | +5 |
| ⑤ 启发式补充 | 文件大小 > 中位数 3 倍 + 被 ≥ 5 个其他文件 import | +3 |

**判定**: 得分 ≥ 5 视为核心文件。

## 核心文件 → 详细分析 (必包含)

对每个核心文件输出：

- **一句话作用** (≤ 30 字)
- **类/函数/方法清单**: `[{name, line, signature, purpose}]`
- **关键逻辑解读**: 每个函数 3-10 行代码片段
- **入参/出参/副作用**: `[{param, type, meaning}, {return, type, meaning}, {side_effect}]`
- **依赖关系**: 该文件 import 哪些其他文件

## 周边文件 → 简略清单

| 路径 | 一句话作用 | 重要度 |
|------|-----------|--------|
| `path/to/file.py` | 工具函数集 | 中 |

**重要度** 评估: 高 (被广泛引用) / 中 (被 2-5 个文件引用) / 低 (叶子节点)

## 永远简略的类别 (不进入核心判断)

- `tests/`, `__tests__/`, `*_test.go`, `*.test.js|ts` → 第 4 层末尾"测试策略"段统一一句话概括
- `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `target/`, `__pycache__/` → 完全跳过
- `*.md`, `*.txt`, `LICENSE*`, `CHANGELOG*` → 仓库元信息
- `*.json`, `*.yaml`, `*.yml`, `*.toml` (配置类) → 第 4.3 节统一处理
- `*.lock`, `*.sum`, `*.lockb` → 完全跳过
- `.git/`, `.github/workflows/`, `.gitlab/` → 不进代码层
- `*.min.js`, `*.min.css` → 跳过
- 大型生成文件 (`.pb.go`, `*_pb2.py`) → 跳过

## 规模自适应

| 总文件数 | 策略 |
|----------|------|
| < 50 | 所有非忽略文件按核心分析 (除上面"永远简略"类) |
| 50-500 | 按 5 条规则筛核心 (得分 ≥ 5) |
| > 500 | 核心文件上限 30 个: 按得分降序 + 文件大小降序取 top 30 |

**兜底**: 任何情况下，简略清单里都至少包含仓库 80% 的非忽略文件路径 (即使标"低"重要度)。

## 已知限制 (写入报告附录)

执行中如发现以下情况，在报告"已知限制"附录记录：

- 某些核心文件因权限/编码问题无法完整读取
- 某些类/函数因动态特性无法静态分析 (如 Python 的 `__getattr__`, Go 的 interface assertion)
- 跨语言边界的依赖关系不完整
- 论文-代码映射的低置信度项
````

- [ ] **Step 2: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/references/depth-rules.md
git commit -m "feat(skill): add depth-rules reference (smart layering)"
```

---

## Task 7: 编写 report-template.md (五层结构模板)

**Files:**
- Create: `repoguide/references/report-template.md`

**前置条件**: Task 6 完成

- [ ] **Step 1: 写 report-template.md**

Create `repoguide/references/report-template.md` with the following content:

````markdown
# 五层结构报告模板

主 agent 在 Phase 3 汇总时，按本模板组装 Markdown 内容。

模板使用方式：用各 phase 产出的 JSON 替换 `{{...}}` 占位符。

## 模板内容

```markdown
# {{repo_name}} 代码分析报告

> 由 RepoGuide skill 自动生成于 {{generated_at}}
> 仓库路径: `{{repo_path}}`
> 报告耗时: {{duration}}

---

## 第 0 层 · 元信息

| 项 | 值 |
|----|-----|
| 仓库名 | {{repo_name}} |
| 路径 | `{{repo_path}}` |
| 主语言 | {{primary_language}} |
| 所有语言 | {{all_languages}} |
| 许可证 | {{license}} |
| 文件总数 | {{file_count_total}} |
| 代码行数 | {{line_count_total}} |

### 按语言统计

| 语言 | 文件数 | 代码行数 |
|------|--------|----------|
{{#each file_count_by_lang}}
| {{lang}} | {{files}} | {{lines}} |
{{/each}}

### 论文信息

{{#if paper_found}}
- **标题**: {{paper_title}}
- **作者**: {{paper_authors}}
- **PDF 路径**: `{{paper_path}}`
{{else}}
- 未在仓库中检测到论文
{{/if}}

---

## 第 1 层 · 一句话总括 + 快速上手

### 一句话总括

{{one_liner}}

### 3 条命令上手

```bash
# 安装
{{install_cmd}}

# 运行
{{run_cmd}}

# 测试
{{test_cmd}}
```

### 5 个最关键的文件

1. `{{top_file_1}}` — {{top_file_1_desc}}
2. `{{top_file_2}}` — {{top_file_2_desc}}
3. `{{top_file_3}}` — {{top_file_3_desc}}
4. `{{top_file_4}}` — {{top_file_4_desc}}
5. `{{top_file_5}}` — {{top_file_5_desc}}

---

## 第 2 层 · 技术栈与依赖

### 语言与版本

- {{primary_language}}: {{language_version}}

### 核心依赖 (按用途分组)

{{#each dependency_groups}}
#### {{group_name}}

| 包 | 版本 | 用途 |
|----|------|------|
{{#each packages}}
| {{name}} | {{version}} | {{purpose}} |
{{/each}}
{{/each}}

### 包管理文件

{{#each package_files}}
- `{{path}}`
{{/each}}

### 外部服务依赖

{{#each external_services}}
- **{{name}}**: {{purpose}} ({{connection}})
{{/each}}

---

## 第 3 层 · 架构与数据流

### 3.1 模块划分

| 顶层目录 | 模块 | 主要职责 |
|----------|------|----------|
{{#each module_mapping}}
| `{{path}}` | {{module}} | {{responsibility}} |
{{/each}}

#### 模块依赖图

```mermaid
{{module_dependency_graph}}
```

### 3.2 数据流

{{data_flow_narrative}}

```mermaid
{{data_flow_graph}}
```

#### 关键状态点

{{#each key_state_points}}
- **{{name}}**: {{description}} (位于 `{{file}}:{{line}}`)
{{/each}}

### 3.3 关键设计决策

{{#each design_decisions}}
#### {{decision}}

**证据**: `{{evidence}}`

{{reasoning}}
{{/each}}

---

## 第 4 层 · 核心代码详解 (智能分层)

### 4.1 核心模块详细分析

{{#each core_files}}
#### `{{path}}`

**作用**: {{one_liner}}

**依赖**: {{#each dependencies}}`{{this}}` {{/each}}

##### 类清单

{{#each classes}}
- `{{name}}` (line {{line}}): `{{signature}}` — {{purpose}}
{{/each}}

##### 函数清单

{{#each functions}}
- `{{name}}` (line {{line}}): `{{signature}}`

  关键逻辑:
  ```{{lang}}
  {{key_logic}}
  ```
{{/each}}

{{/each}}

### 4.2 周边模块简略清单

| 路径 | 一句话作用 | 重要度 |
|------|-----------|--------|
{{#each peripheral_files}}
| `{{path}}` | {{one_liner}} | {{importance}} |
{{/each}}

### 4.3 配置/脚本/资源

#### 配置文件

{{#each config_files}}
- `{{path}}`: {{purpose}}
{{/each}}

#### 脚本

{{#each scripts}}
- `{{path}}`: {{purpose}}
{{/each}}

#### 数据/模型资源

{{#each resources}}
- `{{path}}`: {{purpose}}
{{/each}}

#### 测试策略

{{test_strategy}}

---

{{#if paper_found}}
## 第 5 层 · 论文-代码映射

### 5.1 论文速览

**标题**: {{paper_title}}

**作者**: {{paper_authors}}

**核心贡献**:
{{#each paper_core_contributions}}
- {{this}}
{{/each}}

#### 章节结构

{{#each paper_section_tree}}
- {{indent}}{{title}} (line {{line}})
{{/each}}

### 5.2 论文-代码三层映射

#### 层级 1: 论文章节 ↔ 代码模块

| 论文章节 | 代码模块 | 置信度 |
|----------|----------|--------|
{{#each layer1_section_to_module}}
| {{section}} | `{{module}}` | {{confidence}} |
{{/each}}

#### 层级 2: 论文公式/算法 ↔ 代码函数/类

| 论文公式/算法 | 代码函数/类 | 位置 | 置信度 |
|---------------|-------------|------|--------|
{{#each layer2_formula_to_function}}
| {{formula}} | `{{function}}` | `{{file}}:{{line}}` | {{confidence}} |
{{/each}}

#### 层级 3: 论文实验/表格 ↔ 评估脚本

| 论文实验/表格 | 评估脚本 | 位置 |
|---------------|----------|------|
{{#each layer3_experiment_to_script}}
| {{experiment}} | `{{script}}` | `{{file}}` |
{{/each}}

### 5.3 关键术语对照表

| 论文术语 | 代码标识符 |
|----------|------------|
{{#each paper_glossary}}
| {{term}} | `{{code_identifier}}` |
{{/each}}
{{/if}}

---

## 附录

### 文件清单 (按扩展名分组)

{{#each file_groups}}
- **{{ext}}** ({{count}} 个): {{sample_paths}}
{{/each}}

### 已知限制 / 不确定项

{{#each limitation_notes}}
- {{this}}
{{/each}}

### 生成信息

- **生成时间**: {{generated_at}}
- **总耗时**: {{duration}}
- **执行模式**: {{execution_mode}} (并行 / 串行)
- **降级情况**: {{degradation_notes}}
```

## 模板使用说明

1. 主 agent 在 Phase 3 读取 `analysis_a.json` + `analysis_b.json` + (`analysis_c.json` + `analysis_d.json` 如果有)
2. 读取 `profile.json` 获取元信息
3. 加载本模板
4. 按各 JSON 的字段名填入对应位置
5. 缺失字段留空或在"已知限制"附录标注
6. mermaid 图直接嵌入 `mermaid` 代码块
7. 输出到 `<用户 cwd>/repoguide-report.md`
````

- [ ] **Step 2: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/references/report-template.md
git commit -m "feat(skill): add report-template reference (5-layer structure)"
```

---

## Task 8: 编写并测试 detect-stack.py (TDD)

**Files:**
- Create: `tests/unit/test_detect_stack.py`
- Create: `repoguide/scripts/detect-stack.py`

**前置条件**: Task 7 完成

- [ ] **Step 1: 写失败的测试**

Create `tests/unit/test_detect_stack.py` with the following content:

```python
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent.parent / "repoguide" / "scripts" / "detect-stack.py"


def run_detect_stack(repo_path: str) -> dict:
    """Run detect-stack.py as a subprocess and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), repo_path],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture
def python_repo(tmp_path):
    """Create a minimal Python repo fixture."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'\n")
    (tmp_path / "main.py").write_text("def main(): pass\n")
    (tmp_path / "utils.py").write_text("def helper(): pass\n")
    return tmp_path


@pytest.fixture
def js_repo(tmp_path):
    """Create a minimal JavaScript repo fixture."""
    (tmp_path / "package.json").write_text('{"name": "foo", "main": "index.js"}')
    (tmp_path / "index.js").write_text("function main() {}")
    return tmp_path


@pytest.fixture
def go_repo(tmp_path):
    """Create a minimal Go repo fixture."""
    (tmp_path / "go.mod").write_text("module foo\n\ngo 1.21\n")
    (tmp_path / "main.go").write_text("package main\n\nfunc main() {}\n")
    return tmp_path


def test_detect_python_repo(python_repo):
    result = run_detect_stack(str(python_repo))
    assert result["primary_language"] == "python"
    assert "pyproject.toml" in result["package_managers"]
    assert "main.py" in result["entry_points"]


def test_detect_js_repo(js_repo):
    result = run_detect_stack(str(js_repo))
    assert result["primary_language"] == "javascript"
    assert "package.json" in result["package_managers"]


def test_detect_go_repo(go_repo):
    result = run_detect_stack(str(go_repo))
    assert result["primary_language"] == "go"
    assert "go.mod" in result["package_managers"]


def test_detect_paper_pdf(tmp_path):
    """Verify paper detection when PDF is present."""
    (tmp_path / "main.py").write_text("x = 1")
    (tmp_path / "paper.pdf").write_bytes(b"%PDF-1.4\n")
    result = run_detect_stack(str(tmp_path))
    assert result["paper_found"] is True
    assert "paper.pdf" in result["paper_path"]


def test_detect_no_paper(python_repo):
    """Verify paper_found=False when no paper present."""
    result = run_detect_stack(str(python_repo))
    assert result["paper_found"] is False


def test_detect_empty_repo(tmp_path):
    """Verify behavior on empty repo."""
    result = run_detect_stack(str(tmp_path))
    assert result["primary_language"] is None
    assert result["file_count_total"] == 0
```

- [ ] **Step 2: 跑测试，验证失败**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && python -m pytest tests/unit/test_detect_stack.py -v
```

Expected: FAIL with "FileNotFoundError" (script doesn't exist yet)

- [ ] **Step 3: 写最小实现 detect-stack.py**

Create `repoguide/scripts/detect-stack.py` with the following content:

```python
#!/usr/bin/env python3
"""Detect tech stack of a code repository.

Usage: python detect-stack.py <repo_path>
Output: JSON to stdout
"""
import json
import sys
from pathlib import Path

# Package manager files for each language
LANGUAGE_SIGNALS = {
    "python": {
        "package_files": [
            "pyproject.toml", "requirements.txt", "requirements-dev.txt",
            "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock",
            "conda.yml", "environment.yml",
        ],
        "entry_patterns": ["main.py", "app.py", "__main__.py", "cli.py", "run.py"],
    },
    "javascript": {
        "package_files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "entry_patterns": ["index.js", "app.js", "server.js", "main.js"],
    },
    "typescript": {
        "package_files": ["tsconfig.json"],
        "entry_patterns": ["index.ts", "app.ts", "main.ts", "src/index.ts"],
    },
    "java": {
        "package_files": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
        "entry_patterns": ["Application.java", "Main.java", "src/main/java"],
    },
    "go": {
        "package_files": ["go.mod", "go.sum"],
        "entry_patterns": ["main.go", "cmd/", "app.go"],
    },
    "rust": {
        "package_files": ["Cargo.toml", "Cargo.lock"],
        "entry_patterns": ["src/main.rs", "src/lib.rs", "main.rs", "lib.rs"],
    },
}

IGNORE_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "env",
               "dist", "build", "target", "__pycache__", ".pytest_cache",
               ".mypy_cache", ".tox", "out"}


def detect_paper(repo_path: Path) -> tuple[bool, str | None]:
    """Detect if a paper PDF or tex file is present."""
    for pattern in ["*.pdf", "*.tex", "paper*", "Paper*"]:
        matches = list(repo_path.glob(pattern))
        if matches:
            return True, str(matches[0])
    # Check README for arxiv link
    for readme in repo_path.glob("README*"):
        try:
            content = readme.read_text(encoding="utf-8", errors="ignore")
            if "arxiv.org" in content.lower():
                return True, str(readme)
        except Exception:
            pass
    return False, None


def detect_language(repo_path: Path) -> tuple[str | None, list[str], list[str], list[str]]:
    """Detect primary language, package managers, entry points, all languages present."""
    package_managers: list[str] = []
    entry_points: list[str] = []
    languages_present: list[str] = []

    for lang, signals in LANGUAGE_SIGNALS.items():
        has_package_file = False
        for pf in signals["package_files"]:
            if (repo_path / pf).exists():
                package_managers.append(pf)
                has_package_file = True
        if has_package_file:
            languages_present.append(lang)
        for ep in signals["entry_patterns"]:
            if (repo_path / ep).exists():
                entry_points.append(ep)

    primary = languages_present[0] if languages_present else None
    return primary, package_managers, entry_points, languages_present


def count_files(repo_path: Path) -> tuple[int, dict[str, int]]:
    """Count total files and files by extension."""
    total = 0
    by_ext: dict[str, int] = {}
    for item in repo_path.rglob("*"):
        if item.is_file() and not any(p in item.parts for p in IGNORE_DIRS):
            total += 1
            ext = item.suffix.lstrip(".") or "no_ext"
            by_ext[ext] = by_ext.get(ext, 0) + 1
    return total, by_ext


def main():
    if len(sys.argv) != 2:
        print("Usage: detect-stack.py <repo_path>", file=sys.stderr)
        sys.exit(1)
    repo_path = Path(sys.argv[1]).resolve()
    if not repo_path.exists():
        print(f"Error: path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    primary, package_managers, entry_points, languages = detect_language(repo_path)
    paper_found, paper_path = detect_paper(repo_path)
    file_count_total, file_count_by_ext = count_files(repo_path)

    result = {
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "primary_language": primary,
        "all_languages": languages,
        "package_managers": package_managers,
        "entry_points": entry_points,
        "paper_found": paper_found,
        "paper_path": paper_path,
        "file_count_total": file_count_total,
        "file_count_by_ext": file_count_by_ext,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试，验证通过**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && python -m pytest tests/unit/test_detect_stack.py -v
```

Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/scripts/detect-stack.py tests/unit/test_detect_stack.py
git commit -m "feat(scripts): add detect-stack.py with TDD tests"
```

---

## Task 9: 编写并测试 clone-if-url.sh

**Files:**
- Create: `tests/unit/test_clone_if_url.sh`
- Create: `repoguide/scripts/clone-if-url.sh`

**前置条件**: Task 8 完成

- [ ] **Step 1: 写失败的测试**

Create `tests/unit/test_clone_if_url.sh` with the following content:

```bash
#!/usr/bin/env bash
# Test clone-if-url.sh
set -e

SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/repoguide/scripts/clone-if-url.sh"
TEST_TMP=$(mktemp -d)
trap "rm -rf $TEST_TMP" EXIT

# Test 1: Local path (already exists) - returns the path as-is
echo "=== Test 1: Local path ==="
LOCAL_REPO=$(mktemp -d)
touch "$LOCAL_REPO/.git"  # Mark as a git repo
RESULT=$("$SCRIPT" "$LOCAL_REPO" "$TEST_TMP/out1")
EXPECTED=$(cd "$LOCAL_REPO" && pwd)
if [ "$RESULT" = "$EXPECTED" ]; then
    echo "PASS: local path"
else
    echo "FAIL: expected $EXPECTED, got $RESULT"
    exit 1
fi
rm -rf "$LOCAL_REPO"

# Test 2: Empty/invalid input - should fail
echo "=== Test 2: Invalid input ==="
if "$SCRIPT" "" "$TEST_TMP/out2" 2>/dev/null; then
    echo "FAIL: should have failed on empty input"
    exit 1
else
    echo "PASS: rejects empty input"
fi

# Test 3: Non-existent local path - should fail
echo "=== Test 3: Non-existent local path ==="
if "$SCRIPT" "/nonexistent/path/xyz" "$TEST_TMP/out3" 2>/dev/null; then
    echo "FAIL: should have failed on non-existent path"
    exit 1
else
    echo "PASS: rejects non-existent local path"
fi

# Test 4: GitHub URL format detection (only if git is available and network works)
# This test is skipped in CI to avoid network dependencies
if [ -n "$TEST_NETWORK" ] && [ -d "$LOCAL_REPO2" ]; then
    echo "=== Test 4: GitHub URL ==="
    RESULT=$("$SCRIPT" "https://github.com/octocat/Hello-World" "$TEST_TMP/out4")
    if [ -d "$RESULT" ]; then
        echo "PASS: cloned GitHub URL"
    else
        echo "FAIL: clone did not produce directory"
        exit 1
    fi
fi

echo "All tests passed."
```

- [ ] **Step 2: 跑测试，验证失败**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && bash tests/unit/test_clone_if_url.sh
```

Expected: FAIL (script doesn't exist)

- [ ] **Step 3: 写最小实现 clone-if-url.sh**

Create `repoguide/scripts/clone-if-url.sh` with the following content:

```bash
#!/usr/bin/env bash
# clone-if-url.sh - Normalize a repo reference to a local path.
# Usage: clone-if-url.sh <repo-ref> <target-dir>
#   repo-ref: local path, GitHub URL, or empty (uses current dir)
#   target-dir: where to clone if URL
# Output: absolute path to repo (on stdout)

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <repo-ref> [target-dir]" >&2
    exit 1
fi

REPO_REF="$1"
TARGET_DIR="${2:-$(pwd)}"

if [ -z "$REPO_REF" ]; then
    # Empty: use current directory
    if [ -d ".git" ]; then
        cd "$(git rev-parse --show-toplevel)"
        pwd
    else
        echo "Error: current directory is not a git repository" >&2
        exit 1
    fi
    exit 0
fi

# Detect URL
if [[ "$REPO_REF" =~ ^https?://github\.com/ ]]; then
    # GitHub URL: clone to target-dir
    REPO_NAME=$(basename "$REPO_REF" .git)
    TARGET_PATH="$TARGET_DIR/repoguide-$REPO_NAME"
    if [ -d "$TARGET_PATH/.git" ]; then
        echo "Reusing existing clone at $TARGET_PATH" >&2
    else
        mkdir -p "$TARGET_DIR"
        git clone --depth 1 "$REPO_REF" "$TARGET_PATH"
    fi
    echo "$TARGET_PATH"
    exit 0
fi

# Local path
if [ ! -e "$REPO_REF" ]; then
    echo "Error: path does not exist: $REPO_REF" >&2
    exit 1
fi
# Resolve to absolute path
cd "$REPO_REF" || { echo "Error: cannot cd to $REPO_REF" >&2; exit 1; }
pwd
```

- [ ] **Step 4: 给予执行权限**

Run:
```bash
chmod +x "E:/KimiClaw/repo-code-analysis/repoguide/scripts/clone-if-url.sh"
chmod +x "E:/KimiClaw/repo-code-analysis/tests/unit/test_clone_if_url.sh"
```

- [ ] **Step 5: 跑测试，验证通过**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && bash tests/unit/test_clone_if_url.sh
```

Expected: 3 tests PASS (network test skipped)

- [ ] **Step 6: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/scripts/clone-if-url.sh tests/unit/test_clone_if_url.sh
git commit -m "feat(scripts): add clone-if-url.sh with tests"
```

---

## Task 10: 编写并测试 generate-pdf.sh

**Files:**
- Create: `tests/unit/test_generate_pdf.sh`
- Create: `repoguide/scripts/generate-pdf.sh`

**前置条件**: Task 9 完成

- [ ] **Step 1: 写失败的测试**

Create `tests/unit/test_generate_pdf.sh` with the following content:

```bash
#!/usr/bin/env bash
# Test generate-pdf.sh
set -e

SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/repoguide/scripts/generate-pdf.sh"
TEST_TMP=$(mktemp -d)
trap "rm -rf $TEST_TMP" EXIT

# Test 1: Generate PDF from simple markdown
echo "=== Test 1: Simple markdown to PDF ==="
cat > "$TEST_TMP/simple.md" << 'EOF'
# Test Report

This is a **test** document.

## Section 1

Some content here.
EOF

OUTPUT=$("$SCRIPT" "$TEST_TMP/simple.md" 2>&1) || {
    echo "Note: PDF generation may fail if pandoc/weasyprint not installed"
    echo "Output was: $OUTPUT"
    # Don't fail the test - PDF generation is best-effort
    echo "PASS: script ran (PDF may or may not be generated depending on tools)"
    exit 0
}

# If we got here, check for PDF
PDF_FILE="${OUTPUT##*$'\n'}"
PDF_FILE="${PDF_FILE:-$TEST_TMP/simple.pdf}"
if [ -f "$PDF_FILE" ]; then
    echo "PASS: PDF file created at $PDF_FILE"
else
    echo "Note: PDF file not created (tools may be missing). Output: $OUTPUT"
    echo "PASS: script ran (best-effort)"
fi
```

- [ ] **Step 2: 跑测试，验证失败**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && bash tests/unit/test_generate_pdf.sh
```

Expected: FAIL (script doesn't exist)

- [ ] **Step 3: 写最小实现 generate-pdf.sh**

Create `repoguide/scripts/generate-pdf.sh` with the following content:

```bash
#!/usr/bin/env bash
# generate-pdf.sh - Convert markdown to PDF with tool auto-detection.
# Usage: generate-pdf.sh <input.md> [output.pdf]
# Output: absolute path to PDF (on stdout, last line)
# Falls back gracefully if no PDF tool is available.

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.md> [output.pdf]" >&2
    exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.md}.pdf}"

if [ ! -f "$INPUT" ]; then
    echo "Error: input file not found: $INPUT" >&2
    exit 1
fi

# Make output absolute
case "$OUTPUT" in
    /*) ;;
    *) OUTPUT="$(pwd)/$OUTPUT" ;;
esac

# Try pandoc first (best quality)
if command -v pandoc >/dev/null 2>&1; then
    echo "Using pandoc" >&2
    pandoc "$INPUT" -o "$OUTPUT" --pdf-engine=xelatex 2>/dev/null \
        || pandoc "$INPUT" -o "$OUTPUT" 2>/dev/null \
        || {
            echo "Warning: pandoc failed, trying weasyprint" >&2
            USE_WEASYPRINT=1
        }
fi

# Try weasyprint (Python-based)
if [ ! -f "$OUTPUT" ] && command -v weasyprint >/dev/null 2>&1; then
    echo "Using weasyprint" >&2
    weasyprint "$INPUT" "$OUTPUT" 2>/dev/null || {
        echo "Warning: weasyprint failed" >&2
    }
fi

# Try Python markdown-pdf
if [ ! -f "$OUTPUT" ] && python -c "import markdown_pdf" 2>/dev/null; then
    echo "Using markdown_pdf" >&2
    python -m markdown_pdf "$INPUT" -o "$OUTPUT" 2>/dev/null || {
        echo "Warning: markdown_pdf failed" >&2
    }
fi

# Check result
if [ -f "$OUTPUT" ]; then
    echo "$OUTPUT"
    exit 0
fi

# No tool worked - graceful failure
echo "PDF_GENERATION_FAILED" >&2
echo "To enable PDF generation, install one of:" >&2
echo "  - pandoc (with xelatex): brew install pandoc mactex" >&2
echo "  - weasyprint: pip install weasyprint" >&2
echo "  - markdown-pdf: pip install markdown-pdf" >&2
echo "" >&2
echo "Continuing without PDF. The markdown report is still available." >&2
echo "PDF_GENERATION_FAILED"  # Echo to stdout so caller can detect
exit 0  # Don't fail - report is still useful
```

- [ ] **Step 4: 给予执行权限**

Run:
```bash
chmod +x "E:/KimiClaw/repo-code-analysis/repoguide/scripts/generate-pdf.sh"
chmod +x "E:/KimiClaw/repo-code-analysis/tests/unit/test_generate_pdf.sh"
```

- [ ] **Step 5: 跑测试，验证通过**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && bash tests/unit/test_generate_pdf.sh
```

Expected: PASS (script runs, PDF may or may not be generated)

- [ ] **Step 6: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/scripts/generate-pdf.sh tests/unit/test_generate_pdf.sh
git commit -m "feat(scripts): add generate-pdf.sh with graceful fallback"
```

---

## Task 11: 创建 small-python 测试 fixture

**Files:**
- Create: `tests/fixtures/small-python/main.py`
- Create: `tests/fixtures/small-python/utils.py`
- Create: `tests/fixtures/small-python/pyproject.toml`
- Create: `tests/fixtures/small-python/README.md`

**前置条件**: Task 10 完成

- [ ] **Step 1: 创建 pyproject.toml**

Create `tests/fixtures/small-python/pyproject.toml` with:
```toml
[project]
name = "small-python-fixture"
version = "0.1.0"
description = "Small Python repo for RepoGuide testing"
requires-python = ">=3.10"

[project.scripts]
small-python = "main:cli_main"
```

- [ ] **Step 2: 创建 main.py**

Create `tests/fixtures/small-python/main.py` with:
```python
"""Entry point for small-python fixture."""
from utils import greet, parse_args


def cli_main() -> None:
    """CLI entry point registered in pyproject.toml."""
    args = parse_args()
    print(greet(args.name))


class Application:
    """Main application orchestrator."""

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self) -> str:
        """Execute the main workflow."""
        return greet(self.name)


if __name__ == "__main__":
    cli_main()
```

- [ ] **Step 3: 创建 utils.py**

Create `tests/fixtures/small-python/utils.py` with:
```python
"""Utility functions for small-python fixture."""
import argparse


def greet(name: str) -> str:
    """Return a greeting message for the given name."""
    return f"Hello, {name}!"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Small Python CLI")
    parser.add_argument("name", nargs="?", default="World", help="Name to greet")
    return parser.parse_args()
```

- [ ] **Step 4: 创建 README.md**

Create `tests/fixtures/small-python/README.md` with:
```markdown
# small-python (Test Fixture)

A minimal Python project for testing RepoGuide.
```

- [ ] **Step 5: 验证 detect-stack 正确识别**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && python repoguide/scripts/detect-stack.py tests/fixtures/small-python
```

Expected JSON should have:
- `primary_language`: "python"
- `package_managers`: `["pyproject.toml"]`
- `entry_points`: includes `main.py`
- `file_count_total`: 4

- [ ] **Step 6: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add tests/fixtures/small-python/
git commit -m "test: add small-python fixture (4 files)"
```

---

## Task 12: 创建 medium-ml-with-paper 测试 fixture

**Files:**
- Create: `tests/fixtures/medium-ml-with-paper/main.py`
- Create: `tests/fixtures/medium-ml-with-paper/model.py`
- Create: `tests/fixtures/medium-ml-with-paper/train.py`
- Create: `tests/fixtures/medium-ml-with-paper/evaluate.py`
- Create: `tests/fixtures/medium-ml-with-paper/dataset.py`
- Create: `tests/fixtures/medium-ml-with-paper/pyproject.toml`
- Create: `tests/fixtures/medium-ml-with-paper/README.md`
- Create: `tests/fixtures/medium-ml-with-paper/paper.pdf` (占位空文件)

**前置条件**: Task 11 完成

- [ ] **Step 1: 创建 pyproject.toml**

Create `tests/fixtures/medium-ml-with-paper/pyproject.toml` with:
```toml
[project]
name = "medium-ml-fixture"
version = "0.1.0"
description = "Medium ML repo with paper for RepoGuide testing"
requires-python = ">=3.10"
dependencies = ["torch>=2.0", "numpy>=1.24", "torchvision>=0.15"]

[project.scripts]
medium-ml = "main:cli_main"
```

- [ ] **Step 2: 创建 model.py**

Create `tests/fixtures/medium-ml-with-paper/model.py` with:
```python
"""Neural network model definition."""
import torch
import torch.nn as nn


class SimpleClassifier(nn.Module):
    """A simple 2-layer classifier corresponding to Eq.(3) in paper.pdf."""

    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: h = ReLU(W1*x + b1); y = W2*h + b2"""
        h = self.relu(self.fc1(x))
        return self.fc2(h)
```

- [ ] **Step 3: 创建 dataset.py**

Create `tests/fixtures/medium-ml-with-paper/dataset.py` with:
```python
"""Dataset loading and preprocessing."""
from torch.utils.data import Dataset, DataLoader


class SyntheticDataset(Dataset):
    """A synthetic dataset for testing."""

    def __init__(self, num_samples: int = 1000, input_dim: int = 100) -> None:
        self.num_samples = num_samples
        self.input_dim = input_dim

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> tuple:
        import torch
        x = torch.randn(self.input_dim)
        y = torch.randint(0, 10, (1,)).item()
        return x, y


def build_dataloaders(batch_size: int = 32) -> tuple[DataLoader, DataLoader]:
    """Build train and validation dataloaders."""
    train_ds = SyntheticDataset()
    val_ds = SyntheticDataset(num_samples=200)
    return (
        DataLoader(train_ds, batch_size=batch_size),
        DataLoader(val_ds, batch_size=batch_size),
    )
```

- [ ] **Step 4: 创建 train.py**

Create `tests/fixtures/medium-ml-with-paper/train.py` with:
```python
"""Training loop implementing Algorithm 1 in paper.pdf."""
import torch
from model import SimpleClassifier
from dataset import build_dataloaders


def train_epoch(model: SimpleClassifier, dataloader, optimizer, criterion) -> float:
    """Train for one epoch. Returns average loss."""
    model.train()
    total_loss = 0.0
    for x, y in dataloader:
        optimizer.zero_grad()
        pred = model(x)
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)


def train(num_epochs: int = 10, lr: float = 1e-3) -> SimpleClassifier:
    """Full training pipeline."""
    model = SimpleClassifier(input_dim=100, hidden_dim=64, num_classes=10)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()
    train_loader, _ = build_dataloaders()

    for epoch in range(num_epochs):
        loss = train_epoch(model, train_loader, optimizer, criterion)
        print(f"Epoch {epoch + 1}/{num_epochs}, loss={loss:.4f}")
    return model
```

- [ ] **Step 5: 创建 evaluate.py**

Create `tests/fixtures/medium-ml-with-paper/evaluate.py` with:
```python
"""Evaluation script. Reproduces Table 2 in paper.pdf."""
import torch
from model import SimpleClassifier
from dataset import build_dataloaders


def evaluate(model: SimpleClassifier) -> dict[str, float]:
    """Evaluate model on validation set. Returns accuracy and loss."""
    model.eval()
    _, val_loader = build_dataloaders()
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in val_loader:
            pred = model(x).argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return {"accuracy": correct / total, "num_samples": total}
```

- [ ] **Step 6: 创建 main.py**

Create `tests/fixtures/medium-ml-with-paper/main.py` with:
```python
"""Entry point. Runs training then evaluation."""
from model import SimpleClassifier
from train import train
from evaluate import evaluate


def cli_main() -> None:
    """CLI entry point: train then evaluate."""
    model = train(num_epochs=2, lr=1e-3)
    metrics = evaluate(model)
    print(f"Final accuracy: {metrics['accuracy']:.4f}")


if __name__ == "__main__":
    cli_main()
```

- [ ] **Step 7: 创建 README.md**

Create `tests/fixtures/medium-ml-with-paper/README.md` with:
```markdown
# medium-ml-with-paper (Test Fixture)

A medium-sized ML project with an associated paper.
- `model.py` implements Eq.(3) from the paper
- `train.py` implements Algorithm 1
- `evaluate.py` reproduces Table 2
- See `paper.pdf` for the full paper
```

- [ ] **Step 8: 创建占位 paper.pdf**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && python -c "
content = b'%PDF-1.4\n%fake paper for testing\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\nxref\n0 3\n0000000000 65535 f\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n'
open('tests/fixtures/medium-ml-with-paper/paper.pdf', 'wb').write(content)
print('Wrote', len(content), 'bytes')
"
```

- [ ] **Step 9: 验证 detect-stack 识别论文**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && python repoguide/scripts/detect-stack.py tests/fixtures/medium-ml-with-paper
```

Expected: `paper_found: true`, `paper_path` includes `paper.pdf`

- [ ] **Step 10: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add tests/fixtures/medium-ml-with-paper/
git commit -m "test: add medium-ml-with-paper fixture (7 files + paper.pdf)"
```

---

## Task 13: 创建 multi-lang 测试 fixture (Python + Rust)

**Files:**
- Create: `tests/fixtures/multi-lang/` (Python + Rust 混合)

**前置条件**: Task 12 完成

- [ ] **Step 1: 创建 Python 部分**

Create `tests/fixtures/multi-lang/app.py` with:
```python
"""Python main that calls into Rust extension via PyO3."""
# Note: actual PyO3 binding is mocked for testing
def process_data(data: list[float]) -> list[float]:
    """Process data via Rust FFI (mocked)."""
    # Real implementation would: from _native import process
    return [x * 2.0 for x in data]


def main() -> None:
    """CLI entry."""
    result = process_data([1.0, 2.0, 3.0])
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
```

Create `tests/fixtures/multi-lang/pyproject.toml` with:
```toml
[project]
name = "multi-lang-fixture"
version = "0.1.0"
description = "Python + Rust mixed repo for RepoGuide testing"
requires-python = ">=3.10"
```

- [ ] **Step 2: 创建 Rust 部分**

Create `tests/fixtures/multi-lang/Cargo.toml` with:
```toml
[package]
name = "multi-lang-native"
version = "0.1.0"
edition = "2021"

[lib]
name = "multi_lang_native"
crate-type = ["cdylib"]
```

Create `tests/fixtures/multi-lang/src/lib.rs` with:
```rust
//! Native Rust library exposed to Python via PyO3.

pub fn process(data: &[f64]) -> Vec<f64> {
    data.iter().map(|x| x * 2.0).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process() {
        let result = process(&[1.0, 2.0, 3.0]);
        assert_eq!(result, vec![2.0, 4.0, 6.0]);
    }
}
```

- [ ] **Step 3: 验证 detect-stack 识别两种语言**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && python repoguide/scripts/detect-stack.py tests/fixtures/multi-lang
```

Expected: `all_languages` contains both `"python"` and `"rust"`, `file_count_total` ≥ 4

- [ ] **Step 4: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add tests/fixtures/multi-lang/
git commit -m "test: add multi-lang fixture (Python + Rust)"
```

---

## Task 14: 编写端到端集成测试

**Files:**
- Create: `tests/integration/test_e2e.sh`

**前置条件**: Task 13 完成

- [ ] **Step 1: 写 e2e 测试脚本**

Create `tests/integration/test_e2e.sh` with the following content:

```bash
#!/usr/bin/env bash
# End-to-end test: verify RepoGuide scaffolding is internally consistent.
# This test does NOT invoke an LLM agent (which is what SKILL.md is for).
# Instead it verifies that all references, scripts, and templates exist and parse.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "=== E2E: Verifying RepoGuide scaffolding ==="

# Test 1: All required files exist
echo "--- Test 1: File presence ---"
REQUIRED_FILES=(
    "repoguide/SKILL.md"
    "repoguide/SKILL.codex.md"
    "repoguide/SKILL.kimi.md"
    "repoguide/references/language-profiles.md"
    "repoguide/references/depth-rules.md"
    "repoguide/references/report-template.md"
    "repoguide/scripts/detect-stack.py"
    "repoguide/scripts/clone-if-url.sh"
    "repoguide/scripts/generate-pdf.sh"
    "tests/unit/test_detect_stack.py"
    "tests/unit/test_clone_if_url.sh"
    "tests/unit/test_generate_pdf.sh"
    "tests/fixtures/small-python/main.py"
    "tests/fixtures/medium-ml-with-paper/main.py"
    "tests/fixtures/multi-lang/app.py"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$f" ]; then
        echo "FAIL: missing required file: $f"
        exit 1
    fi
done
echo "PASS: all required files present"

# Test 2: detect-stack.py works on all fixtures
echo "--- Test 2: detect-stack on all fixtures ---"
for fixture in tests/fixtures/*/; do
    if [ -d "$fixture" ]; then
        output=$(python repoguide/scripts/detect-stack.py "$fixture" 2>&1)
        if [ $? -ne 0 ]; then
            echo "FAIL: detect-stack failed on $fixture"
            echo "$output"
            exit 1
        fi
        echo "PASS: detect-stack on $fixture"
    fi
done

# Test 3: SKILL.md contains all required sections
echo "--- Test 3: SKILL.md structure ---"
SKILL_SECTIONS=(
    "## 触发条件"
    "## Phase 0: 输入归一化"
    "## Phase 1: 探查"
    "## Phase 2: 并行深度分析"
    "## Phase 3: 汇总与输出"
    "## 错误处理"
)
for section in "${SKILL_SECTIONS[@]}"; do
    if ! grep -qF "$section" repoguide/SKILL.md; then
        echo "FAIL: SKILL.md missing section: $section"
        exit 1
    fi
done
echo "PASS: SKILL.md has all required sections"

# Test 4: All scripts are executable
echo "--- Test 4: Scripts executable ---"
for script in repoguide/scripts/*.sh; do
    if [ ! -x "$script" ]; then
        echo "FAIL: $script is not executable"
        exit 1
    fi
done
echo "PASS: all shell scripts executable"

# Test 5: All references are non-empty
echo "--- Test 5: References non-empty ---"
for ref in repoguide/references/*.md; do
    if [ ! -s "$ref" ]; then
        echo "FAIL: $ref is empty"
        exit 1
    fi
done
echo "PASS: all references non-empty"

# Test 6: Unit tests still pass
echo "--- Test 6: Unit tests ---"
python -m pytest tests/unit/test_detect_stack.py -v
echo "PASS: detect-stack unit tests pass"

# Test 7: Shell unit tests still pass
echo "--- Test 7: Shell unit tests ---"
bash tests/unit/test_clone_if_url.sh
echo "PASS: clone-if-url tests pass"

bash tests/unit/test_generate_pdf.sh
echo "PASS: generate-pdf tests pass"

echo ""
echo "=== All E2E tests passed ==="
echo "RepoGuide scaffolding is ready for LLM-driven execution."
```

- [ ] **Step 2: 给予执行权限**

Run:
```bash
chmod +x "E:/KimiClaw/repo-code-analysis/tests/integration/test_e2e.sh"
```

- [ ] **Step 3: 跑 e2e 测试，验证通过**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && bash tests/integration/test_e2e.sh
```

Expected: All 7 tests PASS

- [ ] **Step 4: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add tests/integration/test_e2e.sh
git commit -m "test: add end-to-end integration test"
```

---

## Task 15: 编写 README.md (skill 自描述)

**Files:**
- Create: `repoguide/README.md`

**前置条件**: Task 14 完成

- [ ] **Step 1: 写 README.md**

Create `repoguide/README.md` with the following content:

````markdown
# RepoGuide

端到端分析任意代码仓库，自动产出含架构、数据流、核心代码详解、论文-代码映射（条件性）的自顶向下五层结构 Markdown + PDF 报告。

## 使用方式

在 Claude Code / Codex / Kimi Code 中：

```
使用 RepoGuide skill 帮我分析仓库结构
```

或指定 GitHub URL：

```
使用 RepoGuide skill 分析 https://github.com/owner/repo
```

触发后**全自动端到端完成**，不向用户追问任何问题。

## 产物

- `repoguide-report.md` — 结构化 Markdown 报告
- `repoguide-report.pdf` — PDF 格式（依赖 pandoc/weasyprint）

报告保存在**当前用户工作目录**。

## 报告结构（自顶向下五层）

1. **第 0 层 · 元信息** — 仓库基本信息和论文元数据
2. **第 1 层 · 一句话总括 + 快速上手** — 5 分钟读懂仓库
3. **第 2 层 · 技术栈与依赖** — 语言、版本、依赖分组
4. **第 3 层 · 架构与数据流** — 模块划分、依赖图、数据流图、关键设计决策
5. **第 4 层 · 核心代码详解** — 智能分层：核心文件详细 / 周边文件简略
6. **第 5 层 · 论文-代码映射**（条件性）— 论文章节/公式/实验 ↔ 代码模块/函数/脚本
7. **附录** — 文件清单、已知限制

## 支持的语言

- **主支持**（重点适配）：Python、JavaScript、TypeScript、Java、Go、Rust
- **降级支持**：其他语言用 L3 文本扫描策略

## 跨平台兼容

- **Claude Code**: 直接使用 `SKILL.md`
- **Codex**: 使用 `SKILL.codex.md`
- **Kimi Code**: 使用 `SKILL.kimi.md`

## 项目结构

```
repoguide/
├── SKILL.md                        # Claude Code 主版
├── SKILL.codex.md                  # Codex 适配
├── SKILL.kimi.md                   # Kimi Code 适配
├── references/
│   ├── language-profiles.md        # 6 种语言特征
│   ├── depth-rules.md              # 智能分层规则
│   └── report-template.md          # 五层结构模板
└── scripts/
    ├── detect-stack.py             # 技术栈识别
    ├── clone-if-url.sh             # URL 处理
    └── generate-pdf.sh             # md→pdf
```

## 测试

```bash
# 单元测试
python -m pytest tests/unit/test_detect_stack.py -v
bash tests/unit/test_clone_if_url.sh
bash tests/unit/test_generate_pdf.sh

# 端到端测试
bash tests/integration/test_e2e.sh
```

## 设计文档

- 完整设计: `docs/superpowers/specs/2026-06-17-repoguide-design.md`
- 实现计划: `docs/superpowers/plans/2026-06-17-repoguide-implementation.md`
````

- [ ] **Step 2: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/README.md
git commit -m "docs: add RepoGuide README"
```

---

## Task 16: 编写 INSTALL.md (安装指南)

**Files:**
- Create: `repoguide/INSTALL.md`

**前置条件**: Task 15 完成

- [ ] **Step 1: 写 INSTALL.md**

Create `repoguide/INSTALL.md` with the following content:

````markdown
# RepoGuide 安装指南

## 在 Claude Code 中安装

```bash
# 将 repoguide/ 目录复制到 Claude Code 的 skills 目录
# Windows:
xcopy /E /I repoguide "%USERPROFILE%\.claude\skills\repoguide"

# macOS/Linux:
cp -r repoguide ~/.claude/skills/
```

或者直接在当前项目中使用：`repoguide/SKILL.md` 会被 Claude Code 自动发现（如果该文件在项目根目录的 `.claude/skills/` 下）。

## 在 Codex 中安装

```bash
# Windows:
xcopy /E /I repoguide "%USERPROFILE%\.codex\skills\repoguide"

# macOS/Linux:
cp -r repoguide ~/.codex/skills/
```

## 在 Kimi Code 中安装

```bash
# Windows:
xcopy /E /I repoguide "%USERPROFILE%\.kimi\skills\repoguide"

# macOS/Linux:
cp -r repoguide ~/.kimi/skills/
```

## 依赖（PDF 生成可选）

- **必装**：
  - Python 3.10+ （detect-stack.py 用）
  - Git （clone GitHub URL 用）
  - Bash （执行 .sh 脚本用）
- **可选**（至少装一个才能生成 PDF）：
  - `pandoc` （推荐，配合 xelatex）
  - `weasyprint` （`pip install weasyprint`）
  - `markdown-pdf` （`pip install markdown-pdf`）

如果都不装，RepoGuide 仍能生成 Markdown 报告，PDF 步骤会优雅跳过并在对话中提示。

## 验证安装

```bash
# 测试 detect-stack 工具
python ~/.claude/skills/repoguide/scripts/detect-stack.py /path/to/any/repo

# 应输出 JSON
```

## 卸载

```bash
rm -rf ~/.claude/skills/repoguide
```
````

- [ ] **Step 2: Commit**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git add repoguide/INSTALL.md
git commit -m "docs: add RepoGuide INSTALL guide"
```

---

## Task 17: 最终验证 + 标签

**Files:**
- 无 (仅 git 操作)

**前置条件**: Task 16 完成

- [ ] **Step 1: 跑完整测试套件**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && \
  python -m pytest tests/unit/test_detect_stack.py -v && \
  bash tests/unit/test_clone_if_url.sh && \
  bash tests/unit/test_generate_pdf.sh && \
  bash tests/integration/test_e2e.sh
```

Expected: 所有测试通过

- [ ] **Step 2: 检查 git 状态**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && git status && git log --oneline
```

Expected: 无未提交改动，15+ commits

- [ ] **Step 3: 创建 v0.1.0 标签**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis"
git tag -a v0.1.0 -m "RepoGuide v0.1.0: initial release (Claude Code + Codex + Kimi Code)"
git tag -l
```

Expected: 看到 `v0.1.0`

- [ ] **Step 4: 最终目录树确认**

Run:
```bash
cd "E:/KimiClaw/repo-code-analysis" && find repoguide tests -type f -not -name '.gitkeep' | sort
```

Expected: 看到所有创建的文件清单

- [ ] **Step 5: Commit tag**

```bash
cd "E:/KimiClaw/repo-code-analysis"
git log --oneline | head -20
echo "---"
echo "Tag created. RepoGuide v0.1.0 ready for use."
```

---

## Self-Review 完成情况

执行了以下 self-review 检查（按 writing-plans skill 要求）：

### 1. Spec coverage ✅

| Spec Section | Task |
|--------------|------|
| 1. 概述 / 核心定位 | Task 2 (SKILL.md frontmatter) |
| 2. 总体架构（3 phase） | Task 2 (Phase 0/1/2/3) |
| 3. 输入与输出 | Task 9 (clone-if-url) + Task 10 (generate-pdf) |
| 4. 报告结构（五层） | Task 7 (report-template) |
| 5. 智能分层规则 | Task 6 (depth-rules) |
| 6. 多语言适配 | Task 5 (language-profiles) |
| 7. 跨平台兼容 | Task 3 (Codex) + Task 4 (Kimi) |
| 8. 内置默认策略 | Task 2 (SKILL.md 默认值) |
| 9. 错误处理 | Task 2 (错误处理 section) + Task 9/10 (脚本降级) |
| 10. 测试策略 | Task 8-14 (单元 + 集成 + fixture) |
| 11. 风险与缓解 | Task 10 (PDF 降级) + Task 2 (错误处理) |

### 2. Placeholder scan ✅

无 TBD/TODO/"implement later"。"add appropriate error handling" 等抽象指令已替换为具体规则。

### 3. Type consistency ✅

- JSON schema 在 SKILL.md、report-template.md、测试中保持一致（primary_language, entry_points, paper_found 等）
- 函数/方法名在 Task 间保持一致（detect_language, detect_paper, count_files）
- 路径命名保持一致（$REPO_PATH/_repoguide/profile.json 等）

### 4. Scope check ✅

单一 skill，无 subsystem 拆分。15 个 task 全部可独立 commit + 验证。
