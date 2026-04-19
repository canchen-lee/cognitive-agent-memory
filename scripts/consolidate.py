#!/usr/bin/env python3
"""
Deep Consciousness System — Memory Consolidation
by CCL

Consolidation script for the deep consciousness memory system.

Features:
1. Scans recent session transcripts
2. Extracts key info (decisions, projects, rules)
3. Auto-desensitization (API key / PII blocking)
4. Enforces WORKING.md hard cap (300 chars)
5. Updates episodic/topics.md (topic-organized)
6. Updates episodic/index.json (keyword -> summary mapping)
7. Semantic layer updates (user-model / corrections)

Usage:
    python3 consolidate.py [--data-dir ~/.hermes] [--dry-run]
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


# ============ Config ============

DEFAULT_DATA_DIR = os.path.expanduser("~/.hermes")
WORKING_MAX_CHARS = 800       # WORKING.md hard cap
EPISODIC_MAX_CHARS = 3000     # episodic/topics.md soft cap
DRY_RUN = False

# ============ Sensitive Info Detection ============

SENSITIVE_PATTERNS = [
    # API keys (generic)
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\']?[\w\-]{20,}', '[REDACTED_API_KEY]'),
    # OpenAI / Anthropic / common API keys
    (r'(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9\-]{20,})', '[REDACTED_KEY]'),
    # GitHub tokens
    (r'(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})', '[REDACTED_GITHUB_TOKEN]'),
    # Generic passwords
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[\w\-]{6,}', '[REDACTED_PASSWORD]'),
    # Private keys
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', '[REDACTED_PRIVATE_KEY]'),
    # Phone numbers
    (r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b', '[REDACTED_PHONE]'),
]


def scan_sensitive(text: str) -> tuple[str, int]:
    """Scan text for sensitive info. Returns (cleaned_text, intercept_count)."""
    count = 0
    for pattern, replacement in SENSITIVE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            count += len(matches)
            text = re.sub(pattern, replacement, text)
    return text, count


def validate_safe(text: str) -> tuple[bool, str]:
    """Check if text is safe (no sensitive info)."""
    for pattern, _ in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            return False, f"Sensitive info detected: {pattern[:30]}..."
    return True, ""


# ============ Correction Detection ============

CORRECTION_KEYWORDS = ["不对", "错了", "不要", "别", "不是", "wrong", "no ", "don't"]


def detect_correction(user_message: str) -> str | None:
    """Detect if user message contains a correction. Returns correction text or None."""
    msg_lower = user_message.strip().lower()
    for kw in CORRECTION_KEYWORDS:
        if kw in msg_lower and len(user_message.strip()) > 3:
            return user_message.strip()
    return None


# ============ Utilities ============

def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_file_safe(path: Path, content: str):
    """Write file with desensitization check."""
    safe, reason = validate_safe(content)
    if not safe:
        print(f"  ! Blocked write to {path.name}: {reason}", file=sys.stderr)
        content, count = scan_sensitive(content)
        print(f"    Desensitized {count} items, proceeding")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ============ Working Memory Control ============

def enforce_working_limit(memories_dir: Path):
    """Check WORKING.md, truncate if over limit."""
    working_path = memories_dir / "WORKING.md"
    content = read_file(working_path)
    if not content:
        return

    if len(content) > WORKING_MAX_CHARS:
        lines = content.split("\n")
        truncated = []
        length = 0
        for line in lines:
            if length + len(line) + 1 > WORKING_MAX_CHARS:
                break
            truncated.append(line)
            length += len(line) + 1
        truncated.append(f"\n> Truncated: was {len(content)} chars, compressed to {length}")
        write_file_safe(working_path, "\n".join(truncated))
        print(f"  ! WORKING.md truncated: {len(content)} -> {length} chars")
    else:
        print(f"  OK WORKING.md ({len(content)}/{WORKING_MAX_CHARS} chars)")


# ============ Session Scanning ============

def get_recent_sessions(sessions_dir: Path, days: int = 1):
    if not sessions_dir.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for f in sessions_dir.glob("*.json"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime >= cutoff:
                recent.append(f)
        except (OSError, ValueError):
            continue
    return sorted(recent)


def extract_key_points(session_text: str) -> dict:
    """Extract key information from session text."""
    decisions, rules, projects, corrections = [], [], [], []

    for line in session_text.split("\n"):
        line = line.strip()
        if not line or len(line) > 300:
            continue

        line_lower = line.lower()
        if any(kw in line_lower for kw in ["decided", "switch to", "moving to", "going with"]):
            decisions.append(line[:200])
        if any(kw in line_lower for kw in ["rule", "must", "never", "always", "forbidden"]):
            rules.append(line[:200])
        if any(kw in line_lower for kw in ["project", "task", "feature", "milestone"]):
            projects.append(line[:200])

        correction = detect_correction(line)
        if correction:
            corrections.append(correction[:200])

    return {
        "decisions": decisions[:10],
        "rules": rules[:10],
        "projects": projects[:10],
        "corrections": corrections[:10],
    }


# ============ Update Semantic Layer ============

def update_corrections(memories_dir: Path, new_corrections: list[str]):
    """Append corrections to semantic/corrections.md."""
    if not new_corrections:
        return

    corr_path = memories_dir / "semantic" / "corrections.md"
    content = read_file(corr_path)
    today = datetime.now().strftime("%Y-%m-%d")

    insert_marker = "## Rules (sorted by weight"
    if insert_marker in content:
        new_lines = "\n".join(f"- {c} | weight: 1 | first: {today} | last: {today}" for c in new_corrections[:5])
        content = content.replace(
            insert_marker,
            f"{new_lines}\n\n{insert_marker}"
        )
        write_file_safe(corr_path, content)
        print(f"  OK semantic/corrections.md: added {len(new_corrections[:5])} corrections")


# ============ Update Episodic Layer ============

def update_episodic(memories_dir: Path, summary: dict):
    """Update episodic/topics.md."""
    topics_path = memories_dir / "episodic" / "topics.md"
    content = read_file(topics_path)
    today = datetime.now().strftime("%Y-%m-%d")

    if not content:
        return

    if summary["decisions"]:
        decisions_block = "\n".join(f"- {d}" for d in summary["decisions"][:3])
        if "## Decisions" in content:
            content = content.replace(
                "## Decisions\n",
                f"## Decisions\n{decisions_block}\n"
            )

    if summary["rules"]:
        rules_block = "\n".join(f"- {r}" for r in summary["rules"][:3])
        if "## Rules" in content:
            content = content.replace(
                "## Rules\n",
                f"## Rules\n{rules_block}\n"
            )

    write_file_safe(topics_path, content)
    print(f"  OK episodic/topics.md updated")


# ============ Update Index ============

def update_index(memories_dir: Path, summary: dict):
    """Update episodic/index.json keyword mapping."""
    index_path = memories_dir / "episodic" / "index.json"
    index = load_json(index_path)

    if not index:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    index["last_updated"] = today

    existing_kws = {t["keyword"] for t in index.get("topics", [])}
    for project in summary["projects"][:3]:
        kw = project[:20].strip()
        if kw and kw not in existing_kws:
            index["topics"].append({
                "keyword": kw,
                "weight": 50,
                "file": "episodic/topics.md",
                "section": "Projects",
                "summary": project[:100],
            })

    save_json(index_path, index)
    print(f"  OK episodic/index.json updated")


# ============ Main ============

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deep Consciousness System — Consolidation")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Hermes data directory")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, no writes")
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run

    data_dir = Path(args.data_dir)
    memories_dir = data_dir / "memories"

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Deep consciousness consolidation started")
    if DRY_RUN:
        print(f"  Dry run mode")

    # 1. Scan
    print("\n[1/5] Scanning sessions...")
    sessions_dir = data_dir / "sessions"
    recent = get_recent_sessions(sessions_dir, days=1)

    all_decisions, all_rules, all_projects, all_corrections = [], [], [], []
    for sf in recent:
        try:
            content = read_file(sf)
            pts = extract_key_points(content)
            all_decisions.extend(pts["decisions"])
            all_rules.extend(pts["rules"])
            all_projects.extend(pts["projects"])
            all_corrections.extend(pts["corrections"])
        except Exception as e:
            print(f"  Skipped {sf.name}: {e}", file=sys.stderr)

    summary = {
        "decisions": all_decisions,
        "rules": all_rules,
        "projects": all_projects,
        "corrections": all_corrections,
    }
    print(f"  Scanned {len(recent)} sessions")

    # 2. Desensitization check
    print("\n[2/5] Sensitive info scan...")
    all_text = " ".join(all_decisions + all_rules + all_projects)
    _, intercept_count = scan_sensitive(all_text)
    if intercept_count:
        print(f"  ! Found {intercept_count} sensitive items, will auto-desensitize")
    else:
        print(f"  OK No sensitive info found")

    # 3. Update episodic
    print("\n[3/5] Updating episodic/...")
    if not DRY_RUN:
        update_episodic(memories_dir, summary)
        update_index(memories_dir, summary)

    # 4. Update semantic
    print("\n[4/5] Updating semantic/...")
    if not DRY_RUN:
        update_corrections(memories_dir, all_corrections)

    # 5. Token control
    print("\n[5/5] Token budget check...")
    if not DRY_RUN:
        enforce_working_limit(memories_dir)

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Consolidation complete")


if __name__ == "__main__":
    main()
