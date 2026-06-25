import json
import re
from pathlib import Path
from typing import Optional


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
