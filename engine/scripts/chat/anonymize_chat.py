"""
anonymize_chat.py — privacy-preserving extractor for Telegram chat exports.

Runs LOCALLY on a forker's own export(s). It is the privacy gate of the
chat-mining pipeline: merge -> ANONYMIZE -> filter -> slice. Its output stays
under user/ and is NEVER shipped; only the aggregated digest (build_digest.py)
is publishable.

Design:
  * KEEP-ALLOWLIST of fields, not a denylist. Identity leaks through many
    fields (from, from_id, forwarded_from, actor, actor_id, members,
    saved_from, reply_to_peer_id, ...) and unknown future fields would slip a
    denylist. We copy ONLY {id, date, text, reply_to, topics} and add a derived
    pseudonym. Everything else is dropped by construction.
  * Pseudonym = salted hash of from_id (NOT the display name — names collide:
    ~295 names vs ~316 ids in a real corpus). Computed BEFORE from_id is
    dropped. The salt is local & secret; pseudonyms must not be published.
  * Text is flattened with entity-aware redaction (@mentions, emails, phones,
    telegram deep-links) and roster-name stripping (the export's own author
    names are removed from message bodies).
  * type == "service" messages (joins, title changes) carry names in
    actor/members and no practice value — dropped entirely.

Limitation (documented, not hidden): names of NON-participants mentioned in
free text are an open class and cannot be fully stripped. The PUBLISHED surface
is the aggregated digest (counts/ranges), not raw text, which contains this.

Usage:
  python anonymize_chat.py <input.json> <output.json> [options]

Options:
  --salt-file PATH     persisted local salt (default: <output_dir>/.anon_salt)
  --roster-out PATH    write harvested author roster (debug, local only)
  --allowed-root DIR   confine output under this dir (default: cwd)
  --max-bytes N        input size limit (default 512 MiB)
  --max-depth N        JSON nesting limit (default 200)
  --min-token-len N    min length of a name token to strip from text (default 4)
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

# Make Cyrillic console output work on Windows (target audience runs Windows).
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

from _common import (  # noqa: E402  (local sibling module)
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_DEPTH,
    SafeIOError,
    die,
    load_json_safe,
    load_or_create_salt,
    messages_of,
    resolve_output,
    stable_pseudonym,
)

# Output keep-allowlist (the ONLY message fields that survive, + derived author).
KEEP_FIELDS = ("id", "date", "reply_to", "topics")

# Telegram entity types whose text must be redacted regardless of roster.
ENTITY_REDACTIONS = {
    "mention": "[@user]",
    "mention_name": "[имя]",
    "email": "[email]",
    "phone": "[phone]",
    "bank_card": "[card]",
}

_TG_DEEPLINK = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog)/\S+", re.I)
# Backstops for contact PII that appears as PLAIN text (not tagged as an
# entity, so entity-redaction alone misses it — observed in real exports).
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone: requires a leading '+' so we don't nuke money, years, or article
# numbers (e.g. "Ley 14/2013", "€2400") — conservative on purpose.
_PHONE = re.compile(r"\+\d[\d\s()‐-―-]{7,}\d")
_NAME_INTRO = re.compile(
    r"(меня\s+зовут|зовут\s+меня|я\s*[—-]\s*|это\s+я,?\s*)\s*([A-ZА-ЯЁ][\wÀ-ÿ’'-]+)",
    re.I,
)


def flatten_and_redact_text(text_field) -> str:
    """Flatten Telegram's text (str | list of str/dict) and redact identity
    entities (mentions, emails, phones, deep-links) by entity type."""
    parts = []
    if isinstance(text_field, str):
        parts.append(text_field)
    elif isinstance(text_field, list):
        for item in text_field:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                etype = item.get("type")
                if etype in ENTITY_REDACTIONS:
                    parts.append(ENTITY_REDACTIONS[etype])
                else:
                    # text_link / link / plain / bold / etc.: keep visible text,
                    # drop any href (href lives in a separate key, not concatenated).
                    parts.append(item.get("text", ""))
    text = "".join(parts)
    # Plain-text backstops (catch contact PII not tagged as entities).
    text = _TG_DEEPLINK.sub("[ссылка]", text)
    text = _EMAIL.sub("[email]", text)
    text = _PHONE.sub("[phone]", text)
    return text


def harvest_roster(messages) -> set[str]:
    """Collect author display names from every identity-bearing field BEFORE
    they are dropped, so we can strip them out of message bodies."""
    roster: set[str] = set()

    def add(v):
        if isinstance(v, str) and v.strip():
            roster.add(v.strip())

    for m in messages:
        if not isinstance(m, dict):
            continue
        add(m.get("from"))
        add(m.get("forwarded_from"))
        add(m.get("actor"))
        add(m.get("saved_from"))
        members = m.get("members")
        if isinstance(members, list):
            for x in members:
                add(x)
    return roster


def build_name_pattern(roster: set[str], min_token_len: int) -> re.Pattern | None:
    """Compile one alternation matching full roster names and their longer
    individual tokens, as whole words, case-insensitively."""
    needles: set[str] = set()
    for name in roster:
        full = name.strip()
        if len(full) >= 2:
            needles.add(full)
        for tok in re.split(r"\s+", full):
            tok = tok.strip("’'\"().,–—-")
            if len(tok) >= min_token_len:
                needles.add(tok)
    if not needles:
        return None
    # Longest first so multi-token names win over their parts.
    alts = sorted((re.escape(n) for n in needles), key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


def strip_names(text: str, name_re: re.Pattern | None) -> str:
    """Replace roster names and 'меня зовут X' intros with [имя]."""
    if name_re is not None:
        text = name_re.sub("[имя]", text)
    text = _NAME_INTRO.sub(lambda m: f"{m.group(1)} [имя]", text)
    return text


def anonymize(messages, salt: bytes, min_token_len: int):
    roster = harvest_roster(messages)
    name_re = build_name_pattern(roster, min_token_len)

    out = []
    dropped_service = 0
    empty = 0
    for m in messages:
        if not isinstance(m, dict):
            continue
        if m.get("type") == "service":
            dropped_service += 1
            continue

        # Pseudonym from from_id (preferred) BEFORE dropping it; fall back to
        # the display name only if no id exists for this message.
        ident = m.get("from_id")
        if ident is None:
            ident = m.get("from")
        author = stable_pseudonym(str(ident), salt) if ident not in (None, "") else "u_anon"

        text = flatten_and_redact_text(m.get("text", ""))
        text = strip_names(text, name_re)
        if not text.strip():
            empty += 1
            continue

        entry = {
            "id": m.get("id"),
            "date": m.get("date"),
            "text": text,
            "reply_to": m.get("reply_to_message_id", m.get("reply_to")),
            "author": author,
        }
        if isinstance(m.get("topics"), list):
            entry["topics"] = m["topics"]
        # Enforce keep-allowlist explicitly: build only known keys above.
        out.append(entry)

    return out, roster, dropped_service, empty


def main(argv=None):
    ap = argparse.ArgumentParser(description="Anonymize a Telegram chat export (local).")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--salt-file", default=None)
    ap.add_argument("--roster-out", default=None)
    ap.add_argument("--allowed-root", default=".")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    ap.add_argument("--min-token-len", type=int, default=4)
    args = ap.parse_args(argv)

    try:
        out_path = resolve_output(args.output, args.allowed_root)
        salt_file = args.salt_file or (out_path.parent / ".anon_salt")
        salt = load_or_create_salt(salt_file)

        data = load_json_safe(args.input, max_bytes=args.max_bytes, max_depth=args.max_depth)
        messages = messages_of(data)

        anon, roster, dropped_service, empty = anonymize(messages, salt, args.min_token_len)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        out_path.write_text(json.dumps(anon, ensure_ascii=False, indent=1), encoding="utf-8")

        if args.roster_out:
            roster_path = resolve_output(args.roster_out, args.allowed_root)
            roster_path.write_text("\n".join(sorted(roster)), encoding="utf-8")
    except SafeIOError as e:
        die(e)

    distinct = len({m["author"] for m in anon})
    print(f"in={len(messages)} kept={len(anon)} dropped_service={dropped_service} "
          f"empty_after_redaction={empty} distinct_authors={distinct} roster_names={len(roster)}")
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
