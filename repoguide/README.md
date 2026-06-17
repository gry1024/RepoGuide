# RepoGuide

> **拿到一个陌生代码仓库，5 分钟理解它。**
> 一句命令，端到端分析，产出含架构图、数据流、核心代码详解、论文-代码映射的五层结构报告（Markdown + PDF）。

---

## 它是什么

**RepoGuide** 是一个 Agent Skill —— 当你给一个 LLM 编程助手（Claude Code / Codex / Kimi Code）下达指令时，它会自动：

1. **读仓库** —— 扫目录、识别语言、检测论文
2. **并行深度分析** —— 架构、数据流、核心代码、论文映射
3. **输出报告** —— 自顶向下五层结构的 Markdown + PDF

**典型场景**：
- 刚 clone 下来一个陌生仓库，想快速看懂
- 拿到一篇论文的代码，想知道"代码哪里对应论文哪里"
- 接手同事的项目，需要交接文档
- 评估一个开源项目，决定要不要用

**你不需要**：自己读所有文件、画架构图、写 README、写 wiki。
**你只需要**：说一句"使用 RepoGuide skill 帮我分析仓库结构"。

---

## 安装（30 秒）

### 1. 选择平台

RepoGuide 适配三个 agent 编程工具：

| 工具 | 安装路径 |
|------|----------|
| **Claude Code** | `~/.claude/skills/repoguide/` |
| **Codex** | `~/.codex/skills/repoguide/` |
| **Kimi Code** | `~/.kimi/skills/repoguide/` |

### 2. 复制 skill 目录

```bash
# macOS / Linux
cp -r repoguide ~/.claude/skills/    # 或 .codex / .kimi

# Windows
xcopy /E /I repoguide %USERPROFILE%\.claude\skills\repoguide
```

### 3.（可选）安装 PDF 依赖

Markdown 报告永远能生成。PDF 需要以下之一：

```bash
# 推荐
brew install pandoc mactex           # macOS
sudo apt install pandoc texlive-xetex  # Linux

# 或 Python 方案
pip install weasyprint
```

如果都不装，PDF 步骤会优雅跳过，Markdown 仍可用。

### 4. 验证安装

```bash
python ~/.claude/skills/repoguide/scripts/detect-stack.py /path/to/any/repo
# 应输出 JSON
```

---

## 使用（3 步）

### 步骤 1：进入仓库目录（或跳过，进入步骤 2 时给路径/URL）

```bash
cd ~/projects/some-unfamiliar-repo
```

### 步骤 2：触发 skill

对你用的 agent 说：

```
使用 RepoGuide skill 帮我分析仓库结构
```

或显式给路径 / GitHub URL：

```
使用 RepoGuide skill 帮我分析 /path/to/repo
使用 RepoGuide skill 分析 https://github.com/owner/repo
```

### 步骤 3：等报告

skill 端到端执行，**不会问任何问题**。完成后输出：

- `<当前目录>/repoguide-report.md` — Markdown 报告
- `<当前目录>/repoguide-report.pdf` — PDF 报告（如已装 pandoc/weasyprint）

对话中也会给出报告摘要 + 文件路径。

---

## 报告长什么样

报告是**自顶向下五层结构**：

| 层 | 章节 | 你能获得什么 |
|----|------|--------------|
| **0** | 元信息 | 仓库大小、用了什么语言、有没有论文 |
| **1** | 一句话总括 + 快速上手 | 3 条命令跑起来，5 个最关键文件 |
| **2** | 技术栈与依赖 | 装了什么、为什么装、外部依赖是什么 |
| **3** | 架构与数据流 | mermaid 模块依赖图 + 数据流图 + 关键设计决策 |
| **4** | 核心代码详解 | 智能分层：核心文件每个类/函数都讲清楚，周边文件一句话带过 |
| **5** | 论文-代码映射 *(仅当仓库有论文 PDF 时)* | 论文章节/公式/实验 ↔ 代码模块/函数/脚本 三层映射 |
| 附录 | 文件清单、已知限制 | 哪些文件没分析到、哪些 LLM 推断可能不准 |

---

## 它支持什么

### 语言
重点支持：**Python、JavaScript、TypeScript、Java、Go、Rust**
其他语言会降级到文本扫描（仍能用，质量下降）

### 论文检测
自动检测仓库里的：
- `*.pdf` 文件
- `*.tex` 文件
- `paper*` 命名的文件
- README 里的 arxiv 链接

### 平台
- ✅ **Claude Code** (主版)
- ✅ **Codex** (适配版)
- ✅ **Kimi Code** (适配版，串行降级模式)

---

## 它**不**做什么

明确**不**做：
- ❌ 不修改任何源文件（只读）
- ❌ 不做代码质量评分 / 安全审计
- ❌ 不做自动修复 / 重构建议
- ❌ 不联网搜索（除 git clone 之外）
- ❌ 不向用户追问任何问题

如果你需要这些，请用别的工具。

---

## 工作原理（好奇的话可以看）

```
你: "使用 RepoGuide skill 帮我分析仓库"
    ↓
Phase 0:  输入归一化（路径/URL → 本地目录）
Phase 1:  探查（技术栈、论文、入口）
Phase 2:  并行 4 个 subagent（架构/代码/论文/映射）
Phase 3:  汇总五层结构 → 写 Markdown → 转 PDF
```

详见 [`docs/superpowers/specs/2026-06-17-repoguide-design.md`](docs/superpowers/specs/2026-06-17-repoguide-design.md)。

---

## 自己开发 / 改

```bash
# 单元测试
python -m pytest tests/unit/test_detect_stack.py -v
bash tests/unit/test_clone_if_url.sh
bash tests/unit/test_generate_pdf.sh

# 端到端测试
bash tests/integration/test_e2e.sh
```

skill 的"核心"是 [`repoguide/SKILL.md`](repoguide/SKILL.md) —— 一个 prompt 模板，告诉 agent 在每个 Phase 做什么。

---

## License

MIT
