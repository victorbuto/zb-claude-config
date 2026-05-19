---
name: Deep-web-search
description: Advanced keyword generation and web search using the Slice Method. Use when the user needs to generate effective search queries, find information beyond surface-level results, or bypass commercial noise in search engines. Triggers on requests for "search keywords", "find information", "research", "search strategy", or when the user struggles to find relevant results with basic searches. This skill focuses on search execution without fact-checking — pair with a fact-checking skill for verification.
---

# Slice Search Skill

6 steps: receive question → clarify → plan queries + assign tools → approve → 3 parallel subagents (multi-tool search & analyze) → QA audit (background) + merge (foreground).

## Phase 0: Receive the Research Question

**IMPORTANT: Do NOT ask any questions until the user has provided their research topic/question.** If the user's message already contains a clear research question — proceed to Phase 1 (SPICE). If the message is vague or just triggers the skill without a specific question, respond with:

```
Какой вопрос будем исследовать?
```

**STOP here and wait for the user's research question before proceeding.**

---

## Phase 1: Clarify the Research Question (SPICE)

Once you have the user's research question, ask **5 clarifying questions** using the **SPICE framework** (adapted from academic research methodology: Setting, Perspective, Interest, Comparison, Evaluation).

The goal: expose blind spots and hidden assumptions in the user's request.

**Ask these 5 questions and wait for answers before proceeding to Phase 2:**

| # | SPICE element | Question to ask | What it reveals |
|---|---------------|-----------------|-----------------|
| 1 | **Setting** | Какая география, отрасль, сегмент рынка? Есть ли временные рамки (последний год, 5 лет, всё время)? | Boundaries — сужает область поиска |
| 2 | **Perspective** | Чей взгляд важен — бизнес, академия, потребители, инвесторы? Для какой аудитории результат? | Angle — определяет тип источников и язык |
| 3 | **Interest** | Что конкретно нужно найти — обзор темы, конкретные цифры/данные, кейсы, список игроков, тренды? | Depth — задаёт глубину и формат поиска |
| 4 | **Comparison** | Есть ли с чем сравнивать? Нужен бенчмарк (другая страна, период, конкурент)? | Contrast — добавляет сравнительное измерение |
| 5 | **Existing knowledge** | Что уже знаете по теме? Какие источники/статьи уже видели? Что НЕ нужно искать? | Gaps — исключает дубли, фокусирует на белых пятнах |

**Format for asking:**
```
Перед поиском уточню 5 вопросов по фреймворку SPICE:

1. **Рамки:** [вопрос адаптированный к теме]
2. **Перспектива:** [вопрос]
3. **Что ищем:** [вопрос]
4. **Сравнение:** [вопрос]
5. **Уже знаете:** [вопрос]
```

After user answers, incorporate their responses into Phase 2 analysis as constraints.

---

## Phase 2: Plan Search Queries

Use SPICE answers to inform query generation.

### 2.1 Analyze the Query

