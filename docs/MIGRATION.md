# Migration & Troubleshooting

Known issues encountered during real-world deployment. Read this before installing.

## Python 3.9 Compatibility

**Problem:** `consolidate.py` fails with `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`

**Cause:** Python 3.9 doesn't support `str | None` or `list[Path]` type annotation syntax (requires 3.10+).

**Fix:** Already applied in the script — added `from __future__ import annotations` at the top and removed bare `list[Path]` return type. If you're editing the script, use these patterns:

```python
# OK on 3.9+
from __future__ import annotations
def func(x: str) -> str | None:  # works with future import
    ...

# Also OK
from typing import Optional, List
def func(x: str) -> Optional[str]:  # universal
    ...

# BAD on 3.9 (without future import)
def func(x: str) -> str | None:  # TypeError!
    ...
```

## MEMORY.md Bridge Pattern

**Problem:** Hermes auto-injects `MEMORY.md` every turn. If you rename it to `WORKING.md`, the auto-injection stops working.

**Solution:** Keep `MEMORY.md` as a lightweight bridge file that points to the new system:

```markdown
# Deep Consciousness System — Bridge
> This file is auto-injected. For current rules, see WORKING.md.
> For project context, see episodic/topics.md.

## Core Rules
- [keep only the most essential rules here, <500 chars]

## Index
→ WORKING.md | episodic/topics.md | semantic/user-model.md
```

The bridge file should stay under 500 characters. All real content lives in the new structure.

## Directory Layout (after migration)

```
~/.hermes/memories/
├── MEMORY.md              # Bridge file (auto-injected by Hermes), <500 chars
├── USER.md                # Keep for compatibility
├── WORKING.md             # Working memory, <800 chars hard cap
├── episodic/
│   ├── topics.md          # Projects, decisions, rules by topic
│   └── index.json         # Keyword -> topic mapping
├── semantic/
│   ├── user-model.md      # Communication style, decision patterns
│   └── corrections.md     # User corrections log
├── cold/                  # Old archives (keep as-is)
├── hot.md                 # Old file (can be removed after verification)
├── index.json             # Old file (can be removed after verification)
└── scripts/
    └── consolidate.py     # Daily consolidation script
```

## Cron Setup

```bash
# System crontab
crontab -e
0 3 * * * /usr/bin/python3 ~/.hermes/scripts/consolidate.py --data-dir ~/.hermes >> ~/.hermes/logs/consolidation.log 2>&1
```

Or use Hermes built-in cron:

```
cronjob create --schedule "0 3 * * *" --prompt "Run: python3 ~/.hermes/scripts/consolidate.py --data-dir ~/.hermes"
```

## Verification

After installation, verify everything works:

```bash
# Dry run (no writes)
python3 scripts/consolidate.py --data-dir ~/.hermes --dry-run

# Real run
python3 scripts/consolidate.py --data-dir ~/.hermes

# Check file sizes
wc -c memories/WORKING.md          # Should be <= 800
wc -c ~/.hermes/memories/MEMORY.md # Bridge, should be <= 500
```

## Backup Before Migrating

Always back up before changing the memory system:

```bash
cp -r ~/.hermes/memories/ ~/.hermes/memories_backup_$(date +%Y%m%d_%H%M%S)
```

To restore from backup:

```bash
cp -r ~/.hermes/memories_backup_YYYYMMDD_HHMMSS/* ~/.hermes/memories/
```
