#!/usr/bin/env python3
"""
merge_chat_dumps.py — merge two or more raw Telegram exports of the SAME chat.

Pipeline position: MERGE -> anonymize -> filter -> slice. Run this first when
you have overlapping exports (e.g. an old backup + a fresh dump): it dedups by
message id and sorts by time, so re-importing an overlapping range adds zero
duplicates (idempotent).

Usage:
  python merge_chat_dumps.py <in1.json> <in2.json> [<in3.json>...] <out.json> [options]

Options:
  --allowed-root DIR   confine output under this dir (default: cwd)
  --max-bytes N        per-file size limit (default 512 MiB)
  --max-depth N        JSON nesting limit (default 200)
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
    DEFAULT_MAX_BYTES, DEFAULT_MAX_DEPTH, SafeIOError, die, load_json_safe, resolve_output,
)


def merge(input_paths, max_bytes, max_depth):
    merged = None
    seen = set()
    total_in = 0
    for p in input_paths:
        data = load_json_safe(p, max_bytes=max_bytes, max_depth=max_depth)
        if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
            raise SafeIOError(f"{p}: expected a Telegram export object with a 'messages' array.")
        if merged is None:
            merged = {k: v for k, v in data.items() if k != "messages"}
            merged["messages"] = []
        total_in += len(data["messages"])
        for m in data["messages"]:
            mid = m.get("id") if isinstance(m, dict) else None
            if mid is None or mid in seen:
                continue
            seen.add(mid)
            merged["messages"].append(m)

    def sort_key(m):
        ts = m.get("date_unixtime")
        if ts is not None:
            try:
                return (0, int(ts))
            except (TypeError, ValueError):
                pass
        return (1, m.get("id") or 0)

    merged["messages"].sort(key=sort_key)
    return merged, total_in


def main(argv=None):
    ap = argparse.ArgumentParser(description="Merge + dedup raw Telegram exports.")
    ap.add_argument("paths", nargs="+", help="<in1> <in2> [...] <out>")
    ap.add_argument("--allowed-root", default=".")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    args = ap.parse_args(argv)

    if len(args.paths) < 3:
        ap.error("need at least two inputs and one output")
    *inputs, output = args.paths

    try:
        out_path = resolve_output(output, args.allowed_root)
        merged, total_in = merge(inputs, args.max_bytes, args.max_depth)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    except SafeIOError as e:
        die(e)

    out_n = len(merged["messages"])
    print(f"in={total_in} out={out_n} dedup={total_in - out_n}")
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