- **Core topic** — main subject (from user request + SPICE answers)
- **Goal** — facts, sources, opinions, data, comparison (from SPICE #3 Interest)
- **Query type** — classify for slice distribution
- **Constraints** — from SPICE #1 Setting + #2 Perspective + #5 Existing knowledge

| Query Type | Primary Slices | Secondary Slices |
|------------|----------------|------------------|
| **Factual/Statistical** | Source, Authority, Peristatic | Regional, Syntactic |
| **Technical/Expert** | Specific Term, Metonymical, Source | Syntactic, Authority |
| **Current Events** | Source, Regional, Authority | Peristatic |
| **Historical/Academic** | Syntactic (filetype), Authority, Source | Regional, Metonymical |
| **Comparative** | Regional, Source, Authority | Metonymical |
| **Niche/Obscure** | Specific Term, Syntactic, Peristatic | Regional, Source |

### 2.2 Generate 20+ Search Queries

Use **7 slice types** (see [references/slice-method.md](references/slice-method.md)):

| Slice | What It Does |
|-------|--------------|
| **Regional** | Other languages/markets |
| **Authority** | Known institutions/experts |
| **Source** | Specific platforms/databases |
| **Specific Term** | Niche expert terminology |
| **Syntactic** | Alt spellings, scripts, filetypes |
| **Metonymical** | Adjacent/related concepts |
| **Peristatic** | Quotes, contextual fragments |

**Key:** Rare terms > generic terms.

Distribution by type:

| Query Type | Reg | Auth | Source | Spec | Synt | Meton | Perist |
|------------|-----|------|--------|------|------|-------|--------|
| Factual | 2 | 3 | 8 | 2 | 1 | 1 | 3 |
| Technical | 1 | 2 | 4 | 5 | 3 | 4 | 1 |
| News | 3 | 3 | 9 | 1 | 1 | 1 | 2 |
| Academic | 2 | 4 | 4 | 2 | 4 | 2 | 2 |
| Comparative | 5 | 3 | 6 | 2 | 1 | 2 | 1 |
| Niche | 3 | 1 | 1 | 5 | 4 | 3 | 3 |

### 2.3 Assign Search Tool per Query

**BEFORE assigning tools, read [references/operational-rules.md](references/operational-rules.md)** — it contains rules from past QA audits. Apply every rule that matches the current query set.

For each query, select the best tool based on the **search case** it belongs to. Use this decision guide:

#### Available Tools

| Tool | What it does | Returns |
|------|-------------|---------|
| **tavily_search** | Keyword search with snippets + full page text | Snippets (500 chars) + raw_content + relevance score (0–1) |
| **tavily_extract** | Extracts content from known URLs (no search) | Full page text in markdown. Use `extract_depth: "advanced"` for JS-heavy sites |
| **tavily_crawl** | Follows links from a starting URL, collects multiple pages | Content from up to 50 pages. Use `instructions` to filter |
| **tavily_research** | Autonomous multi-search with synthesis | Synthesized answer from multiple searches |
| **Exa** (`web_search_advanced_exa`) | Semantic/neural search with filters | Up to 100 results with highlights, summaries, or full text |
| **WebSearch** | Built-in Claude web search | Snippets with auto-citations |

#### Search Cases → Tool Selection

| Case | How to recognize | Tool | Key parameters |
|------|-----------------|------|----------------|
| **Поиск на конкретном сайте** | Query targets a specific domain (vc.ru, habr, hbr.org, reddit) | **tavily_search** | `include_domains: ["domain.com"]`, `include_raw_content: true`, `search_depth: "advanced"`. Do NOT put `site:` in the query text — use `include_domains` instead |
| **Поиск отзывов покупателей** | Review platforms (otzovik, irecommend, 2gis, yandex maps) | **tavily_search** → **tavily_extract** | Two-pass: search with `include_domains` to find URLs, then `tavily_extract` with `extract_depth: "advanced"` on best URLs. JS-heavy sites need extract |
| **Поиск рыночных данных и цифр** | Market size, shares, growth rates, industry reports | **Exa** | `category: "research paper"` or `"financial report"`, `startPublishedDate`, `enableHighlights: true`, `highlightsQuery: "market size revenue"` |
| **Поиск в деловых/отраслевых медиа** | Business news (РБК, Bloomberg, Коммерсант, retail.ru) | **Exa** | `category: "news"`, `includeDomains: [...]`, `startPublishedDate` |
| **Поиск по бренду/компании** | Query contains a brand name + keywords | **tavily_search** | `include_raw_content: true`, `search_depth: "advanced"`. Brand names are exact keywords — keyword search works best |
| **Концептуальный/тематический поиск** | Topic or concept without specific brand/site (e.g. "customer-centricity in optics", "challenger brand strategy") | **Exa** | `type: "neural"`, `enableHighlights: true`, `highlightsQuery: "[focus phrase]"`. Neural search understands concepts and Russian morphology |
| **Поиск живых голосов покупателей** | Exact phrases people would say (fears, complaints, praise) | **tavily_search** first, then **Exa** fallback | Tavily: `exact_match: true`. If <2 results → Exa: `includeText: ["phrase"]`, `excludeDomains: ["shop domains"]` |
| **Поиск PDF и отчётов** | Research papers, whitepapers, filetype:pdf | **Exa** | `category: "pdf"` or `"research paper"`, `enableHighlights: true` |
| **Поиск на другом языке** | Japanese, Spanish, English queries for cross-market comparison | **Exa** | `type: "neural"`, `userLocation: "JP"/"ES"/etc.` Semantic search handles multilingual better |
| **Поиск экспертов и авторов** | Known people names (Byron Sharp, Raoul Pal) | **tavily_search** | `search_depth: "advanced"`, `include_raw_content: true`. Proper nouns = exact keywords |
| **Поиск в соцсетях и комьюнити** | Reddit, LinkedIn, forums | **tavily_search** | `include_domains: ["reddit.com"]` or `["linkedin.com"]`. VK/Telegram: use **WebSearch** instead (neither Tavily nor Exa parses them well) |
| **Поиск смежных категорий** | Parallels from adjacent industries | **Exa** | `type: "neural"`, `enableHighlights: true`. Cross-category connections are semantic |
| **Поиск свежих трендов и прогнозов** | Predictions, forecasts, current data | **Exa** | `startPublishedDate: "YYYY-MM-DD"`, `category: "news"` |
| **Поиск кейсов и примеров** | Case studies, success stories | **Exa** | `type: "neural"`, `includeText: ["case study"]` or `["кейс"]`, `enableHighlights: true` |
| **Поиск точных фраз с результатами** | Literal quotes with numbers ("revenue grew", "increased sales by") | **tavily_search** | `exact_match: true`, `include_raw_content: true` |
| **Поиск вакансий** (understanding company processes) | Job platforms (hh.ru, glassdoor) | **tavily_search** | `include_domains: ["hh.ru"]` or `["glassdoor.com"]` |
| **Поиск юридических/регуляторных данных** | Laws, standards, compliance docs | **Exa** | `category: "pdf"`, `includeDomains: ["consultant.ru", "garant.ru"]` |
| **Поиск академических исследований** | Scientific papers, academic sources | **Exa** | `category: "research paper"`, `enableHighlights: true` |
| **Обход раздела сайта** (multiple review pages, catalog sections) | Need content from several pages of one site | **tavily_crawl** | `max_depth: 2`, `instructions: "what to return"`, `select_paths: ["/reviews/.*"]` |

#### Fallback Rules

- If **tavily_search** returns <2 results with score >0.3 for a query → retry with **Exa** (neural, no domain restriction)
- If any result has score >0.5 but **raw_content is empty or truncated** → run **tavily_extract** (`extract_depth: "advanced"`) on that URL
- If a query on a specific domain fails completely → remove domain restriction and retry broader

### 2.4 Present to User

**STOP. Show the query list and wait for approval:**

```
## Search Plan: [Topic]
**Type:** [Classification] | **Queries:** [N]

| # | Slice | Query | Tool | Case | Why |
|---|-------|-------|------|------|-----|
| 1 | Source | `оптика отзывы покупатели` | tavily_search → tavily_extract | Отзывы | Отзывы, JS-сайт |
| 2 | Authority | `рынок оптики 2024 аналитика` | Exa (news) | Деловые медиа | Новости + дата |
| 3 | Metonymical | `клиентоцентричность ритейл` | Exa (neural) | Концептуальный | Тема, не keyword |
| ... | ... | ... | ... | ... | ... |

Approve, edit, or add?
```

---

## Phase 3: Search & Analyze (3 parallel subagents)

After user approves, split queries into 3 groups and launch **3 subagents in parallel**. Each subagent searches AND analyzes within its own context window.

### CRITICAL: Per-Query Attribution

Each subagent MUST return results **grouped by query** so that search quality can be evaluated per keyword. This is essential for the QA audit in Phase 3.5.

### Subagent prompt template

Each subagent receives its queries **with the assigned tool and parameters**. The prompt must include tool-specific instructions.

```
Task(subagent_type="general-purpose", prompt="
  You are a research agent. Your task:

  1. SEARCH: Execute each query using the assigned tool with the specified parameters.

     Queries:

     Query 1: `[query text]`
     - Tool: [tavily_search / Exa / WebSearch / tavily_crawl]
     - Parameters: [specific params from the plan, e.g. include_domains, category, type, etc.]

     Query 2: `[query text]`
     - Tool: [...]
     - Parameters: [...]

     [... repeat ...]

     OPERATIONAL RULES (from past QA audits — follow strictly):
     [paste the current contents of references/operational-rules.md here]

     TOOL USAGE RULES:
     - tavily_search: use mcp__tavily__tavily_search. Key params: query, search_depth='advanced', include_raw_content=true, max_results=5, include_domains, exclude_domains, exact_match, country
     - Exa: use mcp__exa__web_search_advanced_exa. Key params: query, type='neural', numResults=10, enableHighlights=true, highlightsPerUrl=3, includeDomains, excludeDomains, includeText, excludeText, category, startPublishedDate, userLocation
     - WebSearch: use the built-in WebSearch tool
     - tavily_extract: use mcp__tavily__tavily_extract. Params: urls (array), extract_depth='advanced', format='markdown', query (for reranking)
     - tavily_crawl: use mcp__tavily__tavily_crawl. Params: url, max_depth, max_breadth, limit, instructions, select_paths, extract_depth

     FALLBACK RULES:
     - If tavily_search returns <2 results with useful content for a query → retry with Exa (type='neural', no domain restriction)
     - If any result has content that is empty or truncated but URL looks relevant → run tavily_extract (extract_depth='advanced') on that URL
     - Log every fallback action in the per-query breakdown

  2. ANALYZE: Read through all results.
     Extract: facts, statistics, expert quotes, case studies, contradictions.
     For tavily_search: drop results with score < 0.3.
     For Exa: evaluate highlight relevance qualitatively.
     Deduplicate by URL.

  3. RETURN exactly this format:

     ## Round [N] Results

     **Queries executed:** [N]
     **Results found:** [N] unique after dedup

     ### Per-Query Breakdown

     **Query 1:** `[exact query text]`
     - Tool used: [tavily_search / Exa / WebSearch]
     - Fallback used: [none / retried with Exa / used tavily_extract on URL X]
     - Results returned: [N]
     - Useful results (with real content): [N]
     - Score range: [min–max] (for tavily) or [N/A for Exa/WebSearch]
     - Content quality: [full text / snippets only / empty / JS-blocked]
     - Best result: [Title](URL) — [one-line summary]
     - Findings:
       - [fact/data — [Source](URL)]
       - [fact/data — [Source](URL)]

     **Query 2:** `[exact query text]`
     [... same structure ...]

     [... repeat for each query ...]

     ### Combined Key Findings
     [Deduplicated synthesis of ALL findings across all queries.
     Every fact, statistic, or claim with inline source link:
     'fact or data — [Source Name](URL)']

     ### Source List
     | # | Title | URL | Tool | Score/Quality | From Query # | What it contributed |
     |---|-------|-----|------|---------------|--------------|---------------------|

     ### Gaps
     [What queries returned nothing useful, what's missing]
")
```

**Launch all 3 in parallel in a single message:**
- Subagent 1: queries 1-8 (priority slices)
- Subagent 2: queries 9-15 (secondary slices)
- Subagent 3: queries 16-22+ (adaptive, gap-filling)

### What main context receives

3 structured summaries with per-query breakdowns and pre-analyzed findings. NO raw page content in main context.

---

## Phase 3.5: QA Audit (background) + Synthesis (foreground) — IN PARALLEL

After all 3 search subagents complete, launch **two processes simultaneously**:

1. **QA Audit Agent** — runs in BACKGROUND (`run_in_background: true`)
2. **Synthesis** — proceeds immediately in the FOREGROUND (Phase 4)

This way the user gets their research results without waiting for the QA report. The QA report arrives after and is shown separately.

### QA Audit Agent prompt

The QA audit evaluates **3 dimensions**: keyword quality, tool selection, and content extraction. This helps improve the skill over time.

```
Task(subagent_type="general-purpose", run_in_background=true, prompt="
  You are a search quality auditor. Analyze the per-query breakdowns
  from 3 search rounds and produce a quality report across 3 dimensions.

  Here are the search results from all 3 rounds:

  [paste the Per-Query Breakdown sections from all 3 subagents]

  Produce this EXACT format:

  ## Отчёт по качеству поиска

  ### 1. Оценка по каждому запросу

  | # | Запрос | Слайс | Инструмент | Результатов | Полезных | С контентом | Fallback | Вердикт |
  |---|--------|-------|------------|-------------|----------|-------------|----------|---------|
  | 1 | `[query]` | Source | tavily_search | 5 | 3 | 3 | нет | ✓ |
  | 2 | `[query]` | Meton | Exa neural | 10 | 1 | 1 | нет | ~ |
  | 3 | `[query]` | Source | tavily→extract | 5 | 4 | 2+2 extract | да | ✓ |
  | ... | ... | ... | ... | ... | ... | ... | ... | ... |

  Вердикт:
  - ✓ Хорошо — 3+ полезных результата с конкретными данными
  - ~ Слабо — 1-2 полезных или только общий контент
  - ✗ Пусто — 0 полезных или всё нерелевантно

  ### 2. Оценка ключевых слов

  | Оценка | Детали |
  |--------|--------|
  | **Лучшие запросы** | `[query]` — почему сработал (конкретный термин, правильный домен, удачная фраза) |
  | **Худшие запросы** | `[query]` — почему провалился (слишком общий, неправильный язык, SEO-шум, нерелевантная выдача) |
  | **Пропущенные запросы** | Какие запросы стоило бы добавить, исходя из найденных gaps |
  | **Рекомендации по формулировке** | Что изменить в будущем: более узкие термины, другой язык, другие домены |

  ### 3. Оценка выбора инструментов

  | Инструмент | Запросов | Ср. полезных | Лучший результат | Худший результат |
  |------------|----------|-------------|-----------------|-----------------|
  | tavily_search | [N] | [N] из [N] | `[query]` → [что нашёл] | `[query]` → [почему провал] |
  | Exa neural | [N] | [N] из [N] | ... | ... |
  | tavily_extract | [N] | [N] из [N] | ... | ... |
  | tavily_crawl | [N] | [N] из [N] | ... | ... |
  | WebSearch | [N] | [N] из [N] | ... | ... |

  **Ошибки выбора инструмента:**
  - Запрос #[N]: использовали [tool], лучше было бы [other tool] — потому что [reason]
  - [... repeat for each misassignment ...]
  - Если все инструменты выбраны верно: «Ошибок выбора не обнаружено»

  ### 4. Оценка извлечения контента

  | Проблема | Запросы | Причина | Как исправить |
  |----------|---------|---------|---------------|
  | JS-рендеринг (пустой контент) | #[N], #[N] | [сайт] не отдаёт текст через search | Использовать tavily_extract (advanced) или tavily_crawl |
  | Кодировка сломана | #[N] | [сайт] — кириллица побилась | Попробовать Exa или WebSearch |
  | Контент обрезан | #[N] | raw_content неполный | tavily_extract на конкретный URL |
  | SEO-мусор вместо контента | #[N] | Запрос слишком общий | Добавить excludeDomains или includeText |
  | Если проблем нет: «Извлечение контента прошло без проблем» | | | |

  ### 5. Слайсы: эффективность

  | Тип слайса | Запросов | Ср. hit rate | Лучший | Худший |
  |------------|----------|-------------|--------|--------|
  | Source | [N] | [%] | `[query]` | `[query]` |
  | Authority | [N] | [%] | ... | ... |
  | Regional | [N] | [%] | ... | ... |
  | Specific Term | [N] | [%] | ... | ... |
  | Syntactic | [N] | [%] | ... | ... |
  | Metonymical | [N] | [%] | ... | ... |
  | Peristatic | [N] | [%] | ... | ... |

  ### 6. Итого

  - **Всего запросов:** [N]
  - **✓ Хорошо:** [N] ([%])
  - **~ Слабо:** [N] ([%])
  - **✗ Пусто:** [N] ([%])
  - **Fallback использован:** [N] раз — помог в [N] случаях
  - **Общий hit rate:** [%]

  ### 7. Рекомендации для улучшения скилла

  **По ключевым словам:**
  - [конкретная рекомендация: какие типы запросов формулировать иначе]

  **По выбору инструментов:**
  - [конкретная рекомендация: какие кейсы переназначить на другой инструмент]

  **По извлечению контента:**
  - [конкретная рекомендация: где добавить extract/crawl, где сменить подход]
")
```

### What the user sees

1. First: the synthesized research results (Phase 4 output) — delivered immediately
2. Then: the QA report appears when the background agent finishes — shown as a follow-up

**Format when showing the QA report to the user:**
```
---

## Отчёт по качеству поиска

[QA agent output here]
```

---

## Phase 4: Merge & Synthesize

**This runs IMMEDIATELY after search agents return, NOT waiting for QA audit.**

Combine findings from all 3 subagents into final output.

### 4.0 Save Results to File

**MANDATORY.** Two separate saves:

**A) Research file** — new file per research:
- Path: `CLOUD ZB (3600)/Researches/[topic-slug]-[YYYY-MM-DD].md`
- Include frontmatter: date, purpose, description
- Include: findings, search effectiveness
- Do NOT include QA audit here

