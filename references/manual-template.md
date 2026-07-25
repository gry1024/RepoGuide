# 仓库手册指南模板（面向人 · 全中文 · 概念驱动）

writer agent 按本模板组装 Markdown 内容。**唯一读者是人**：一切叙述须简体中文，让人最快掌握结构、架构、核心概念与代码-论文映射。

输入 JSON：
- `profile.json`
- `analysis_arch.json`（含 `annotated_tree`、`architecture_overview_dot`、`data_flow_narrative`、`data_flow_table`）
- `analysis_code.json`（含 `core_files`、`peripheral_files`、`config_files`、`scripts`、`resources`）
- `analysis_concepts.json`（Phase 2c 产物，含 `concepts`、`concept_relations`、`concept_map_dot`、`reading_path`）
- `analysis_paper.json`（可选）
- `analysis_map.json`（可选）
- `image-manifest.json`（可选）

## 排版硬规则

1. **概念驱动**：代码详解不得平铺所有文件所有函数。先讲核心概念（含类比、教学顺序），明星函数展开 key_logic，其余函数折叠进 `<details>` 或附录表格。
2. 目录树必须每行带 `# 中文用途注释`（≤ 30 字），无注释的行不得出现。
3. 类/函数一律输出签名代码块、一句话中文职责、参数表、返回值与关键逻辑片段（≤ 8 行）。
4. 论文公式用 `$$...$$` 块，公式编号用 `\tag{n}`。术语表、映射表用 Markdown 表格。
5. 图片引用前必须有中文图注段落；图片路径用相对路径 `images/xxx.png`。
6. 架构总览图、概念关系图均由 graphviz 生成，分别引用 `images/architecture_overview.png` 与 `images/concept_map.png`。
7. 全文不出现英文整句；专有名词（GFlowNet、RGCN、PPO、Qlib 等）可保留原文。
8. 概念章节按 `teaching_order` 升序排列，由浅入深。

## 三层结构总览

| 层 | 章节 | 目标 | 读者动作 |
|----|------|------|----------|
| 概念导览层 | 四、核心概念导览 | 建立直觉，看懂"是什么、为什么" | 5 分钟通读 |
| 文件速览层 | 五、文件速览表 | 一张表看完所有核心文件职责 | 扫一眼定位 |
| 深入详解层 | 六、明星函数深入 + 折叠区 | 只看关键函数 key_logic，其余折叠 | 按需展开 |

## 模板内容

```markdown
# {{repo_name}} 仓库手册指南

> 由 RepoGuide 自动生成于 {{generated_at}}
> 仓库路径：`{{repo_path}}`
> 分析档位：{{depth}}　生成耗时：{{duration}}

---

## 一、一页速览

> **一句话总括**：{{one_liner}}

| 项 | 值 |
|----|----|
| 主语言 | {{primary_language}} |
| 文件总数 | {{file_count_total}} |
| 论文 | {{paper_found ? "已配套" : "未配套"}} |
| 核心入口 | {{entry_points_short}} |

### 三条命令上手

```bash
# 安装
{{install_cmd}}

# 训练/运行
{{run_cmd}}

# 测试/评估
{{test_cmd}}
```

### 推荐阅读路径

> 按以下顺序建立直觉：{{reading_path_names}}

| 序 | 概念 | 类比 | 一句话职责 |
|----|------|------|------------|
| 1 | {{concept_name_1}} | {{analogy_1}} | {{summary_1}} |
| ... | ... | ... | ... |

---

## 二、技术栈与依赖

（同原模板，略）

---

## 三、架构与数据流

### 3.1 架构总览图

![{{repo_name}} 架构总览](images/architecture_overview.png)

> 图 1：分层架构与数据流转总览（graphviz 生成，按层着色）。

### 3.2 注释化目录树

> 每一行末尾 `#` 后为该文件/目录的中文用途说明。{{depth}} 模式。

```text
{{annotated_tree}}
```

### 3.3 数据流叙述

{{data_flow_narrative}}

#### 数据流转表

