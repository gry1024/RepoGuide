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

## 训练/实验入口脚本（强制核心）

以下脚本**一律视为核心文件，不得仅放入 scripts 清单**，需按"核心文件 → 详细分析"处理：

- `train_*.py`（如 `train_gfn.py`、`train_ppo.py`、`train_qcm.py`、`train_AFF.py`、`train_GP.py`）
- `run_*.py`（如 `run_adaptive_combination.py`）
- `combine_*.py`（如 `combine_AFF.py`）

这些脚本是理解仓库"如何运行/复现"的关键入口。

## 核心文件 → 详细分析 (必包含)

对每个核心文件输出结构化字段：

- **一句话作用** (≤ 30 字，中文)
- **类清单**：`[{name, line, signature, purpose}]`，`purpose` 不得为空、不得输出空字符串，必须中文
- **函数条目**：`[{name, line, signature, purpose, params:[{name,meaning}], returns, key_logic}]`
  - `purpose` 不得为空字符串，必须中文
  - `key_logic` 为 3-12 行原代码片段
- **入参/出参**：`params` 表 + `returns`
- **依赖关系**：该文件 import 哪些其他文件

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
