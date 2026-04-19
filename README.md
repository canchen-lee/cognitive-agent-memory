# Cognitive Agent Memory System

### A lightweight memory architecture for AI agents

Inspired by cognitive science — working, episodic, and semantic memory — this system is designed to address cross-session forgetting in AI agents, originally developed for Hermes.

## TL;DR

- Preserves context across sessions
- Zero dependencies (no vector DB, no API calls)
- Token-efficient (<800 chars working memory)
- Topic-based recall instead of time-based logs

## Why

Starting a fresh conversation with an AI agent should feel like picking up where you left off — not re-explaining everything from scratch. But that's exactly what happens. Every session starts blank. Decisions you made together are gone. Preferences you corrected a dozen times come right back. The agent asks "who?" about someone you spent hours discussing yesterday.

Human memory doesn't work like this. We don't recall everything equally — recent memories are vivid and instantly accessible, older ones fade but can be retrieved with effort, and truly ancient knowledge sits deep until something triggers it.

This system models that. Not a dump of everything into one growing file. Not a complex hook system with background services. Just a layered structure where fresh context is always at hand, recent knowledge is one search away, and deep archives wait silently until needed.

## Architecture

```
WORKING                         ← Auto-injected every turn. <800 chars hard limit.
  ↓ topic ends, natural sink
EPISODIC                        ← On-demand recall by topic relevance.
  ↓ validated, corrected
SEMANTIC                        ← User model, corrections, cross-project knowledge.
```

## Key Features

- **Token budget control** — WORKING.md hard cap at 800 characters
- **Auto-desensitization** — API keys, tokens, PII blocked before writing
- **Correction capture** — User feedback auto-saved and weighted
- **Topic-based recall** — Not time-based, relevance-driven
- **Zero dependencies** — Pure markdown + Python, no vector DB, no API calls

## Directory Structure

```
deep-consciousness/
├── README.md
├── SKILL.md                        # Design doc for agents
├── memories/                       # Template directory, ready to use
│   ├── WORKING.md                  # Working memory (<800 chars, auto-injected)
│   ├── episodic/
│   │   ├── topics.md               # Projects, decisions, rules by topic
│   │   └── index.json              # Keyword -> topic mapping
│   └── semantic/
│       ├── user-model.md           # Communication style, decision patterns
│       └── corrections.md          # User corrections (never repeat mistakes)
├── examples/                       # Real-world examples (sanitized)
└── scripts/
    └── consolidate.py              # Daily auto-consolidation script
```

## Quick Start

### 1. Copy memories/ to your Hermes data directory

```bash
cp -r memories/ ~/.hermes/memories/
```

### 2. Add system prompt section

Add this to SOUL.md or your system prompt:

```markdown
## Deep Consciousness System
WORKING.md is auto-injected every turn — that is your working memory (<800 chars).
If the user references a topic not in WORKING.md, check episodic/topics.md by topic relevance.
Semantic layer (user-model.md, corrections.md) defines how to interact — load when behavior context is needed.
Never bulk-load any layer. Only load what's relevant to current conversation.
```

### 3. Set up daily auto-consolidation

Copy the consolidation script:

```bash
cp scripts/consolidate.py ~/.hermes/scripts/
```

Option A — system crontab:

```bash
crontab -e
0 3 * * * /usr/bin/python3 ~/.hermes/scripts/consolidate.py >> ~/.hermes/logs/memory_consolidate.log 2>&1
```

Option B — Hermes built-in cron:

```
cronjob create --schedule "0 3 * * *" --prompt "Run memory consolidation: scan recent sessions, update WORKING.md, episodic/topics.md, index.json, capture corrections to semantic/corrections.md"
```

Preview without writing:

```bash
python3 scripts/consolidate.py --data-dir ~/.hermes --dry-run
```

## Core Rules

1. **WORKING.md hard cap: 800 chars.** Every char costs tokens every turn.
2. **Episodic: topic-based, not time-based.** Recall by relevance, not recency.
3. **Semantic: slow to build, never deleted.** User model and corrections compound over time.
4. **Auto-desensitization.** API keys, tokens, PII are blocked before writing.
5. **Correction capture.** User corrects the agent (e.g. "wrong", "no", "不对") → auto-save to corrections.md.

## Token Budget

| Layer | Auto-inject | Max size | Recall method |
|-------|-------------|----------|---------------|
| WORKING | Every turn | 800 chars | Always loaded |
| EPISODIC | No | 3000 chars | Keyword match |
| SEMANTIC | No | No limit | On-demand |

## Auto-Consolidation

`scripts/consolidate.py` runs daily via cron. It:

1. Scans recent session transcripts
2. Auto-desensitizes (blocks API keys, tokens, PII)
3. Extracts decisions, rules, corrections
4. Enforces WORKING.md <800 char limit
5. Updates episodic/topics.md and index.json
6. Captures user corrections to semantic/corrections.md

## Contributing

This system is under active development. Feedback, suggestions, and pull requests are welcome. The design may be idealistic in places — if something doesn't work or could be improved, don't hesitate to say so.

---

# 中文说明

## 这是什么

认知型 Agent 记忆系统

受认知科学启发（工作记忆、情景记忆、语义记忆），该系统旨在缓解 AI Agent 在跨会话中的遗忘问题，最初基于 Hermes 的使用场景构建。

## TL;DR

- 跨会话保留上下文，不再从零开始
- 零依赖（无需向量数据库或外部 API）
- 高效控制 token（工作记忆 <800 字符）
- 按话题召回，而非按时间堆积日志

## 为什么需要它

每一次重新开对话，都应该像接着上次聊——而不是把一切从头解释一遍。但现实就是这样：每次启动都是白板，一起做的决定没了，纠正过十几次的偏好又回来了，昨天花了几小时讨论的人，今天问你"是谁？"

人类记忆不是这样运作的。我们不会平等地回忆所有事情——近期的记忆清晰且随时可取，久远的记忆会模糊但稍微努力就能想起来，更深的知识埋在底层，直到某个触发点才会浮现。

这套系统模拟的就是这种机制。不是一个无限膨胀的文件，也不是一套需要后台服务的复杂 hook 系统。就是分层结构：新鲜的上下文触手可及，近期知识一次搜索就能找到，深层档案静静等着，需要时才唤醒。

## 架构

- **WORKING（工作记忆）** — 每轮自动注入，硬上限 800 字符。只放当前任务和关键决策。
- **EPISODIC（情景记忆）** — 按需召回，按话题组织。放项目状态、决策记录、工具/规则。
- **SEMANTIC（语义记忆）** — 长期积累。用户行为模型、纠错记录、跨项目知识。

## 核心特色

- **Token 预算控制** — 工作记忆 800 字符硬上限
- **自动脱敏** — 写入前拦截 API key、token、个人隐私
- **纠错捕获** — 用户说"不对"时自动记录，永远不再犯
- **按话题召回** — 不按时间排序，按相关性加载
- **零依赖** — 纯 markdown + Python，不用向量数据库

## 快速开始

1. 复制 `memories/` 到 `~/.hermes/memories/`
2. 在系统提示里加一段 Memory System 说明（见上方英文部分）
3. 设置每日自动整理 cron（`scripts/consolidate.py`）

支持 `--dry-run` 预览模式，不写入任何文件。

## 参与

该系统仍在积极开发中，欢迎提交建议与改进方案。设计初衷可能过于理想化，如果发现任何问题或有更好的思路，欢迎随时指出。

---

**Author:** Li Canchen