| 步骤 | 输入 | 处理模块 | 输出 | 关键文件 |
|------|------|----------|------|----------|
{{#each data_flow_table}}
| {{step}} | {{input}} | {{module}} | {{output}} | `{{file}}` |
{{/each}}

### 3.4 关键设计决策

{{#each design_decisions}}
#### {{decision}}

- **证据**：`{{evidence}}`
- **理由**：{{reasoning}}
{{/each}}

---

## 四、核心概念导览

> 本章是理解本仓库的"地图"。先看概念关系图，再按教学顺序逐个理解核心概念，每个概念附类比、关联文件、明星函数与论文公式。

### 4.1 概念关系图

![{{repo_name}} 概念关系图](images/concept_map.png)

> 图 2：核心概念间的依赖与数据流向（graphviz 生成，按 layer 着色：橙=数据配置，蓝=核心算法，绿=训练评估）。

### 4.2 概念卡片（按教学顺序）

{{#each concepts_sorted_by_teaching_order}}
### 概念 {{teaching_order}}：{{name}}

> **类比**：{{analogy}}

- **是什么**：{{summary}}
- **所属层**：{{layer}}
- **关联文件**：{{#each related_files}}`{{this}}` {{/each}}

#### 明星函数

{{#each star_functions}}
##### `{{function}}`

- **位置**：`{{file}}:{{line}}`
- **为何重要**：{{why_star}}

```python
{{key_logic}}
```
{{/each}}

{{#if related_formulas}}
#### 关联公式

{{#each related_formulas}}
$$
{{this}}
$$
{{/each}}
{{/if}}

---
{{/each}}

---

## 五、文件速览表

> 一张表看完所有核心文件的职责与归属概念。需要深入时再跳到第六章对应函数。

| # | 文件 | 一句话职责 | 类数 | 函数数 | 所属概念 |
|---|------|------------|------|--------|----------|
{{#each core_files}}
| {{index}} | `{{path}}` | {{one_liner}} | {{class_count}} | {{func_count}} | {{concept_names}} |
{{/each}}

### 周边文件清单

| 路径 | 用途 | 重要度 |
|------|------|--------|
{{#each peripheral_files}}
| `{{path}}` | {{one_liner}} | {{importance}} |
{{/each}}

### 配置 / 脚本 / 资源

（同原模板，略）

---

## 六、明星函数深入详解

> 仅展开第四章各概念挑选的明星函数（共 {{star_func_count}} 个），附完整 key_logic。其余函数见附录"全函数索引表"或仓库源码。

{{#each concepts}}
### {{name}} · 明星函数

{{#each star_functions}}
#### `{{function}}`

```python
{{signature}}
```

- **职责**：{{purpose}}
- **参数**：{{#each params}}`{{name}}`：{{meaning}}；{{/each}}
- **返回**：{{returns}}
- **关键逻辑**：

```python
{{key_logic}}
```

{{/each}}
{{/each}}

---

## 七、其余函数折叠区

> 以下为核心文件中非明星函数的索引，按文件分组。完整 key_logic 见仓库源码。

<details>
<summary>点击展开全部函数索引（{{total_non_star_funcs}} 个）</summary>

{{#each core_files}}
#### `{{path}}`

| 函数 | 行号 | 职责 |
|------|------|------|
{{#each functions}}
| `{{name}}` | {{line}} | {{purpose}} |
{{/each}}

{{/each}}

</details>

---

{{#if paper_found}}
## 八、论文—代码映射

### 8.1 论文速览

- **标题**：{{paper_title}}
- **作者**：{{paper_authors}}

**核心贡献**：

{{#each paper_core_contributions}}
- {{this}}
{{/each}}

### 8.2 关键公式

{{#each paper_key_formulas}}
$$
{{latex}}
$$

> 公式 {{index}}：{{meaning}}
{{/each}}

### 8.3 论文—代码三层映射

（同原模板：层级 1/2/3 表格，略）

### 8.4 论文原图与仓库关键图

{{#each paper_figures}}
**图 {{index}}：{{caption}}**

![{{caption}}]({{path}})
{{/each}}

### 8.5 术语对照表

| 论文术语 | 代码标识符 | 含义 |
|----------|------------|------|
{{#each paper_glossary}}
| {{term}} | `{{code_identifier}}` | {{description}} |
{{/each}}
{{/if}}

---

## 附录

### 全函数索引表

> 所有核心文件的所有函数索引（含明星与非明星），按文件分组。

{{#each core_files}}
#### `{{path}}`

| 函数 | 行号 | 职责 | 明星？ |
|------|------|------|--------|
{{#each functions}}
| `{{name}}` | {{line}} | {{purpose}} | {{is_star ? "★" : ""}} |
{{/each}}

{{/each}}

### 文件清单（按扩展名分组）

{{#each file_groups}}
- **{{ext}}**（{{count}} 个）：{{sample_paths}}
{{/each}}

### 已知限制 / 不确定项

{{#each limitation_notes}}
- {{this}}
{{/each}}

### 生成信息

- 生成时间：{{generated_at}}
- 总耗时：{{duration}}
- 执行模式：{{execution_mode}}
- 核心概念数：{{concept_count}}
- 明星函数数：{{star_func_count}}
- 降级情况：{{degradation_notes}}
```

## writer 组装规则

1. 读取 `profile.json` + `analysis_*.json`（含 `analysis_concepts.json`）+ `image-manifest.json`。
2. **第 1 层（速览）的"推荐阅读路径"**：从 `analysis_concepts.json.reading_path` 取概念 id 序列，映射为概念名表格。
3. **第四章（核心概念导览）**：按 `teaching_order` 升序渲染概念卡片。每张卡片含类比、summary、关联文件、明星函数（带 key_logic）、关联公式。
4. **第五章（文件速览表）**：所有核心文件一张表，含 `所属概念` 列（从 `analysis_concepts.json` 反查每个文件属于哪个概念）。
5. **第六章（明星函数深入）**：仅渲染 `star_functions`，带完整 key_logic。
6. **第七章（折叠区）**：用 `<details><summary>` 包裹非明星函数索引表。
7. **附录全函数索引表**：所有函数索引，标记明星（★）。
8. **概念关系图**：引用 `images/concept_map.png`（由 image-handler 从 `concept_map_dot` 渲染）。若图缺失，改用概念关系表格替代并记录限制。
9. **公式**：论文公式以 `$$...$$` 写入，保留原始 LaTeX；writer 不得对公式内容做转义。
10. **全中文校验**：写完 `manual.md` 后，调用 `sub-skills/tools/manual-quality-checker.md` 扫描英文整句；若有违规项，改写为中文后重新检查。
11. 缺失字段留空并在附录"已知限制"标注。
12. 输出到 `$WORK_DIR/manual.md`。

## 降级策略

- `analysis_concepts.json` 缺失或解析失败：回退到原"按文件平铺"模式（第四章=核心代码详解），在 `limitation_notes` 记录"概念层缺失，代码详解按文件平铺"。
- `concept_map.png` 渲染失败：第四章用概念关系表格（from→to+label）替代图片。
- 明星函数 key_logic 缺失：显示签名+职责，标注"key_logic 未提取"。
