---
description: vibecoding and programming any type of code
alwaysApply: false
---

# My Setup
- MacBook Pro M1
- 16 GB RAM
- Default browser: Google Chrome
- Phone: iPhone 16 pro
- IDE: Cursor with Claude Code extension for chatting with AI
- Hosting: Railway

# MCP Tools
- Default web search: use built-in **WebSearch** tool
- **Tavily** — use only inside skills that explicitly require it (Deep-web-search, etc.). Config: `~/.claude.json` → global `mcpServers.tavily`
- **Exa** — use only when need date/domain/category filters. ALWAYS use `web_search_advanced_exa` (not `web_search_exa`). Config: `~/.claude.json` → `projects.<path>.mcpServers`, tools via CLI arg `tools=tool1,tool2`

# My bio
- I am Victor Buto, a 29 y.o. russian male living in Moscow 
- I work as head of research in a branding agency. We do branding, digital products (websites mostly) and brand strategies. 
- I'm responsible for developing research department: commerce, production, people management
- we do indepth interviews, focus groups, UX research, online surveys, SML and desk research
- I have deep expertise in go-to-market research, segmentation, JTBD
- I have telegram channel about research and brand strategies and make videos on history of ideas (study how they become influential)


# ​​General Guidelines

## Before doing anything
1) Search the repo folder in /Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600) for existing files before creating a new one.
2) Read project context
3) If the request is ambiguous, ask up to 3 clarifying questions.
4) Use web search when research is needed 

## File Management
- All new files create within "Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)", not otside, and within the folder of a project / file you're working with
- Use clear, descriptive file and folder names
- For each new project create UNIQUE slug&name - project-name.
- For each new project create its own folder
- Don't base your answer on other project. Make each project unique from scratch.
- Maintain logical organization structure
- Keep related materials grouped together
- Regular cleanup and organization of outdated content
- Always reference actual file paths when suggesting connections
- **NEVER overwrite or merge into existing files.** Always create a new separate file. For research — always a new file.

# Documentation
- Readme should contain Title, Description and Features. 
- When you add something new - update readme.
- Each text file with descriptions should contain meta data: data of update, purpose of a document and brief description of a content

## Skills
- Default path for all new skills: `/Users/fixed/Documents/ZB CLOUD 3600/.claude/skills/`
- When using skill-creator, always pass `--path "/Users/fixed/Documents/ZB CLOUD 3600/.claude/skills/"` to init_skill.py
- When packaging, always output to `/Users/fixed/Documents/ZB CLOUD 3600/.claude/skills/`

## Answer rules
- Answer with short and precise comments that will be easy to comprehend for a person who know little about programming
- When adding a new code explain shortly what was done and solutions were used
