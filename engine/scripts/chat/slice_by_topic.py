#!/usr/bin/env python3
"""
slice_by_topic.py — extract per-topic slices from a filtered (anonymized) chat.

Pipeline position: merge -> anonymize -> filter -> SLICE. Produces one file per
topic (with 1-level thread context) so downstream skills can Grep a small,
relevant slice instead of the whole corpus.

Usage:
  python slice_by_topic.py <filtered_in.json> <out_dir> [topic ...] [options]
  python slice_by_topic.py <filtered_in.json> <out_dir> all
"""

from __future__ import annotations

import argparse
import io
import json
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


def slice_topic(messages, topic):
    topic_ids = {m["id"] for m in messages if topic in m.get("topics", [])}
    ids = set(topic_ids)
    for m in messages:
        if m.get("reply_to") in topic_ids:
            ids.add(m["id"])
        if m["id"] in topic_ids and m.get("reply_to"):
            ids.add(m["reply_to"])
    return [m for m in messages if m["id"] in ids]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Slice filtered chat by topic.")
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("topics", nargs="*", default=["all"])
    ap.add_argument("--allowed-root", default=".")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    args = ap.parse_args(argv)

    try:
        out_dir = resolve_output(args.out_dir, args.allowed_root)
        data = load_json_safe(args.input, max_bytes=args.max_bytes, max_depth=args.max_depth)
        messages = messages_of(data)

        available = sorted({t for m in messages for t in m.get("topics", []) if t != "thread_context"})
        requested = args.topics or ["all"]
        if "all" in requested:
            requested = available

        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for topic in requested:
            if topic not in available:
                print(f"unknown topic: {topic} (available: {', '.join(available)})")
                continue
            result = slice_topic(messages, topic)
            out_file = out_dir / f"topic_{topic}.json"
            out_file.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
            written.append((topic, len(result), out_file))
    except SafeIOError as e:
        die(e)

    for topic, n, f in written:
        print(f"  {topic}: {n} msgs -> {f.name}")
    print(f"-> {out_dir}")


if __name__ == "__main__":
    main()
