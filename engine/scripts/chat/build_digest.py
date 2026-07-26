"""
build_digest.py — turn curated practice claims + anonymized slices into a
PUBLISHABLE, de-identified digest.

This is the ONLY chat-derived artifact that may ship to the public repo. It
contains, per claim: a human-curated statement, a confidence tag, a coarse
SUPPORT BAND (how many DISTINCT pseudonymous authors back it), and a
year-month date range. It deliberately does NOT contain raw messages, message
ids, author pseudonyms, or the salt — publishing pseudo-keys against a known
roster + public salt would be reversible.

Privacy controls:
  * Distinct-author counting over salted pseudonyms (from anonymize_chat.py).
  * k-anonymity suppression: a claim backed by fewer than --min-authors
    distinct people is DROPPED (an individual opinion is re-identifiable and is
    not "practice").
  * Counts are reported as BANDS, never exact numbers.
Determinism: no randomness — given the same curation file + slices the digest
(and its bands) are exactly reproducible.

Coverage date: LAST_COVERED_DATE is DERIVED from the newest message in the
slices, not copied from the curation file. `curation.last_covered_date` is an
optional FLOOR — if it claims more coverage than the data has, that mismatch is
printed as a warning and the corpus date is published anyway (warning, not gate).

Curation file (JSON):
  {
    "last_covered_date": "YYYY-MM-DD",  # optional floor; corpus date wins
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


NO_DATES = "—"  # module-wide marker for "no parseable dates" (see date_range)
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def year_month(date_str) -> str | None:
    if not isinstance(date_str, str) or len(date_str) < 7:
        return None
    return date_str[:7]  # "YYYY-MM"


def iso_day(date_str) -> str | None:
    """'2026-07-24T18:30:00' -> '2026-07-24'. Same guard shape as year_month(),
    but validated: this value is published as LAST_COVERED_DATE."""
    if not isinstance(date_str, str) or len(date_str) < 10:
        return None
    day = date_str[:10]
    return day if _ISO_DAY.match(day) else None


def date_range(dates: list[str]) -> str:
    yms = sorted(d for d in (year_month(x) for x in dates) if d)
    if not yms:
        return NO_DATES
    return yms[0] if yms[0] == yms[-1] else f"{yms[0]} — {yms[-1]}"


def corpus_last_date(messages: list[dict]) -> str | None:
    """Newest message date (YYYY-MM-DD) across the loaded slices, or None if no
    message carries a parseable date. ISO days sort lexicographically, so max()
    over strings is both correct and deterministic."""
    days = [d for d in (iso_day(m.get("date")) for m in messages) if d]
    return max(days) if days else None


def resolve_last_covered(curation: dict, messages: list[dict]) -> tuple[str, str | None]:
    """Coverage date is DERIVED from the corpus, never copied from curation.

    `curation.last_covered_date` is treated as an optional FLOOR: if it claims
    coverage the data does not have, that is a curation bug and we say so — but
    we publish what the corpus actually supports and still exit 0 (a warning,
    not a gate). Returns (last_covered_date, warning_or_None).
    """
    declared = curation.get("last_covered_date")
    declared = declared.strip() if isinstance(declared, str) and declared.strip() else None
    corpus = corpus_last_date(messages)

    if corpus is None:
        # Deterministic fallback: the declared floor if there is one, else the
        # same "no dates" marker date_range() uses. Never "" and never a crash.
        return (declared or NO_DATES, None)

    warning = None
    if declared and declared > corpus:
        warning = (
            f"ВНИМАНИЕ: curation.last_covered_date={declared} новее максимальной "
            f"даты корпуса ({corpus}) — курация заявляет покрытие, которого в "
            f"данных нет. Публикуется {corpus}."
        )
    return (corpus, warning)


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


def render_markdown(curation: dict, published: list[dict], last_covered_date: str) -> str:
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
        f"- **LAST_COVERED_DATE:** {last_covered_date}",
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
        last_covered, coverage_warning = resolve_last_covered(curation, messages)

        out_dir = resolve_output(args.out_dir, args.allowed_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "digest.md").write_text(
            render_markdown(curation, published, last_covered), encoding="utf-8")
        (out_dir / "digest.json").write_text(
            json.dumps({"source": curation.get("source"),
                        "last_covered_date": last_covered,
                        "min_authors": args.min_authors,
                        "claims": published}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        (out_dir / "LAST_COVERED_DATE").write_text(last_covered + "\n", encoding="utf-8")
    except SafeIOError as e:
        die(e)

    if coverage_warning:
        print(coverage_warning)
    print(f"messages={len(messages)} last_covered={last_covered} "
          f"published={len(published)} suppressed(k-anon)={len(suppressed)}")
    for r in suppressed:
        print(f"  suppressed [{r.get('distinct_authors')} автор(ов)]: {r['statement'][:60]}...")
    print(f"-> {out_dir}/digest.md, digest.json, LAST_COVERED_DATE")


if __name__ == "__main__":
    main()
