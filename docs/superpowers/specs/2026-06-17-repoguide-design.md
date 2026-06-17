# RepoGuide · 代码仓库分析 Skill 设计文档

**日期**：2026-06-17
**状态**：Design (待用户 review)
**作者**：RepoGuide 设计 brainstorm 产出

---

## 1. 概述

### 1.1 目标
构建一个名为 **RepoGuide** 的 agent skill。当用户给出一个代码仓库（本地路径或 GitHub URL）时，skill 自动端到端地分析其结构、架构、数据流、核心代码，并在检测到论文时关联论文-代码映射，最终输出**自顶向下五层结构的 Markdown + PDF 报告**。

### 1.2 核心定位
- **零澄清问题**：用户说"使用 RepoGuide skill 帮我分析仓库结构"后，端到端完成，不向用户追问
- **跨平台**：同时支持 Claude Code、Codex、Kimi Code 三种 agent 工具
- **多语言**：重点支持 Python / JavaScript / TypeScript / Java / Go / Rust，其他语言降级
- **论文感知**：检测到本地 PDF 时自动生成论文-代码映射章节

### 1.3 非目标
- 不做代码质量评分、安全审计、自动修复、重构建议
- 不依赖外部 API（除 `git clone` 外不主动联网）
- 不修改源文件（只读分析）

---

## 2. 总体架构

### 2.1 三 Phase 执行模型

```
Phase 0: 输入归一化
  - 本地路径 / GitHub URL / 当前目录自动识别
  - URL 场景：git clone --depth 1 到 /tmp/repoguide-<hash>/

Phase 1: 探查 (主 agent 串行)
  - 目录树扫描、技术栈识别、论文检测、入口识别
  - 产出 _repoguide/profile.json (仓库画像)

Phase 2: 并行深度分析 (派 4 个 subagent)
  - A: 架构与数据流
  - B: 核心代码详解
  - C: 论文解析 (条件性)
  - D: 论文-代码映射 (条件性, 依赖 C)

Phase 3: 汇总与输出 (主 agent 串行)
  - 整合 subagent 产出 → 五层结构 Markdown
  - 写入 <cwd>/repoguide-report.md
  - md → pdf → repoguide-report.pdf
  - 对话中输出摘要 + 文件路径
```

### 2.2 关键不变量
- Subagent 互不依赖，可真正并行
- 主 agent 持有仓库画像作为唯一可信源
- 报告永远是单一 Markdown 文件，结构固定

---

## 3. 输入与输出

### 3.1 输入形式
| 形式 | 例子 | 处理方式 |
|------|------|----------|
| 本地路径 | `/Users/me/projects/foo` | 直接使用 |
| GitHub URL | `https://github.com/foo/bar` | `git clone --depth 1` 到临时目录 |
| 隐式当前目录 | 用户在某个 git 仓库内说"分析仓库" | 探测当前目录 `.git` |

### 3.2 输出形式
- **主产物**：`./repoguide-report.md` (Markdown)
- **次产物**：`./repoguide-report.pdf` (PDF，由 md 转换)
- **对话摘要**：报告位置 + 五层结构的一句话总览

---

## 4. 报告结构（自顶向下五层）

### 第 0 层 · 元信息
- 仓库名 / 路径 / 主语言 / 许可证
- 代码量统计（行数、文件数，按语言分）
- 论文信息（如有）：标题、作者、本地 PDF 路径
- 生成时间、报告生成耗时

### 第 1 层 · 一句话总括 + 快速上手
- 一句话总括（这个项目是干什么的）
- 3 条命令上手（install / run / test）
- 5 个最关键的文件路径（带一句话说明）

### 第 2 层 · 技术栈与依赖
- 语言与版本
- 核心依赖（按用途分组）
- 包管理文件清单
- 外部服务依赖

### 第 3 层 · 架构与数据流
- **3.1 模块划分**：顶层目录→模块映射 + mermaid 模块依赖图
- **3.2 数据流**：从入口到输出的完整调用链 + mermaid 流程图 + 关键状态点
- **3.3 关键设计决策**：基于代码事实推断

### 第 4 层 · 核心代码详解（智能分层）
- **4.1 核心模块详细分析**（按"调用链上游→下游"顺序）
  - 每个核心文件：一句话作用、类/函数清单（带签名+行号）、关键逻辑解读（≤10 行/函数）、入参出参/副作用、依赖关系
