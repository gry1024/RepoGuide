---
name: repoguide-task-phase-4
description: RepoGuide Phase 4：手册组装。按面向人、全中文模板生成 manual.md。
---

# Phase 4: 手册组装

## 执行方式

创建 **writer** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json + analysis_arch.json + analysis_code.json + analysis_concepts.json(Phase 2c) + analysis_paper.json(可选) + analysis_map.json(可选) + image-manifest.json(可选)
输出: $WORK_DIR/manual.md
```

## 任务

1. 读取所有分析产物（**含 `analysis_concepts.json`**）与 `image-manifest.json`。
2. 严格按 `references/manual-template.md` 的**三层结构**（概念导览 → 文件速览 → 明星函数深入 → 折叠区）组装。
3. **第 1 层（一页速览）**：一句话总括、三条命令、推荐阅读路径（取自 `analysis_concepts.json.reading_path`）。
4. **第四章（核心概念导览）**：按 `teaching_order` 升序渲染概念卡片，每张含类比、summary、关联文件、明星函数（带 key_logic）、关联公式。引用 `images/concept_map.png`。
5. **第五章（文件速览表）**：所有核心文件一张表，含"所属概念"列（反查 `analysis_concepts.json`）。
6. **第六章（明星函数深入）**：仅渲染各概念的 `star_functions`，带完整 key_logic（≤ 8 行）。
7. **第七章（折叠区）**：用 `<details><summary>` 包裹非明星函数索引表。
8. **附录全函数索引表**：所有函数索引，明星标记 ★。
9. **架构总览图**：引用 `images/architecture_overview.png`。若图缺失，用数据流叙述替代并记录限制。
10. **注释化目录树**：直接取 `analysis_arch.json.annotated_tree`，不得删注释。
11. **论文公式**：以 `$$...$$` 写入，保留原始 LaTeX，不得转义。
12. **全中文校验**：写完后调用 `sub-skills/tools/manual-quality-checker.md` 的英文整句扫描逻辑；若发现违规项，必须改写为中文后重新检查。
13. 写入 `$WORK_DIR/manual.md`。

## 降级策略

- `analysis_concepts.json` 缺失或解析失败：回退到原"按文件平铺"模式（第四章=核心代码详解，按文件分章），在 `limitation_notes` 记录"概念层缺失，代码详解按文件平铺"。
- `concept_map.png` 缺失：第四章用概念关系表格（from→to+label）替代图片。

## 手册结构（章节式，参考 PocketFlow）

输出到 `outputs/<repo_name>/` 目录，每个概念一个独立 .md 文件：

### index.md（首页）
1. 项目简介（一句话总括 + 关键信息表）
2. 概念关系图（`images/concept_map.png`）
3. 目录（按教学顺序，每章含链接 + 一句话摘要）
4. 数据流总览
5. 目录结构（注释化目录树）
6. 论文速览（可选）

### 每个概念文件（01_<概念名>.md ~ N）
1. 章节标题（第 N 章：概念名）
2. 欢迎引导（"欢迎来到第 N 章！本章将带你理解 xxx"）
3. **它解决什么问题？**（类比 + summary）
4. **明星函数**（每个含位置、为何重要、key_logic 代码块）
5. **关联公式**（`$$...$$`）
6. **关联文件**（表格）
7. 前后导航（← 上一章 | 目录 | 下一章 →）

### 99_附录_全函数索引.md
所有核心文件的函数索引表，明星函数标 ★。

## 按 depth 调整内容

### standard
- 5-8 个概念章节
- 注释化目录树为核心目录
- 论文部分仅主要章节与公式

### deep
- 8-12 个概念章节
- 完整注释化目录树
- 论文逐章映射 + 论文原图 + 术语表

## 输出校验

```python
# 检查 outputs/<repo_name>/ 目录结构
import os
out_dir = f"outputs/{repo_name}"
assert os.path.exists(f"{out_dir}/index.md")
assert len([f for f in os.listdir(out_dir) if f.endswith('.md')]) >= 5
assert os.path.exists(f"{out_dir}/images")
```

附加检查：index.md 须含项目简介、目录、概念关系图；每个概念文件须含"明星函数"和前后导航；目录树代码块内 ≥ 80% 行含 ` # `。

## 下一 Phase

完成后进入 [phase-5-renderer.md](phase-5-renderer.md)。
