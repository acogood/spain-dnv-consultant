"""
build_digest.py — turn curated practice claims + anonymized slices into a
PUBLISHABLE, de-identified digest.

This is the ONLY chat-derived artifact that may ship to the public repo. It
contains, per claim: a human-curated statement, a confidence tag, a coarse
SUPPORT BAND (how many DISTINCT pseudonymous authors back it), and a
year-month date range. It deliberately does NOT contain raw messages, message
ids, author pseudonyms, or the salt — publishing pseudo-keys against a known
roster + public salt would be reversible (KTD4).

Privacy controls:
  * Distinct-author counting over salted pseudonyms (from anonymize_chat.py).
  * k-anonymity suppression: a claim backed by fewer than --min-authors
    distinct people is DROPPED (an individual opinion is re-identifiable and is
    not "practice").
  * Counts are reported as BANDS, never exact numbers.
Determinism: no randomness — given the same curation file + slices the digest
(and its bands) are exactly reproducible.

Curation file (JSON):
  {
    "last_covered_date": "YYYY-MM-DD",
    "source": "free-text provenance, PII-free",
    "claims": [
      {
        "topic": "доход_IPREM",
        "tag": "практика — Telegram",
        "statement": "PII-free human-written claim.",
        "supporting_ids": [123, 456],        # explicit (LLM-curated) — optional
        "match": ["regex1", "regex2"]        # auto-discovery helper — optional
      }
    ]
  }
A claim may use supporting_ids, match, or both. At least one is required.

Usage:
  python build_digest.py --curation FILE --slices-dir DIR --out-dir DIR [options]
  python build_digest.py --curation FILE --slices a.json b.json --out-dir DIR
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

from _common import (  # noqa: E402
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_DEPTH,
    SafeIOError,
    die,
    load_json_safe,
    messages_of,
    resolve_output,
)


def support_band(d: int) -> str:
    if d <= 4:
        return "немного (2–4 чел.)"
    if d <= 9:
        return "несколько (5–9 чел.)"
    if d <= 19:
        return "многие (10–19 чел.)"
    if d <= 49:
        return "массово (20–49 чел.)"
    if d <= 99:
        return "массово (50–99 чел.)"
    return "массово (100+ чел.)"


def year_month(date_str) -> str | None:
    if not isinstance(date_str, str) or len(date_str) < 7:
        return None
    return date_str[:7]  # "YYYY-MM"


def date_range(dates: list[str]) -> str:
    yms = sorted(d for d in (year_month(x) for x in dates) if d)
    if not yms:
        return "—"
    return yms[0] if yms[0] == yms[-1] else f"{yms[0]} — {yms[-1]}"


def load_slices(slice_paths, max_bytes, max_depth) -> list[dict]:
    """Load + concatenate anonymized message lists. Validates each carries the
    'author' field produced by anonymize_chat.py (fail-closed: refuse raw,
    un-anonymized input so we never aggregate over real identities)."""
    all_msgs: list[dict] = []
    for p in slice_paths:
        data = load_json_safe(p, max_bytes=max_bytes, max_depth=max_depth)
        msgs = messages_of(data)
        for m in msgs:
            if not isinstance(m, dict):
                continue
            if "author" not in m:
                raise SafeIOError(
                    f"{p}: messages have no 'author' field — input does not look "
                    f"anonymized. Run anonymize_chat.py first (refusing to build a "
                    f"digest over possibly-real identities)."
                )
            all_msgs.append(m)
    return all_msgs


def aggregate(curation: dict, messages: list[dict], min_authors: int):
    by_id = {m.get("id"): m for m in messages if m.get("id") is not None}

    published, suppressed = [], []
    for claim in curation.get("claims", []):
        statement = claim.get("statement", "").strip()
        if not statement:
            continue
        ids = set(claim.get("supporting_ids") or [])
        regexes = [re.compile(r, re.IGNORECASE) for r in (claim.get("match") or [])]
        topic = claim.get("topic")

        supporters = {}  # author -> list of dates
        # explicit ids
        for mid in ids:
            m = by_id.get(mid)
            if m:
                supporters.setdefault(m.get("author"), []).append(m.get("date"))
        # regex auto-discovery (optionally scoped to the claim's topic)
        if regexes:
            for m in messages:
                if topic and isinstance(m.get("topics"), list) and topic not in m["topics"]:
                    continue
                text = m.get("text") or ""
                if any(rx.search(text) for rx in regexes):
                    supporters.setdefault(m.get("author"), []).append(m.get("date"))

        supporters.pop(None, None)
        supporters.pop("u_anon", None)  # never count anonymous bucket as a person
        distinct = len(supporters)

        record = {
            "topic": topic,
            "tag": claim.get("tag", "практика — Telegram"),
            "statement": statement,
        }
        if distinct < min_authors:
            record["distinct_authors"] = distinct
            suppressed.append(record)
            continue

        all_dates = [d for ds in supporters.values() for d in ds]
        record["support"] = support_band(distinct)
        record["period"] = date_range(all_dates)
        published.append(record)

    return published, suppressed


def render_markdown(curation: dict, published: list[dict]) -> str:
    lines = [
        "# Дайджест практики сообщества (обезличенный)",
        "",
        "> **Это не закон и не официальное разъяснение.** Агрегированные наблюдения "
        "из публичных Telegram-сообществ: что заявители *сообщают* о своём опыте. "
        "Telegram = мнение, не норма. Проверяйте каждый пункт против актуальных "
        "источников (см. `knowledge_base/norms/`).",
        "",
        "> **Приватность.** Здесь нет сырых сообщений, идентификаторов, имён авторов "
        "и псевдо-ключей — только курируемые утверждения, диапазон по числу *разных* "
        "людей (band) и период. Пункты, подтверждённые единичными авторами, "
        "исключены (k-анонимность).",
        "",
        f"- **Источник:** {curation.get('source', '—')}",
        f"- **LAST_COVERED_DATE:** {curation.get('last_covered_date', '—')}",
        f"- **Опубликовано пунктов:** {len(published)}",
        "",
    ]
    by_topic: dict[str, list[dict]] = {}
    for r in published:
        by_topic.setdefault(r.get("topic") or "прочее", []).append(r)
    for topic in sorted(by_topic):
        lines.append(f"## {topic}")
        lines.append("")
        for r in by_topic[topic]:
            lines.append(f"- {r['statement']}")
            lines.append(f"  - _по теме высказывались:_ {r['support']} · _период:_ {r['period']} · `[{r['tag']}]`")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a de-identified practice digest.")
    ap.add_argument("--curation", required=True)
    ap.add_argument("--slices", nargs="*", default=[])
    ap.add_argument("--slices-dir", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--allowed-root", default=".")
    ap.add_argument("--min-authors", type=int, default=2,
                    help="k-anonymity floor: drop claims backed by fewer distinct people")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    args = ap.parse_args(argv)

    try:
        slice_paths = list(args.slices)
        if args.slices_dir:
            slice_paths += sorted(str(p) for p in Path(args.slices_dir).glob("*.json"))
        if not slice_paths:
            raise SafeIOError("No slices given (use --slices or --slices-dir).")

        curation = load_json_safe(args.curation, max_bytes=args.max_bytes, max_depth=args.max_depth)
        if not isinstance(curation, dict) or "claims" not in curation:
            raise SafeIOError("Curation file must be an object with a 'claims' array.")

        messages = load_slices(slice_paths, args.max_bytes, args.max_depth)
        published, suppressed = aggregate(curation, messages, args.min_authors)

        out_dir = resolve_output(args.out_dir, args.allowed_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "digest.md").write_text(render_markdown(curation, published), encoding="utf-8")
        (out_dir / "digest.json").write_text(
            json.dumps({"source": curation.get("source"),
                        "last_covered_date": curation.get("last_covered_date"),
                        "min_authors": args.min_authors,
                        "claims": published}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        lcd = curation.get("last_covered_date", "")
        (out_dir / "LAST_COVERED_DATE").write_text(str(lcd) + "\n", encoding="utf-8")
    except SafeIOError as e:
        die(e)

    print(f"messages={len(messages)} published={len(published)} suppressed(k-anon)={len(suppressed)}")
    for r in suppressed:
        print(f"  suppressed [{r.get('distinct_authors')} автор(ов)]: {r['statement'][:60]}...")
    print(f"-> {out_dir}/digest.md, digest.json, LAST_COVERED_DATE")


if __name__ == "__main__":
    main()