- **4.2 周边模块简略清单**（表格：路径 | 一句话 | 重要度）
- **4.3 配置/脚本/资源**（配置项说明、脚本用途、数据/模型资源位置）

### 第 5 层 · 论文-代码映射（**仅当检测到论文时存在**）
- **5.1 论文速览**：标题、作者、核心贡献、章节结构（最多 5 级）
- **5.2 三层映射**：
  - 层级 1：论文章节 ↔ 代码模块
  - 层级 2：论文公式/算法 ↔ 代码函数/类
  - 层级 3：论文实验/表格 ↔ 评估脚本
- **5.3 关键术语对照表**

### 附录
- 文件清单（按扩展名分组）
- 已知限制 / 不确定项（LLM 无法 100% 判断的地方）

---

## 5. 智能分层规则

### 5.1 核心文件判定（5 条规则按权重合并）

| 规则 | 信号 | 权重 |
|------|------|------|
| ① 入口链追溯 | 从 main 入口沿 import/include 反向追踪能到达 | 高 |
| ② 配置显式声明 | 出现在 setup.py/package.json main/pyproject.toml/Cargo.toml [[bin]]/Makefile | 高 |
| ③ 模块入口命名 | `__init__.py`/`index.js|ts`/`mod.rs`/`main.go`/`app.py` | 中 |
| ④ 论文伪代码对应 | 论文 PDF 中提到的算法/类名/函数名能在代码匹配 | 中 |
| ⑤ 启发式补充 | 文件大小 > 中位数 3 倍 + 被 ≥ 5 个其他文件 import | 低 |

### 5.2 永远简略的类别
- `tests/`, `__tests__/`, `*_test.go`, `*.test.js|ts` → 一句话测试策略
- `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/` → 跳过
- `*.md`, `*.txt`, `LICENSE*`, `CHANGELOG*` → 仓库元信息
- `*.json`/`*.yaml`/`*.toml` → 第 4.3 节统一处理
- `*.lock`, `*.sum` → 跳过
- `.git/`, `.github/workflows/` → 不进代码层

### 5.3 规模自适应
- 总文件 < 50：所有非忽略文件按核心分析
- 总文件 50-500：按 5 条规则筛核心
- 总文件 > 500：核心文件上限 30 个（命中数+文件大小排序取 top 30）

---

## 6. 多语言适配

### 6.1 语言特征表

| 语言 | 包管理/依赖文件 | 入口识别 | 模块系统 | AST 提取 |
|------|----------------|----------|----------|----------|
| Python | `pyproject.toml`/`requirements*.txt`/`setup.py`/`Pipfile` | `[project.scripts]`/`__main__`/`entry_points` | import + package | Python 内置 `ast` |
| JavaScript | `package.json`/`yarn.lock`/`package-lock.json` | `package.json` `main`/`bin`、`index.js` | CJS + ESM | 正则 |
| TypeScript | `package.json` + `tsconfig.json` | 同 JS + `tsconfig` `outDir`/`rootDir` | ESM 为主 | 正则 + 提取 type 声明 |
| Java | `pom.xml`/`build.gradle*` | `@SpringBootApplication`/`public static void main`/Maven `<mainClass>` | package + import | `javap` 或正则 |
| Go | `go.mod`/`go.sum` | `package main` 中 `func main()` | package + import | `go/ast` 或正则 |
| Rust | `Cargo.toml`/`Cargo.lock` | `src/main.rs`/`src/lib.rs`/`[[bin]]` | crate + mod + use | `cargo`/`rustc --emit=metadata` 或正则 |

### 6.2 统一抽象层
所有语言抽出 4 类信息：
1. **入口清单**（含启动方式）
2. **模块依赖图**（节点=文件，边=import/include/require/use）
3. **类/函数/方法清单**（含签名+行号+一句话作用）
4. **关键数据流**（从入口出发跟踪主要调用链）

### 6.3 AST 提取降级
- L1：语言原生 AST 工具（Python `ast`、Go `go/ast`）
- L2：失败则用正则 + 启发式
- L3：再失败则按行扫描 + 标识符提取

### 6.4 多语言混合
按主语言切分"模块划分"，"数据流"章节专门标出跨语言边界。

---

## 7. 跨平台兼容

### 7.1 三平台适配

