import json
import re
from pathlib import Path
from typing import Optional

import pytest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def extract_python_block(markdown: str, marker: Optional[str] = None) -> str:
    blocks = re.findall(r"```python\n(.*?)\n```", markdown, flags=re.S)
    if marker is None:
        assert blocks, "expected at least one python code block"
        return blocks[0]
    for block in blocks:
        if marker in block:
            return block
    raise AssertionError(f"missing python block marker: {marker}")


def test_detect_stack_preserves_phase0_repo_name_and_promotes_research_entrypoints(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "_repoguide" / "repo"
    repo.mkdir(parents=True)
    work_dir = tmp_path / "_repoguide"

    (repo / "README.md").write_text("# AlphaSAGE\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='alphasage'\n", encoding="utf-8")
    for name in [
        "train_gfn.py",
        "train_ppo.py",
        "train_qcm.py",
        "train_AFF.py",
        "train_GP.py",
        "run_adaptive_combination.py",
        "combine_AFF.py",
    ]:
        (repo / name).write_text("def main():\n    pass\n", encoding="utf-8")

    (work_dir / "profile.json").write_text(
        json.dumps(
            {
                "repo_path": str(repo),
                "work_dir": str(work_dir),
                "analysis_mode": "clone",
                "repo_name": "AlphaSAGE",
                "repo_ref": "https://github.com/BerkinChen/AlphaSAGE.git",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    code = extract_python_block(read_rel("sub-skills/tools/detect-stack.md"))
    code = re.sub(
        r'REPO_PATH = Path\("/path/to/repo"\)\.resolve\(\)',
        lambda _m: f"REPO_PATH = Path({str(repo)!r}).resolve()",
        code,
    )

    monkeypatch.setenv("WORK_DIR", str(work_dir))
    monkeypatch.setenv("REPOGUIDE_DEPTH", "deep")
    exec(compile(code, "detect-stack.md", "exec"), {})
    capsys.readouterr()

    profile = json.loads((work_dir / "profile.json").read_text(encoding="utf-8"))
    assert profile["repo_name"] == "AlphaSAGE"
    assert profile["repo_ref"] == "https://github.com/BerkinChen/AlphaSAGE.git"

    for expected in ["train_ppo.py", "train_qcm.py", "train_AFF.py", "train_GP.py"]:
        assert expected in profile["entry_points"]
        assert expected in profile["core_files_seed"]
    assert "run_adaptive_combination.py" in profile["entry_points"]


def test_image_manifest_reconciliation_records_existing_paper_images_and_removes_stale_limitation(tmp_path, monkeypatch):
    work_dir = tmp_path / "_repoguide"
    images = work_dir / "images"
    images.mkdir(parents=True)
    (images / "paper_p5_img1.png").write_bytes(b"\x89PNG\r\n\x1a\nsample")
    (work_dir / "image-manifest.json").write_text(
        json.dumps(
            {
                "paper_figures": [],
                "repo_figures": [],
                "generated_diagrams": [],
                "limitations": ["论文原图未从 PDF 中提取。"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    code = extract_python_block(
        read_rel("sub-skills/tools/image-handler.md"),
        "REPOGUIDE_IMAGE_MANIFEST_RECONCILE_START",
    )
    monkeypatch.setenv("WORK_DIR", str(work_dir))
    exec(compile(code, "image-handler.md", "exec"), {})

    manifest = json.loads((work_dir / "image-manifest.json").read_text(encoding="utf-8"))
    assert manifest["paper_figures"] == [
        {
            "path": "images/paper_p5_img1.png",
            "page": 5,
            "caption": "论文第 5 页图 1",
            "size": 14,
        }
    ]
    assert not any("论文原图未从 PDF 中提取" in item for item in manifest["limitations"])


def test_image_handler_contains_image_optimization_contract():
    text = read_rel("sub-skills/tools/image-handler.md")
    assert "REPOGUIDE_IMAGE_OPTIMIZE_START" in text
    assert "MAX_W" in text or "max_width" in text
    assert "MAX_H" in text
    assert "optimized_images" in text


def test_latex_renderer_preserves_math_and_adapts_image_size():
    text = read_rel("sub-skills/tools/latex-renderer.md")
    # 数学段必须被保护，不得把 $ 转义为 \$
    assert "占位符保护" in text or "stash_math" in text
    assert "keepaspectratio" in text  # 自适应尺寸
    # 模板须含 amsmath
    assert "amsmath" in read_rel("references/latex-template/main.tex")


def test_architect_uses_annotated_tree_and_graphviz_not_mermaid_trees():
    text = read_rel("sub-skills/tasks/phase-2-architect.md")
    assert "annotated_tree" in text
    assert "architecture_overview_dot" in text
    assert "rankdir=LR" in text
    assert "cluster_" in text
    # 废弃树状 mermaid 依赖/数据流图
    assert "module_dependency_graph" not in text
    assert "data_flow_graph" not in text


def test_code_analyzer_forbids_empty_symbol_descriptions_and_uses_purpose_schema():
    text = read_rel("sub-skills/tools/code-analyzer.md") + read_rel("sub-skills/tasks/phase-2-code-analyst.md")
    assert "不得输出空字符串" in text
    assert '"purpose"' in text
    assert '"key_logic"' in text
    assert '"description": ""' not in text


def test_depth_rules_treat_training_and_experiment_scripts_as_core_files():
    text = read_rel("references/depth-rules.md")
    assert "训练/实验入口脚本" in text
    assert "train_*.py" in text
    assert "run_*.py" in text
    assert "不得仅放入 scripts 清单" in text


def test_template_enforces_chinese_and_card_layout():
    text = read_rel("references/manual-template.md")
    assert "全中文" in text
    assert "卡片" in text
    assert "annotated_tree" in text or "注释化目录树" in text
    # 论文公式以 $$ 写入
    assert "$$" in text
    visible_template = text.split("## writer 组装规则", 1)[0]
    forbidden = [
        "## 四、核心代码详解（卡片式）",
        "每个核心文件一张",
        "函数签名+职责+参数+关键逻辑",
        "`key_logic` 超",
    ]
    for phrase in forbidden:
        assert phrase not in visible_template


def test_manual_quality_checker_rejects_reader_facing_meta_instructions():
    text = read_rel("sub-skills/tools/manual-quality-checker.md")
    assert "find_reader_facing_meta_violations" in text
    assert "每个核心文件一张卡片" in text
    assert "key_logic" in text
    assert "卡片式" in text


def test_tracked_alphasage_samples_do_not_include_writer_meta_instructions():
    sample_paths = [
        "AlphaSAGE-manual/AlphaSAGE-standard-manual.md",
        "AlphaSAGE-manual/AlphaSAGE-deep-manual.md",
        "AlphaSAGE-manual/AlphaSAGE-standard-manual.html",
        "AlphaSAGE-manual/AlphaSAGE-deep-manual.html",
    ]
    forbidden = [
        "核心代码详解（卡片式）",
        "每个核心文件一张卡片",
        "标题带一句话职责",
        "函数签名+职责+参数+关键逻辑",
        "key_logic",
    ]
    for path in sample_paths:
        text = read_rel(path)
        for phrase in forbidden:
            assert phrase not in text


def test_depth_confirmation_is_required_across_runtime_docs():
    skill = read_rel("skill.md")
    index = read_rel("sub-skills/tasks/_index.md")
    phase0 = read_rel("sub-skills/tasks/phase-0-normalize.md")
    codex = read_rel("sub-skills/runtime/codex-subagent.md")

    combined = "\n".join([skill, index, phase0, codex])
    assert "未指定时默认使用" not in combined
    assert "不向用户提问" not in codex
    assert "必须询问" in skill
    assert "等待用户明确回复" in phase0


def test_detect_stack_refuses_to_default_missing_depth(tmp_path, monkeypatch):
    repo = tmp_path / "sample"
    repo.mkdir()
    (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
    work_dir = tmp_path / "_repoguide"
    work_dir.mkdir()
    (work_dir / "profile.json").write_text(
        json.dumps(
            {
                "repo_path": str(repo),
                "work_dir": str(work_dir),
                "analysis_mode": "local",
                "repo_name": "sample",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    code = extract_python_block(read_rel("sub-skills/tools/detect-stack.md"))
    code = re.sub(
        r'REPO_PATH = Path\("/path/to/repo"\)\.resolve\(\)',
        lambda _m: f"REPO_PATH = Path({str(repo)!r}).resolve()",
        code,
    )

    monkeypatch.setenv("WORK_DIR", str(work_dir))
    monkeypatch.delenv("REPOGUIDE_DEPTH", raising=False)

    with pytest.raises(SystemExit, match="REPOGUIDE_DEPTH"):
        exec(compile(code, "detect-stack.md", "exec"), {})


def test_detect_stack_prefers_typescript_over_javascript_when_tsconfig_present(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "_repoguide" / "repo"
    (repo / "src").mkdir(parents=True)
    work_dir = tmp_path / "_repoguide"

    (repo / "package.json").write_text('{"scripts":{"dev":"vite"}}\n', encoding="utf-8")
    (repo / "tsconfig.json").write_text('{"compilerOptions":{}}\n', encoding="utf-8")
    (repo / "src" / "index.ts").write_text("export const value: number = 1;\n", encoding="utf-8")

    (work_dir / "profile.json").write_text(
        json.dumps(
            {
                "repo_path": str(repo),
                "work_dir": str(work_dir),
                "analysis_mode": "clone",
                "repo_name": "ts-app",
                "depth": "standard",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    code = extract_python_block(read_rel("sub-skills/tools/detect-stack.md"))
    code = re.sub(
        r'REPO_PATH = Path\("/path/to/repo"\)\.resolve\(\)',
        lambda _m: f"REPO_PATH = Path({str(repo)!r}).resolve()",
        code,
    )

    monkeypatch.setenv("WORK_DIR", str(work_dir))
    monkeypatch.setenv("REPOGUIDE_DEPTH", "standard")
    exec(compile(code, "detect-stack.md", "exec"), {})
    capsys.readouterr()

    profile = json.loads((work_dir / "profile.json").read_text(encoding="utf-8"))
    assert profile["primary_language"] == "typescript"
    assert profile["all_languages"][0] == "typescript"


def test_repo_normalizer_extracts_full_github_repo_names(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_DIR", str(tmp_path / "_repoguide"))
    monkeypatch.setenv("REPO_REF", "")
    code = extract_python_block(read_rel("sub-skills/tools/repo-normalizer.md"))
    ns = {}
    exec(compile(code, "repo-normalizer.md", "exec"), ns)

    extract_repo_name = ns["extract_repo_name"]
    assert extract_repo_name("https://github.com/acme/my.repo.git") == "my.repo"
    assert extract_repo_name("git@github.com:acme/repo-name.git") == "repo-name"
    assert extract_repo_name("https://github.com/acme/repo.name-with-dash") == "repo.name-with-dash"


def test_pytest_configuration_ignores_generated_work_dirs():
    pytest_ini = ROOT / "pytest.ini"
    assert pytest_ini.exists()
    text = pytest_ini.read_text(encoding="utf-8")
    assert "testpaths = tests" in text
    assert "_repoguide" in text
    assert "AlphaSAGE-manual" in text

    gitignore = read_rel(".gitignore")
    assert "_repoguide_eval/" in gitignore


def test_manual_quality_checker_detects_english_sentences_and_ignores_code():
    code = extract_python_block(read_rel("sub-skills/tools/manual-quality-checker.md"))
    ns = {}
    exec(compile(code, "manual-quality-checker.md", "exec"), ns)

    find_violations = ns["find_english_sentence_violations"]
    markdown = """# 示例

这是中文说明，GFlowNet 和 RGCN 是允许保留的专有名词。

This section should be rewritten into Chinese.

```python
def train_model():
    return "This code string is allowed"
```
"""

    violations = find_violations(markdown)
    assert [item["text"] for item in violations] == ["This section should be rewritten into Chinese."]


def test_pdf_template_contains_layout_safety_primitives():
    template = read_rel("references/latex-template/main.tex")
    assert "adjustbox" in template
    assert "\\IfFontExistsTF{FandolSong}" in template
    assert "\\setCJKmainfont" in template
    assert "\\begin{titlepage}" in template
    assert "\\pagestyle{repoguide}" in template
    assert "\\newenvironment{repoguidetoc}" in template
    assert "\\setcounter{secnumdepth}{0}" in template
    assert "\\setcounter{tocdepth}{2}" in template
    assert "\\setkeys{Gin}" in template
    assert "max width=\\linewidth" in template
    assert "max height=0.72\\textheight" in template
    assert "\\raggedright" in template
    assert "\\definecolor{primary}{RGB}{139,0,18}" in template
    assert "\\definecolor{linkblue}{RGB}{139,0,18}" in template
    assert "\\definecolor{primary}{RGB}{25,72,145}" not in template
    assert template.count("{CONTENT}") == 1


def test_latex_renderer_defines_manual_toc_and_safe_table_contracts():
    text = read_rel("sub-skills/tools/latex-renderer.md")
    assert "REPOGUIDE_RENDERER_TOC_START" in text
    assert "REPOGUIDE_RENDERER_SAFE_TABLE_START" in text
    assert "build_manual_toc" in text
    assert "detect_heading_offset" in text
    assert "heading_anchor" in text
    assert "\\hyperlink" in text
    assert "\\hypertarget" in text
    assert "repoguidetoc" in text
    assert "tocmajor" in text
    assert "CODE_LIKE_TOKEN" in text
    assert "\\allowbreak{}" in text
    assert "longtable_col_spec" in text
    assert "\\begin{longtable}" in text
    assert "long_table = len(rows) > 10" in text
    assert '"_": "\\\\_"' in text
    assert '"↔": "\\\\ensuremath{\\\\leftrightarrow}"' in text
    assert "\\begin{tcolorbox}[notebox]" in text
    assert "begin{adjustbox}{max width=\\textwidth}" in text
    assert "不得把 pandoc 作为主转换器" in text


def test_latex_renderer_escapes_paths_methods_tables_and_quotes(tmp_path, monkeypatch):
    work_dir = tmp_path / "_repoguide"
    work_dir.mkdir()
    (work_dir / "manual.md").write_text(
        """# AlphaSAGE 仓库手册指南

> 由 RepoGuide 自动生成  > 仓库路径：`E:\\KimiClaw\\RepoGuide\\_repoguide_eval`，公式用 `$$...$$` 块渲染。

## train_gfn.py — 主训练入口

### 3.1 架构总览图

### src/alpha_gfn/modules.py — AlphaSAGE 结构感知编码器：RPN 到 RGCN 的长文件卡片标题

## 工具： up-calculate_quantile_huber_loss/get_subtree/reproduce

| 项 | 值 |
| --- | --- |
| 入口 | `train_gfn.py` 与 `__add__/__sub__` |
| 路径 | E:\\KimiClaw\\RepoGuide\\_repoguide_eval |

正文包含 train_gfn.py、filter_by_index/__add__ 和 $x_i^2$。
""",
        encoding="utf-8",
    )

    renderer = read_rel("sub-skills/tools/latex-renderer.md")
    ns = {}
    exec(compile(extract_python_block(renderer, "REPOGUIDE_RENDERER_TOC_START"), "toc", "exec"), ns)
    monkeypatch.setenv("WORK_DIR", str(work_dir))
    exec(compile(extract_python_block(renderer, "TEXT_ESCAPES"), "latex-renderer", "exec"), ns)

    tex = (work_dir / "manual-body.tex").read_text(encoding="utf-8")
    assert "\\begin{repoguidetoc}" in tex
    assert "\\tocmajor{\\hyperlink{repoguide-heading-5}{train\\_gfn.py" in tex
    assert "\\tocminor{\\hyperlink{repoguide-heading-7}{3.1 架构总览图}" in tex
    assert "RPN 到 RGCN 的长文件卡片标题" not in tex.split("\\end{repoguidetoc}", 1)[0]
    assert "\\hypertarget{repoguide-heading-5}{}" in tex
    assert "\\hypertarget{repoguide-heading-11}{}" in tex
    assert "\\section{train\\_gfn.py" in tex
    assert "calculate\\_\\allowbreak{}quantile" in tex
    assert "huber\\_\\allowbreak{}loss/\\allowbreak{}get" in tex
    assert "get\\_\\allowbreak{}subtree/\\allowbreak{}reproduce" in tex
    assert "\\section{AlphaSAGE 仓库手册指南}" not in tex
    assert "\\begin{tcolorbox}[notebox]" in tex
    assert "\\begin{adjustbox}{max width=\\textwidth}" in tex
    assert "\\texttt{train\\_gfn.py}" in tex
    assert "\\texttt{\\$\\$...\\$\\$}" in tex
    assert "train\\_gfn.py" in tex
    assert "\\_\\_add\\_\\_/\\_\\_sub\\_\\_" in tex
    assert "filter\\_\\allowbreak{}by\\_\\allowbreak{}index/\\allowbreak{}" in tex
    assert "\\(x_i^2\\)" in tex
    assert "\x00" not in tex
    assert "\\textbackslash{}texttt" not in tex
    assert "> 由 RepoGuide" not in tex


def test_latex_renderer_uses_longtable_for_long_tables(tmp_path, monkeypatch):
    work_dir = tmp_path / "_repoguide"
    work_dir.mkdir()
    formula_row = (
        r"| L_{final} = \mathbb{E}_{\tau}[L_{TB}(\tau)] + \beta \cdot entropy_bonus "
        r"| `EntropyTBGFlowNet.loss` | `src/alpha_gfn/gflownet.py:81` | high |"
    )
    rows = "\n".join(
        [formula_row]
        + [
            f"| formula_{i} | `AlphaPoolGFN._find_k_nearest_neighbors_{i}` | `src/alpha_gfn/alpha_pool.py:{i}` | high |"
            for i in range(11)
        ]
    )
    (work_dir / "manual.md").write_text(
        "\n".join(
            [
                "# AlphaSAGE 仓库手册指南",
                "",
                "## 论文-代码映射",
                "",
                "| 论文公式/算法 | 代码函数/类 | 位置 | 置信度 |",
                "| --- | --- | --- | --- |",
                rows,
            ]
        ),
        encoding="utf-8",
    )

    renderer = read_rel("sub-skills/tools/latex-renderer.md")
    ns = {}
    exec(compile(extract_python_block(renderer, "REPOGUIDE_RENDERER_TOC_START"), "toc", "exec"), ns)
    monkeypatch.setenv("WORK_DIR", str(work_dir))
    exec(compile(extract_python_block(renderer, "TEXT_ESCAPES"), "latex-renderer", "exec"), ns)

    tex = (work_dir / "manual-body.tex").read_text(encoding="utf-8")
    assert "\\begin{longtable}" in tex
    assert "\\endfirsthead" in tex
    assert "\\footnotesize" in tex
    assert "\\begin{adjustbox}" not in tex
    assert "find\\_\\allowbreak{}k\\_\\allowbreak{}nearest" in tex
    assert "\\textbackslash{}\\allowbreak{}mathbb" in tex


def test_html_renderer_contract_wraps_wide_tables_and_images():
    text = read_rel("sub-skills/tools/latex-renderer.md")
    assert "table-wrap" in text
    assert "overflow-x: auto" in text
    assert "max-height: 82vh" in text
    assert "object-fit: contain" in text
    assert "#94070A" in text
    assert "#0b3d91" not in text


def test_phase5_requires_visual_pdf_validation():
    text = read_rel("sub-skills/tasks/phase-5-renderer.md")
    assert "渲染抽检" in text
    assert "PyMuPDF" in text or "pdftoppm" in text
    assert "目录页不得为空" in text
