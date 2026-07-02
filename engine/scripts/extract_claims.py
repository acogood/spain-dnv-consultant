#!/usr/bin/env python3
"""
extract_claims.py — extract tagged claims from the case spec into structured JSON
for the devils-advocate verification agent.

Parameterized (no hardcoded paths / interpreter). Reads a markdown spec, writes
a claims JSON whose path is confined to the allowed root.

Usage:
  python extract_claims.py [spec.md] [claims.json] [--allowed-root DIR]
  # defaults: user/spec.md -> user/claims.json

Extraction:
  1. Table rows / inline bullets carrying a confidence tag ([норма], [практика — …], …)
  2. Untagged critical assertions in risk sections (4.x) -> marked [implicit]
Each claim: id, section, line, text, confidence_tag, legal_refs, time_sensitive.
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

# Reuse the canonical path-containment guard from the chat helpers.
sys.path.insert(0, str(Path(__file__).resolve().parent / "chat"))
from _common import SafeIOError, die, resolve_output  # noqa: E402

MAX_SPEC_BYTES = 16 * 1024 * 1024  # a spec is text; 16 MiB is far more than enough

TAG_PATTERN = re.compile(
    r'\['
    r'(норма|'
    r'официальное разъяснение|'
    r'официально не подтверждено[^]]*|'
    r'практика\s*—\s*консультант[^]]*|'
    r'практика\s*—\s*Telegram[^]]*|'
    r'практика\s*—\s*[^]]+|'
    r'первый опыт\s*—\s*Telegram[^]]*|'
    r'вторичный источник[^]]*|'
    r'не подтверждено[^]]*|'
    r'не полностью подтверждено[^]]*|'
    r'новое требование[^]]*|'
    r'консенсус [^]]*)'
    r'\]',
    re.IGNORECASE,
)

LEGAL_REF_PATTERN = re.compile(
    r'(?:'
    r'(?:Ley\s+\d+/\d+[^,|]*)|'
    r'(?:art(?:\.\s*|\s+)\d+[^,|]*)|'
    r'(?:D\.A\.\s*\d+[^,|]*)|'
    r'(?:Real Decreto\s+\d+/\d+[^,|]*)|'
    r'(?:Resolución\s+[A-Z]+[^,|]*)|'
    r'(?:Criterio\s+[A-Z]+[^,|]*)|'
    r'(?:Canje de Notas[^,|]*)|'
    r'(?:LO\s+\d+/\d+[^,|]*)'
    r')',
    re.IGNORECASE,
)

TIME_KEYWORDS = re.compile(
    r'(?:SMI|IPREM|€[\d.,]+|20(?:2[5-9]|3\d)|'
    r'\d+\s*(?:раб\.|рабочих|календ\.|дн[ея]й|мес\.|месяц)|'
    r'(?:до|после|начало|истечени)|'
    r'(?:срок|окно|дедлайн|период)|'
    r'Real Decreto)',
    re.IGNORECASE,
)

SECTION_PATTERN = re.compile(r'^(#{1,4})\s+(.+)')


def extract_table_row_text(line):
    cells = [c.strip() for c in line.split('|')[1:-1]]
    if all(re.match(r'^[-:]+$', c) for c in cells):
        return None, []
    if len(cells) < 2:
        return None, []
    return ' | '.join(c for c in cells if c and not re.match(r'^\d+$', c)), cells


def extract_legal_refs(text):
    refs = LEGAL_REF_PATTERN.findall(text)
    return [r.strip().rstrip('.,:;').replace('**', '') for r in refs]


def normalize_tag(tag_text):
    return re.sub(r'\s+', ' ', tag_text.strip('[]').strip())


def is_time_sensitive(text):
    return bool(TIME_KEYWORDS.search(text))


def parse_spec(lines):
    claims = []
    current_section = ""
    counter = 0
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = SECTION_PATTERN.match(s)
        if m:
            if len(m.group(1)) <= 3:
                current_section = m.group(2).strip()
            continue
        if not s or s.startswith('---') or s.startswith('>'):
            continue
        tags = TAG_PATTERN.findall(s)
        if not tags:
            continue
        if s.startswith('|'):
            text, _ = extract_table_row_text(s)
            if text is None:
                continue
        else:
            text = TAG_PATTERN.sub('', s).strip()
            text = re.sub(r'^[-*]\s+', '', text).strip()
        text = text.replace('**', '')
        if len(text) < 15:
            continue
        counter += 1
        all_tags = [normalize_tag(f'[{t}]') for t in tags]
        claims.append({
            "id": f"C{counter:03d}",
            "section": current_section,
            "line": i,
            "text": text,
            "confidence_tag": all_tags[0] if all_tags else 'не подтверждено',
            "all_tags": all_tags if len(all_tags) > 1 else None,
            "legal_refs": extract_legal_refs(s) or None,
            "time_sensitive": is_time_sensitive(text),
        })
    return claims


def add_implicit_claims(lines, existing):
    existing_lines = {c["line"] for c in existing}
    implicit = []
    in_risk = False
    counter = len(existing)
    patterns = [
        re.compile(r'(?:НЕ|не)\s+(?:нужн|требуется|обязательн|принимается)', re.I),
        re.compile(r'(?:обязательн|критическ|необходим|должн)', re.I),
        re.compile(r'(?:одобрен|отказ|принят|отклонён)', re.I),
        re.compile(r'(?:безопасн|риск\w*\s*зон)', re.I),
        re.compile(r'(?:нет\s+задокументированных|не\s+найдено|ни\s+одного)', re.I),
    ]
    current_section = ""
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = SECTION_PATTERN.match(s)
        if m:
            if len(m.group(1)) <= 3:
                current_section = m.group(2).strip()
            title = m.group(2)
            in_risk = '4.' in title or '⚠️' in title or 'риск' in title.lower()
            continue
        if not in_risk or i in existing_lines:
            continue
        if TAG_PATTERN.search(s) or s.startswith('|') or s.startswith('#') or len(s) < 30:
            continue
        for p in patterns:
            if p.search(s):
                counter += 1
                text = re.sub(r'^[-*]\s+', '', s).strip()
                text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
                implicit.append({
                    "id": f"C{counter:03d}", "section": current_section, "line": i,
                    "text": text, "confidence_tag": "implicit — без тега в источнике",
                    "all_tags": None, "legal_refs": extract_legal_refs(s) or None,
                    "time_sensitive": is_time_sensitive(s),
                })
                break
    return implicit


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract tagged claims from a case spec.")
    ap.add_argument("spec", nargs="?", default="user/spec.md")
    ap.add_argument("out", nargs="?", default="user/claims.json")
    ap.add_argument("--allowed-root", default=".")
    args = ap.parse_args(argv)

    try:
        spec_path = Path(args.spec)
        if not spec_path.is_file():
            raise SafeIOError(f"Spec not found: {spec_path}")
        if spec_path.stat().st_size > MAX_SPEC_BYTES:
            raise SafeIOError(f"Spec too large (> {MAX_SPEC_BYTES} bytes).")
        out_path = resolve_output(args.out, args.allowed_root)
        lines = spec_path.read_text(encoding="utf-8").splitlines()
        claims = parse_spec(lines)
        claims += add_implicit_claims(lines, claims)
        for c in claims:
            for k in [k for k, v in c.items() if v is None]:
                del c[k]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(claims, ensure_ascii=False, indent=2), encoding="utf-8")
    except SafeIOError as e:
        die(e)

    print(f"claims={len(claims)} -> {out_path}")


if __name__ == "__main__":
    main()
