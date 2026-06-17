#!/usr/bin/env bash
# generate-pdf.sh - Convert markdown to PDF with tool auto-detection.
# Usage: generate-pdf.sh <input.md> [output.pdf]
# Output: absolute path to PDF (on stdout, last line)
# Falls back gracefully if no PDF tool is available.

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.md> [output.pdf]" >&2
    exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.md}.pdf}"

if [ ! -f "$INPUT" ]; then
    echo "Error: input file not found: $INPUT" >&2
    exit 1
fi

# Make output absolute
case "$OUTPUT" in
    /*) ;;
    *) OUTPUT="$(pwd)/$OUTPUT" ;;
esac

# Try pandoc first (best quality)
if command -v pandoc >/dev/null 2>&1; then
    echo "Using pandoc" >&2
    if pandoc "$INPUT" -o "$OUTPUT" 2>/dev/null; then
        if [ -f "$OUTPUT" ]; then
            echo "$OUTPUT"
            exit 0
        fi
    fi
fi

# Try weasyprint (Python-based)
if command -v weasyprint >/dev/null 2>&1; then
    echo "Using weasyprint" >&2
    if weasyprint "$INPUT" "$OUTPUT" 2>/dev/null; then
        if [ -f "$OUTPUT" ]; then
            echo "$OUTPUT"
            exit 0
        fi
    fi
fi

# Try Python markdown-pdf
if python -c "import markdown_pdf" 2>/dev/null; then
    echo "Using markdown_pdf" >&2
    if python -m markdown_pdf "$INPUT" -o "$OUTPUT" 2>/dev/null; then
        if [ -f "$OUTPUT" ]; then
            echo "$OUTPUT"
            exit 0
        fi
    fi
fi

# No tool worked - graceful failure
echo "PDF_GENERATION_FAILED: no PDF tool available" >&2
echo "To enable PDF generation, install one of:" >&2
echo "  - pandoc (with xelatex): brew install pandoc mactex" >&2
echo "  - weasyprint: pip install weasyprint" >&2
echo "  - markdown-pdf: pip install markdown-pdf" >&2
echo "" >&2
echo "Continuing without PDF. The markdown report is still available." >&2
echo "PDF_GENERATION_FAILED"
exit 0
