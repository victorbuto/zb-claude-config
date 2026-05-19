---
name: researching-web-yakov
description: |
  Researches questions using web search and generates HTML reports with confidence scores and sources.
  Use when: (1) User asks a question requiring current information, (2) User says "find out about X", (3) User gives URL to extract data from, (4) Question about code/API/library, (5) Comparing options or alternatives.
---

# Web Research Skill

Orchestrates Exa + Tabstack for hybrid search, parallel extraction, and structured output.

## Pipeline

```
Query → Classify → Search (parallel) → Score → Extract (parallel) → Synthesize → Verify → Output
```

**Tools:** `mcp__exa__web_search_exa`, `mcp__tabstack__tabstack_search`, `mcp__tabstack__tabstack_extract_markdown`

## Progress Format

Show progress with real data at each step:

```
══════════════════════════════════════════
   RESEARCHING: "{query}"
══════════════════════════════════════════
[■■□□□□] Search: Exa 8 | Tabstack 5 → 10 unique
         (⚠️ Tabstack unavailable → Exa-only mode)

[■■■□□□] Scoring: digitalapplied.com (82), decode.agency (78), ...
         Selected: 5 sources above threshold

[■■■■□□] Extracting (parallel)...
         ✓ digitalapplied.com
         ✓ decode.agency
         ...

[■■■■■□] Synthesizing + Verifying...

[■■■■■■] Confidence: 85%
         ├─ Consensus: 4/5 agree
         ├─ Top source: 82 (official docs tier)
         ├─ Freshness: 5/5 from 2025-2026
         └─ Contradictions: none

📊 RESEARCH DEPTH
   Pages analyzed: 12 | Facts extracted: 47
   Sources: 5 (2 official, 2 research, 1 blog)
   Coverage: High — multiple independent confirmations
══════════════════════════════════════════
```

---

## Step 1: Classify & Plan

| Type | Signals | Sources | Search Strategy |
|------|---------|---------|-----------------|
| Fact | "what is", "when", "how much" | 1-2 | Exa only |
| How-to | "how to", tutorial | 2-3 | Exa only |
| Comparison | "vs", "compare", "best" | 5+ | Hybrid (Exa + Tabstack) |
| Overview | "explain", "tell me about" | 3-5 | Hybrid |
| Code/API | library, SDK, docs | 1-2 | `get_code_context_exa` |

## Step 2: Search

**Has URL** → skip to extraction.

**No URL** → search with query augmentation (synonyms, EN version for tech).

For hybrid: call both `mcp__exa__web_search_exa` and `mcp__tabstack__tabstack_search` in single message.

**Fallback:** If Tabstack unavailable → "⚠️ Exa-only mode" and continue.

## Step 3: Score & Select

Trust Claude's judgment. Prefer: official docs > research > GitHub > Stack Overflow > blogs > forums.

Skip: SEO spam, paywalls, >2 years old (for tech).

## Step 4: Extract (Parallel)

Call ALL extractions in single message using `mcp__tabstack__tabstack_extract_markdown`.

If extraction fails: "⚠️ {url} failed, continuing with others"

## Step 5: Synthesize

1. Merge facts, dedupe
2. Note contradictions with source attribution
3. Identify consensus vs disputed points

## Step 6: Verify & Detect Contradictions

Before finalizing, actively look for contradictions between sources. When found, display:

```
⚠️ CONTRADICTION DETECTED:
   Source A (domain.com): "Claim X"
   Source B (other.com): "Claim Y"
   → Likely cause: {different timeframes / methodology / scope}
```

Also check:
- Single-source claims → mark as "unverified"
- Non-authoritative sources for topic → adjust confidence

## Step 7: Output (Zero Friction)

**Auto-select format, no questions asked:**
- "vs"/"compare" → Comparison Table HTML
- Simple question → Answer in chat + sources
- Complex topic → Full HTML Report

Generate immediately. If user wants different format, they'll ask.

**Include in every output:**
- Confidence score with breakdown
- Contradictions found (if any)
- Research depth stats

---

## Fallback

Tool fails → inform with ⚠️, continue with remaining. Search empty → simplify query. All weak → suggest refining.
