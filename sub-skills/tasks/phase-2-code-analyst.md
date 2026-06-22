---
name: repoguide-task-phase-2-code-analyst
description: RepoGuide Phase 2b：代码详解。创建 code-analyst agent，按 depth 规则详尽分析核心文件与所有文件。
---

# Phase 2b: 代码详解

## 执行方式

创建 **code-analyst** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_code.json
```

## 任务

1. 读取 `profile.json`（注意 `depth` 字段与 `core_files_seed`）。
2. 按 `references/depth-rules.md` 和 `depth` 判定核心文件与周边文件。
3. 对每个核心文件完整 Read，提取：
   - 一句话作用
   - 类/函数/方法清单（签名 + 行号 + 作用）
   - 关键逻辑（3-10 行/函数）
   - 依赖关系
4. 对周边文件生成简略清单。
5. 输出 `directory_tree`。

## 按 depth 调整范围

### standard

- 读取**核心模块文件**（按 `references/depth-rules.md` 得分 ≥ 5 的核心文件）。
- 输出**核心目录**的 tree 风格目录树。
- 解析关键类/函数，不必覆盖每个小函数。
- 简略清单覆盖仓库 80% 的非忽略文件路径。

### deep

- **面面俱到**：读取**所有非忽略文件**（核心文件 + 测试/配置/脚本/资源）。
- 输出**完整目录树**，每个核心文件带注释。
- **每个类/函数都带说明**：
  - 类：职责、关键方法、继承/组合关系
  - 函数：签名、行号、参数/返回值/副作用、关键逻辑
- 对测试文件概括测试策略，对配置文件说明作用，对脚本说明用途。
- 任何无法静态分析的动态特性写入 `limitation_notes`。

## 输出 JSON

```json
{
  "core_files": [
    {
      "path": "...",
      "one_liner": "...",
      "classes": [
        {"name": "...", "line": 0, "signature": "...", "purpose": "..."}
      ],
      "functions": [
        {"name": "...", "line": 0, "signature": "...", "key_logic": "...", "params": [...], "returns": "...", "side_effects": "..."}
      ],
      "dependencies": ["..."]
    }
  ],
  "peripheral_files": [
    {"path": "...", "importance": "high|medium|low", "one_liner": "..."}
  ],
  "config_files": [
    {"path": "...", "purpose": "..."}
  ],
  "scripts": [
    {"path": "...", "purpose": "..."}
  ],
  "resources": [
    {"path": "...", "purpose": "..."}
  ],
  "test_strategy": "一句话概括",
  "directory_tree": "字符串形式的目录树，deep 必填完整树，standard 为核心目录",
  "limitation_notes": []
}
```

## 注意事项

- 严格遵循 `references/depth-rules.md` 中的"永远简略的类别"，不将 node_modules、vendor、构建产物等纳入分析。
- deep 模式下，不得因文件数量多而跳过任何非忽略文件；若因工具限制无法全部读取，写入 `limitation_notes`。
- 行号必须尽量准确，便于 writer 在手册中定位。

## 下一 Phase

本 Phase 与 [phase-2-architect.md](phase-2-architect.md) 并行执行。