**B) QA feedback log** — append to ONE cumulative file:
- Path: `CLOUD ZB (3600)/Researches/search-quality-log.md`
- If file doesn't exist, create it with header `# Search Quality Log`
- After QA audit agent completes, APPEND a new entry at the end of the file:

```markdown
---
## [YYYY-MM-DD] — [Topic]
**Queries:** [N] | **Hit rate:** [%] | **✓** [N] **~** [N] **✗** [N]

### Per-query scores
| # | Query | Tool | Useful/Total | Verdict |
[... condensed table ...]

### Tool performance
[... tool stats ...]

### Key lessons
- [what worked and why]
- [what failed and why]
- [new rules to add to operational-rules.md]
```

- Show the QA report to the user in chat as before
- Then append it to the log file

### 4.1 Merge

- Combine Key Findings from all rounds
- Deduplicate facts (same stat from different sources → keep best source)
- Note contradictions between rounds

### 4.2 Output

**Source attribution rule:** Inline hyperlink right after the fact it supports: `fact — [Source Name](URL)`. Do NOT collect sources into a separate table at the bottom.

```markdown
## Research: [Topic]

**Queries:** [N] | **Sources found:** [N] | **Rounds:** 3

### Key Findings
[Synthesized answer organized by themes/subtopics.
Each fact, statistic, or claim has an inline source link:
"fact or data — [Source Name](URL)"]

### Search Effectiveness

| Metric | Details |
|--------|---------|
| **Best slices** | [slice type] — [why it worked, example result] |
| **Failed slices** | [slice type] — [why it failed or returned noise] |
| **Gaps** | [what's missing] |
| **Follow-up queries** | `query 1`, `query 2` |
```

## Quick Reference

| Slice | Example |
|-------|---------|
| Regional | `AI news` → `actualités IA France` |
| Authority | `climate` → `IPCC report findings` |
| Source | `AI` → `site:arxiv.org transformer` |
| Specific Term | `coffee` → `anaerobic fermentation` |
| Syntactic | `report` → `filetype:pdf quarterly` |
| Metonymical | `blockchain` → `Byzantine fault tolerance` |
| Peristatic | `article` → `"absorbs 30 percent"` |