| 平台 | 触发方式 | Skill 文件格式 |
|------|----------|----------------|
| Claude Code | `/RepoGuide` 或自然语言 | `SKILL.md` + frontmatter |
| Codex | 自然语言 + 显式 skill 引用 | `SKILL.md` (放 `.codex/skills/`) |
| Kimi Code | 自然语言 + `activate_skill` | `SKILL.md` + Kimi frontmatter |

### 7.2 分发结构
```
RepoGuide/
├── SKILL.md                  # Claude Code 主版本
├── SKILL.codex.md            # Codex 适配
├── SKILL.kimi.md             # Kimi Code 适配
├── references/
│   ├── language-profiles.md  # 6 种语言特征表
│   ├── depth-rules.md        # 智能分层规则
│   └── report-template.md    # 五层结构模板
└── scripts/
    ├── clone-if-url.sh       # URL 检测+clone
    ├── generate-pdf.sh       # md → pdf
    └── detect-stack.py       # 技术栈识别
```

### 7.3 降级
- 平台不支持并行 subagent → 单 agent 顺序 + 报告元信息标注
- 无原生 AST → L2/L3 降级
- 无网络/无 git → 立即报错退出

---

## 8. 内置默认策略（"全自动"约束）

| 决策点 | 默认值 | 备注 |
|--------|--------|------|
| 输出格式 | 一次性完整报告 | 永远 |
| 论文来源 | 优先本地 PDF，否则扫 README/主页论文链接 | 永远 |
| 报告结构 | 五层（5 条件性） | 永远 |
| 粒度策略 | 智能分层 | 永远 |
| 涉及语言 | Python/JS/TS/Java/Go/Rust 主支持，其他降级 | 永远 |
| 论文映射深度 | 中度（三层） | 永远 |
| 执行架构 | 主 + 并行 subagent | 平台不支持时退化 |
| 报告保存位置 | `<cwd>/repoguide-report.{md,pdf}` | 永远 |
| 报告语言 | 与用户交互语言一致（默认中文） | 英文输入→英文 |

---

## 9. 错误处理

| 错误 | 行为 | 报告体现 |
|------|------|----------|
| 路径不存在 | 立即终止 | 无报告 |
| URL 无效/clone 失败 | 终止，给清晰错误 | 无报告 |
| 仓库为空 | 终止 | 无报告 |
| 单个文件读取失败 | 跳过 | 已知限制附录 |
| 论文 PDF 损坏 | C/D subagent 跳过 | 第 5 层不出现 + 元信息标注 |
| md→pdf 失败 | 报告仍生成 | 对话中提示安装 pandoc |
| Subagent 失败 | 主 agent 重试 1 次，仍失败则继续 | 已知限制附录 |
| 不支持语言 | 降级 L3 | 元信息标注 |
| 上下文溢出 | 增量处理：先高层再深入 | 报告元信息标注"分段生成" |

**核心原则**：能降级就降级，能跳过就跳过。报告永远尽力产出，除非连仓库都进不去。

---

## 10. 测试策略

### 10.1 单元测试（针对 scripts/）
- `clone-if-url.sh`：本地路径 / URL / 错误 URL / 当前目录
- `detect-stack.py`：6 种语言各 1 fixture
- `generate-pdf.sh`：纯文本 / 含 mermaid / 含代码块 / 含表格

### 10.2 集成测试（端到端）
- 3 个不同规模 fixture：小型(<30)、中型(50-500)、大型(>1000)
- 3 个论文代码 fixture
- 1 个多语言混合 fixture

### 10.3 质量验证（人评）
- 报告第 1 层"一句话总括"是否准确
- 第 3 层"数据流图"和实际执行流是否一致
- 第 5 层"论文-代码映射"是否被作者认可

---

## 11. 风险与缓解

| 风险 | 缓解 |
|------|------|
| LLM 对代码意图理解错 | 已知限制附录 + 置信度标注 |
| 巨型仓库 token 超限 | 规模自适应 + 分段生成 |
| 论文-代码映射牵强 | 中度映射（不做反向追溯）+ 承认限制 |
| 跨平台差异 | 三套 SKILL.md + 显式降级 |
| PDF 工具链依赖 | 三层降级（pandoc → weasyprint → 仅 md） |

---

## 12. 后续步骤

本设计文档经用户 review 通过后，将进入 **writing-plans** 阶段，产出 RepoGuide 的实现计划（包含：Skill 文件分平台生成、references 文档、scripts 脚本、测试 fixture、CI 集成等任务的拆分）。
