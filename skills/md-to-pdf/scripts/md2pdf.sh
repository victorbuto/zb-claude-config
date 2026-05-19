#!/bin/bash
# Convert Markdown to PDF using pandoc + tectonic
# Usage: md2pdf.sh <input.md> [output.pdf]
# If output is omitted, creates PDF in the same folder with same name

set -euo pipefail

INPUT="$1"
OUTPUT="${2:-${INPUT%.md}.pdf}"

if [ ! -f "$INPUT" ]; then
  echo "Error: file not found: $INPUT" >&2
  exit 1
fi

pandoc "$INPUT" \
  -o "$OUTPUT" \
  --pdf-engine=tectonic \
  -V mainfont="Helvetica" \
  -V geometry:margin=2.5cm \
  -V fontsize=11pt \
  -V lang=ru

echo "$OUTPUT"
