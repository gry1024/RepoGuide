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

## 手册结构（三层，与模板一致）

1. 一页速览（一句话 + 命令 + 推荐阅读路径）
2. 技术栈与依赖
3. 架构与数据流（总览图 + 注释化目录树 + 数据流叙述 + 流转表 + 设计决策）
4. **核心概念导览**（概念关系图 + 概念卡片按教学顺序）
5. **文件速览表**（所有核心文件 + 所属概念 + 周边文件）
6. **明星函数深入详解**（仅明星函数，带 key_logic）
7. **其余函数折叠区**（`<details>` 包裹非明星函数索引）
8. 论文—代码映射（可选：速览 + 公式 + 三层映射 + 论文原图 + 术语表）
9. 附录（全函数索引表 + 文件清单 + 已知限制 + 生成信息）

## 按 depth 调整内容

### standard
- 注释化目录树为核心目录。
- 核心代码详解聚焦核心文件。
- 论文部分仅主要章节与公式。

### deep
- 完整注释化目录树。
- 核心代码详解覆盖所有核心文件，每个类/函数。
- 论文逐章映射 + 论文原图 + 术语表。

## 输出校验

```python
validate_file_exists("$WORK_DIR/manual.md", min_bytes=100)
```

附加检查：手册须含"一、一页速览"、"三、架构与数据流"、"四、核心代码详解"标题；目录树代码块内 ≥ 80% 行含 ` # `。

## 下一 Phase

完成后进入 [phase-5-renderer.md](phase-5-renderer.md)。
