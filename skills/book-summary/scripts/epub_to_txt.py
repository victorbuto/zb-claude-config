#!/usr/bin/env python3
"""
EPUB to Text Converter
Extracts text from EPUB files preserving Markdown structure.
"""

import sys
import re
from pathlib import Path

try:
    from ebooklib import epub
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "ebooklib", "beautifulsoup4", "markdownify",
                          "--break-system-packages", "-q"])
    from ebooklib import epub
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md


def clean_text(text: str) -> str:
    """Clean up extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Clean up markdown artifacts
    text = re.sub(r'\n +', '\n', text)
    return text.strip()


def epub_to_text(epub_path: str, output_path: str) -> None:
    """Convert EPUB to text file with Markdown formatting."""

    book = epub.read_epub(epub_path)

    # Get metadata
    title = book.get_metadata('DC', 'title')
    title = title[0][0] if title else "Unknown Title"

    creator = book.get_metadata('DC', 'creator')
    creator = creator[0][0] if creator else "Unknown Author"

    full_text = []
    full_text.append(f"# {title}\n")
    full_text.append(f"**Автор:** {creator}\n")
    full_text.append("---\n")

    # Extract text from all documents
    for item in book.get_items():
        if item.get_type() == 9:  # XHTML document type
            soup = BeautifulSoup(item.get_content(), 'html.parser')

            # Remove scripts and styles
            for tag in soup(['script', 'style', 'nav']):
                tag.decompose()

            # Convert to markdown
            content = md(str(soup), heading_style="ATX", bullets="-")
            content = clean_text(content)

            if content and len(content) > 50:  # Skip near-empty sections
                full_text.append(content)
                full_text.append("\n\n---\n\n")

    # Write output
    output = "\n".join(full_text)
    output = clean_text(output)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"✓ Converted: {epub_path}")
    print(f"✓ Output: {output_path}")
    print(f"✓ Size: {len(output):,} characters")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python epub_to_txt.py <input.epub> <output.txt>")
        sys.exit(1)

    epub_to_text(sys.argv[1], sys.argv[2])
