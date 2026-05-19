---
name: book-summary
description: Creates comprehensive structured summaries (non-fiction) from EPUB or text files. Use when the user asks to summarize a book, create a book summary, or make a конспект книги. Triggers on requests like "summarize this book", "сделай саммари книги", "конспект книги", "book summary", or when an .epub/.txt/.md file is mentioned together with summary/analysis request.
---

# Book Summary Skill

Creates structured, actionable summaries of non-fiction books.

## File Paths

| Purpose | Path |
|---------|------|
| **Save summaries** | `/Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)/working files/Книги/Summary/` |
| **Save converted text (from EPUB)** | `/Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)/working files/Книги/Очищенные/` |

## Start

When skill is triggered, do NOT ask any preliminary questions or show option menus. Simply say: **"Подгрузи файл книги (.epub, .txt или .md)"** and wait for the user to provide the file.

## Workflow

### Step 1: Check Source Format

**If source is EPUB (.epub):**
- Run conversion script (see below)
- Save converted text to `Книги/Очищенные/`

**If source is already text (.txt, .md):**
- Skip conversion, read file directly
- No script needed

### Step 1a: Convert EPUB to Text (only for .epub files)

Run the conversion script:

```bash
pip install ebooklib beautifulsoup4 markdownify --break-system-packages
python /Users/fixed/Documents/ZB\ CLOUD\ 3600/.claude/skills/book-summary/scripts/epub_to_txt.py /path/to/book.epub "/Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)/working files/Книги/Очищенные/[Book Name].md"
```

The script extracts text preserving Markdown structure (headers, lists).

### Step 2: Create Summary

**IMPORTANT: Before creating summary, read the full standard file located in this skill folder:**
`Book Summary Standard v2.md`

Use Read tool to open: `/Users/fixed/Documents/ZB CLOUD 3600/.claude/skills/book-summary/Book Summary Standard v2.md` 

**Key principles:**
- Use **True Bottom-Up Generation**: write detailed chapters first, then synthesize Tools & Executive Summary
- Language matches source book (English book → English summary, Russian → Russian)
- Focus on **instruments and algorithms** — actionable content is priority #1
- Write in **bullet points**, not paragraphs
- Every concept needs an answer to "What to do with this?"

**Output structure (in order):**
1. **Book Passport** — metadata, author, audience, idea rating (1-10)
2. **Main Topics** — navigation list of H2 sections
3. **Detailed Content** — H2/H3 sections with bullets, examples, warnings
4. **🛠 Tools & Frameworks** — all practical methods with step-by-step algorithms
5. **Key Takeaways** — 3-10 main insights (generated LAST, based on full context)

### Step 3: Save Summary

**Save to:** `/Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)/working files/Книги/Summary/`

**Filename format:** `Summary_[Book Title]_[Author].md`

**Example:** `Summary_Thinking Fast and Slow_Kahneman.md`

**Full path example:** `/Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)/working files/Книги/Summary/Summary_Thinking Fast and Slow_Kahneman.md`

## Formatting Quick Reference

| Element | Usage |
|---------|-------|
| `>` blockquote | Key formulations, author quotes |
| `→` arrow | Interpretation, consequences |
| `⚠️` | Warnings, common mistakes |
| `💡` | Tips, insights |
| `🛠` | Tools and algorithms |
| Tables | Comparisons, classifications |

## What to Include / Exclude

**Always include:**
- 🛠 Tools, algorithms, methodologies
- Key concepts with definitions
- Author's logic and reasoning
- Practical examples with interpretation
- Cause-effect relationships
- Warnings about common mistakes

**Exclude:**
- Empty motivational content
- Repeated ideas
- Biographical details (minimize)
- Off-topic discussions