#!/usr/bin/env python3
"""
fill_forms.py — deterministic form-filler: case profile -> per-form filling
sheets, driven by the field registry.

This is the MECHANICAL core of the dnv-documents skill. Rule (KTD5/KTD6): the
value of every form field IS the corresponding profile value (by profile_key).
A field whose profile value is missing becomes `[ТРЕБУЕТСЯ: <field>]` — never a
guessed value. No hallucination is structurally possible here.

Precondition (KTD12): a case profile must exist. Without it the script halts
with an instruction (it does not invent one).

Usage:
  python fill_forms.py [profile.json] [registry.json] [--out-dir DIR] [--allowed-root DIR]
  # defaults: user/case-profile.json  knowledge_base/forms/registry.json
  #           --out-dir user/drafts   --allowed-root user
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

sys.path.insert(0, str(Path(__file__).resolve().parent / "chat"))
from _common import SafeIOError, die, resolve_output  # noqa: E402

REQUIRED = "[ТРЕБУЕТСЯ: {}]"


def flatten(obj, prefix=""):
    """Nested profile -> dotted keys ({'applicant': {'sexo': 'Hombre'}} -> {'applicant.sexo': 'Hombre'})."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(flatten(v, key))
            else:
                out[key] = v
    return out


def is_empty(v):
    return v is None or v == "" or v == [] or v == {}


def fill_form(form, flat):
    rows = []
    for field in form.get("fields", []):
        pk = field.get("profile_key")
        val = flat.get(pk)
        if is_empty(val):
            value = REQUIRED.format(field.get("name", pk))
            present = False
        else:
            value = str(val)
            present = True
        rows.append({
            "name": field.get("name"),
            "profile_key": pk,
            "domain": field.get("domain", "free"),
            "criticality": field.get("criticality", ""),
            "value": value,
            "present": present,
        })
    return rows


def render_md(form_id, title, rows):
    lines = [f"# {form_id} — {title}", "",
             "> Сгенерировано из профиля по реестру. `[ТРЕБУЕТСЯ: …]` — нет данных "
             "в профиле (заполнить, не выдумывать). Сверьте ярлыки с текущим бланком.",
             "", "| Поле | Значение | Домен | Крит. |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['name']} | {r['value']} | {r['domain']} | {r['criticality']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fill DNV forms from the case profile.")
    ap.add_argument("profile", nargs="?", default="user/case-profile.json")
    ap.add_argument("registry", nargs="?", default="knowledge_base/forms/registry.json")
    ap.add_argument("--out-dir", default="user/drafts")
    ap.add_argument("--allowed-root", default="user")
    args = ap.parse_args(argv)

    try:
        pp = Path(args.profile)
        if not pp.is_file():
            raise SafeIOError(
                f"Профиль не найден: {pp}. Сначала пройдите интервью (/dnv-intake) — "
                f"оно создаёт user/case-profile.json. (KTD12: без профиля не генерирую.)"
            )
        profile = json.loads(pp.read_text(encoding="utf-8"))
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        out_dir = resolve_output(args.out_dir, args.allowed_root)
        out_dir.mkdir(parents=True, exist_ok=True)

        flat = flatten(profile)
        drafts = {}
        summary = []
        for form_id, form in registry.get("forms", {}).items():
            rows = fill_form(form, flat)
            drafts[form_id] = rows
            safe_id = form_id.replace("/", "_")
            (out_dir / f"{safe_id}.md").write_text(
                render_md(form_id, form.get("title", ""), rows), encoding="utf-8")
            missing = sum(1 for r in rows if not r["present"])
            summary.append((form_id, len(rows), missing))

        (out_dir / "drafts.json").write_text(
            json.dumps(drafts, ensure_ascii=False, indent=1), encoding="utf-8")
    except SafeIOError as e:
        die(e)
    except json.JSONDecodeError as e:
        die(SafeIOError(f"Bad JSON: {e}"))

    for fid, n, miss in summary:
        print(f"  {fid}: {n} полей, {miss} [ТРЕБУЕТСЯ]")
    print(f"-> {out_dir} (drafts.json + per-form .md)")


if __name__ == "__main__":
    main()
