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
