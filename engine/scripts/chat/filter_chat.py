#!/usr/bin/env python3
"""
filter_chat.py — keyword-filter an ANONYMIZED chat list by DNV-relevant topics
and reconstruct 1-level reply threads for context.

Pipeline position: merge -> anonymize -> FILTER -> slice. Input must already be
anonymized (messages carry `author`, not `from`); this script refuses raw input
so you never filter over real identities.

Keyword groups live in a config JSON (default: ../config.example.json) so you
can tune topics without editing code.

Usage:
  python filter_chat.py <anon_in.json> <filtered_out.json> [--config FILE] [options]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_MAX_BYTES, DEFAULT_MAX_DEPTH, SafeIOError, die, load_json_safe,
    messages_of, resolve_output,
)

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.example.json"


def load_config(path):
    cfg = load_json_safe(path, max_bytes=4 * 1024 * 1024, max_depth=20)
    groups = cfg.get("keyword_groups")
    if not isinstance(groups, dict) or not groups:
        raise SafeIOError(f"{path}: 'keyword_groups' missing or empty.")
    compiled = {}
    for name, patterns in groups.items():
        if not isinstance(patterns, list):
            raise SafeIOError(f"{path}: keyword_groups['{name}'] must be a list.")
        try:
            compiled[name] = [re.compile(p, re.IGNORECASE) for p in patterns]
        except re.error as e:
            raise SafeIOError(f"{path}: bad regex in '{name}': {e}")
    return compiled, int(cfg.get("min_text_len", 40))


def match_topics(text, compiled):
    out = []
    for group, patterns in compiled.items():
        if any(p.search(text) for p in patterns):
            out.append(group)
    return out


def filter_messages(messages, compiled, min_len):
    # Fail-closed: input must be anonymized.
    for m in messages[:50]:
        if isinstance(m, dict) and "from" in m and "author" not in m:
            raise SafeIOError(
                "Input looks raw (has 'from', no 'author'). Run anonymize_chat.py "
                "first — filtering must run on anonymized data."
            )
    by_id = {m["id"]: m for m in messages if isinstance(m, dict) and "id" in m}

    matched, topics_of = set(), {}
    for m in messages:
        text = m.get("text") or ""
        if len(text) < min_len:
            continue
        t = match_topics(text, compiled)
        if t:
            matched.add(m["id"])
            topics_of[m["id"]] = t

    thread = set(matched)
    for mid in list(matched):
        cur = by_id.get(mid)
        if cur and cur.get("reply_to"):
            parent = by_id.get(cur["reply_to"])
            if parent and len(parent.get("text") or "") >= min_len:
                thread.add(cur["reply_to"])
    for m in messages:
        if m.get("reply_to") in matched and len(m.get("text") or "") >= min_len:
            thread.add(m["id"])

    out = []
    for m in messages:
        if m.get("id") not in thread:
            continue
        entry = dict(m)  # already anonymized (keep-allowlist enforced upstream)
        entry["topics"] = topics_of.get(m["id"], ["thread_context"])
        out.append(entry)
    return out, matched


def main(argv=None):
    ap = argparse.ArgumentParser(description="Filter anonymized chat by topic keywords.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--allowed-root", default=".")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    args = ap.parse_args(argv)

    try:
        out_path = resolve_output(args.output, args.allowed_root)
        compiled, min_len = load_config(args.config)
        data = load_json_safe(args.input, max_bytes=args.max_bytes, max_depth=args.max_depth)
        messages = messages_of(data)
        out, matched = filter_messages(messages, compiled, min_len)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    except SafeIOError as e:
        die(e)

    counts = {}
    for m in out:
        for t in m["topics"]:
            counts[t] = counts.get(t, 0) + 1
    print(f"total={len(messages)} matched={len(matched)} with_context={len(out)}")
    for t, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
