#!/usr/bin/env python3
from __future__ import annotations
"""Convert Markdown to PDF, installing dependencies if necessary.

Usage: python generate-pdf.py <input.md> [output.pdf]
Output: absolute path to PDF (on stdout, last line)
Falls back gracefully if no PDF backend can be set up.

Strategy:
1. Ensure markdown + fpdf2 are installed (auto-install via pip/uv).
2. Find a system Unicode font (CJK/DejaVu support).
3. Convert Markdown -> simplified HTML -> PDF with fpdf2.
"""
import logging
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

# fpdf2/fontTools emit harmless font-subsetter warnings; silence them for clean output.
warnings.filterwarnings("ignore", message=".*MERG.*")
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
logging.getLogger("fontTools").setLevel(logging.ERROR)


def install_deps() -> bool:
    """Try to install markdown + fpdf2 into the current Python environment."""
    packages = ["markdown", "fpdf2"]
    candidates = [
        [sys.executable, "-m", "pip", "install", "--user", *packages],
        [sys.executable, "-m", "pip", "install", *packages],
        [sys.executable, "-m", "uv", "pip", "install", *packages],
        ["uv", "pip", "install", *packages],
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            import importlib
            importlib.import_module("markdown")
            importlib.import_module("fpdf")
            return True
        except Exception:
            continue
    return False


def ensure_deps() -> bool:
    """Ensure required packages are importable, installing if needed."""
    try:
        import markdown  # noqa: F401
        from fpdf import FPDF  # noqa: F401
        return True
    except ImportError:
        return install_deps()


def find_unicode_font() -> Path | None:
    """Find a system font that supports Unicode/CJK text."""
    candidates = [
        # Windows
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        # macOS
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        # Linux
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def simplify_html(html: str) -> str:
    """Simplify Markdown-generated HTML so fpdf2 can render it reliably."""
    # Headings -> bold paragraphs with size
    def repl_heading(m):
        level = len(m.group(1))
        text = m.group(2)
        size = {1: 20, 2: 16, 3: 14, 4: 13, 5: 12, 6: 12}.get(level, 12)
        return f'<p><b><font size="{size}">{text}</font></b></p>'

    html = re.sub(r"<h([1-6])>(.*?)</h\1>", repl_heading, html, flags=re.S)

    # Bold / italic
    html = html.replace("<strong>", "<b>").replace("</strong>", "</b>")
    html = html.replace("<em>", "<i>").replace("</em>", "</i>")

    # Code blocks -> smaller paragraphs with line breaks
    def repl_codeblock(m):
        code = m.group(1)
        code = code.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        code = code.replace("\n", "<br>")
        return f'<p><font size="10">{code}</font></p>'

    html = re.sub(r"<pre><code>(.*?)</code></pre>", repl_codeblock, html, flags=re.S)
    html = html.replace("<code>", '<font size="10">').replace("</code>", "</font>")

    # Self-closing tags that fpdf2 dislikes
    html = html.replace("<hr />", "<hr>").replace("<br />", "<br>")

    # List items need inner paragraph
    html = html.replace("<li>", "<li><p>").replace("</li>", "</p></li>")

    # Wrap everything in the Unicode font face
    return f'<font face="Unicode">{html}</font>'


def md_to_pdf(input_path: Path, output_path: Path, font_path: Path) -> bool:
    """Generate PDF from Markdown using markdown + fpdf2."""
    import markdown
    from fpdf import FPDF

    try:
        md_text = input_path.read_text(encoding="utf-8", errors="ignore")
        html_body = markdown.markdown(md_text, extensions=["extra", "nl2br", "tables"])
        html = simplify_html(html_body)

        pdf = FPDF()
        pdf.add_font("Unicode", "", str(font_path))
        pdf.add_font("Unicode", "B", str(font_path))
        pdf.set_font("Unicode", "", 12)
        pdf.add_page()
        pdf.write_html(html)
        pdf.output(str(output_path))
        return output_path.exists()
    except Exception:
        return False


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate-pdf.py <input.md> [output.pdf]", file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2]).resolve()
    else:
        output_path = input_path.with_suffix(".pdf")

    if not ensure_deps():
        print("PDF_GENERATION_FAILED: could not install PDF dependencies", file=sys.stderr)
        print("Continuing without PDF. The markdown report is still available.", file=sys.stderr)
        print("PDF_GENERATION_FAILED")
        return 0

    font_path = find_unicode_font()
    if font_path is None:
        print("PDF_GENERATION_FAILED: no usable Unicode system font found", file=sys.stderr)
        print("Continuing without PDF. The markdown report is still available.", file=sys.stderr)
        print("PDF_GENERATION_FAILED")
        return 0

    if md_to_pdf(input_path, output_path, font_path):
        print(str(output_path))
        return 0

    print("PDF_GENERATION_FAILED: PDF engine could not generate output", file=sys.stderr)
    print("Continuing without PDF. The markdown report is still available.", file=sys.stderr)
    print("PDF_GENERATION_FAILED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
