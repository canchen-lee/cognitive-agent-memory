---
name: deep-consciousness
description: Deep Consciousness System — Working + Episodic + Semantic, a cognitive science-based memory architecture.
tags: [memory, architecture, persistence, agent, cognition]
author: CCL
---

# Deep Consciousness System

Cognitive science-based memory: Working memory → Episodic memory → Semantic memory.

## Architecture

```
WORKING                         ← Auto-injected every turn. <800 chars hard limit.
  ↓ topic ends, natural sink
EPISODIC                        ← On-demand recall by topic relevance.
  ↓ validated, corrected
SEMANTIC                        ← User model, corrections, cross-project knowledge.
```

## Key Rules

1. **WORKING.md hard cap: 800 characters.** Every char costs tokens every turn.
2. **Episodic: topic-based, not time-based.** Recall by relevance, not recency.
3. **Semantic: slow to build, never deleted.** User model and corrections compound over time.
4. **Auto-desensitization.** API keys, tokens, PII are blocked before writing.
5. **Correction capture.** User corrects the agent (e.g. "wrong", "no", "不对") → auto-save to corrections.md.

## SOUL.md / System Prompt Section

Add this to your agent's system prompt:

```markdown
## Deep Consciousness System
WORKING.md is auto-injected every turn — that is your working memory (<800 chars).
If the user references a topic not in WORKING.md, check episodic/topics.md by topic relevance.
Semantic layer (user-model.md, corrections.md) defines how to interact — load when behavior context is needed.
Never bulk-load any layer. Only load what's relevant to current conversation.
```

## Directory Structure

```
memories/
├── WORKING.md                    # Auto-injected, <800 chars
├── episodic/
│   ├── topics.md                 # Projects, decisions, rules by topic
│   └── index.json                # Keyword -> topic mapping
└── semantic/
    ├── user-model.md             # Communication style, decision patterns
    ├── corrections.md            # User corrections (never repeat mistakes)
    └── .gitkeep
```

## Token Budget

| Layer | Auto-inject | Max size | Recall method |
|-------|-------------|----------|---------------|
| WORKING | Every turn | 800 chars | Always loaded |
| EPISODIC | No | 3000 chars | Keyword match |
| SEMANTIC | No | No limit | On-demand |

## What NOT To Do

- Exceeding 800 chars in WORKING.md
- Bulk-loading episodic or semantic layers
- Storing sensitive info without desensitization
- Time-based archiving (use relevance-based)
- Duplicating content across layers

## Auto-Consolidation

Run `scripts/consolidate.py` daily (via cron). It:
1. Scans recent session transcripts
2. Auto-desensitizes (blocks API keys, tokens, PII)
3. Extracts decisions, rules, corrections
4. Enforces WORKING.md <300 char limit
5. Updates episodic/topics.md and index.json
6. Captures user corrections to semantic/corrections.md
