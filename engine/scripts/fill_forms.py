#!/usr/bin/env python3
"""
fill_forms.py — deterministic form-filler: case profile -> per-form filling
sheets, driven by the field registry.

This is the MECHANICAL core of the dnv-documents skill. Rule: the
value of every form field IS the corresponding profile value (by profile_key).
A field whose profile value is missing becomes `[ТРЕБУЕТСЯ: <field>]` — never a
guessed value. No hallucination is structurally possible here.

Presentation is NOT invention: the registry declares a `type` per field, and
`_fieldfmt.render_value()` turns the profile value into the exact cell string —
an ISO birth date becomes `DD/MM/AAAA` (the format the Spanish form wants), a
`checkbox` field becomes a tick plus the value. The DATUM is still the profile's;
only its spelling on the sheet is the registry's call. `field_qa.py` re-derives
through the SAME function, so the two sides cannot drift apart.

Precondition: a case profile must exist. Without it the script halts
with an instruction (it does not invent one).

Applicability gating: a form may carry `applies_when` (a profile key, or a list
AND-ed) saying it does not apply to this case in its current state. Two kinds,
and the key deliberately does not distinguish them:
  * STAGE  — EX-17 / tasa-790-012 need `case.resolution_notified`; they WILL
             apply later.
  * SHAPE  — MI-F / EX-17-familiar need `family.present`; for a solo applicant
             they will NEVER apply.
Such forms are still generated (so the sheet exists the moment it becomes
relevant), but they are LABELLED — in the summary line and in the `.md` header —
so "almost entirely [ТРЕБУЕТСЯ]" reads as "does not apply to you", not as a hole
in the package. Structural, so the skills no longer have to say it in prose.
`field_qa.py` reads the same key and suspends the requiredness gate.

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

# Сосед по каталогу: `sys.path[0]` уже равен engine/scripts при прямом запуске,
# но вставляем путь явно — симметрично вставке выше, чтобы импорт не зависел от
# того, как интерпретатор был вызван (`-m`, из другого cwd, из теста).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fieldfmt import render_value  # noqa: E402

REQUIRED = "[ТРЕБУЕТСЯ: {}]"

# What an unmet gate key MEANS for the reader. Both kinds suspend the same
# requiredness gate, but they are not the same news: a STAGE key will be filled
# in later, a SHAPE key never will for this applicant, and telling a solo
# applicant to "wait for the stage" would have them waiting forever. Unknown keys
# fall back to the neutral wording rather than guessing.
GATE_MEANING = {
    "case.resolution_notified":
        "Этап ещё не наступил: лист станет актуальным после одобрения "
        "(на этапе TIE запишется дата уведомления) — тогда перегенерируйте его.",
    "family.present":
        "Эта форма относится к члену семьи, а в профиле его нет. Если вы "
        "подаётесь **соло** — форма вам не нужна вообще: не заполняйте и не "
        "подавайте её, ждать тут нечего.",
}


def gate_explanations(missing_keys):
    """Reader-facing sentences for the unmet keys, in the order given."""
    out = [GATE_MEANING[k] for k in missing_keys if k in GATE_MEANING]
    if not out:
        out = ["Лист станет актуальным, когда это условие в профиле выполнится."]
    return out


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


def applies_when_keys(form):
    """Normalize a form's `applies_when` into a list of profile keys (AND-ed)."""
    raw = form.get("applies_when")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return [k for k in raw if isinstance(k, str)]


def gate_satisfied(v):
    """Does a profile value SWITCH ON the form that gates on it?

    Not the same question as is_empty(): a boolean gate key is answered by its
    value, not by its presence. `family.present: false` is a filled-in answer
    meaning "no family member" — it must leave the family form OFF, whereas
    is_empty(False) is False and would switch it ON. Mirrors field_qa.py.
    """
    if isinstance(v, bool):
        return v
    return not is_empty(v)


def form_applies(form, flat):
    """(applies, missing_keys) for one form against the flattened profile."""
    missing = [k for k in applies_when_keys(form) if not gate_satisfied(flat.get(k))]
    return (not missing), missing


def fill_form(form, flat):
    rows = []
    for field in form.get("fields", []):
        pk = field.get("profile_key")
        val = flat.get(pk)
        if is_empty(val):
            value = REQUIRED.format(field.get("name", pk))
            present = False
        else:
            value = render_value(val, field)
            present = True
        rows.append({
            "name": field.get("name"),
            "profile_key": pk,
            # `type` едет в drafts.json не для кода, а для ЧИТАТЕЛЯ: без него
            # непонятно, почему ячейка `15/01/1990`, а в профиле `1990-01-15` —
            # выглядит как расхождение, хотя это объявленный формат поля.
            "type": field.get("type", "text"),
            "domain": field.get("domain", "free"),
            "criticality": field.get("criticality", ""),
            "value": value,
            "present": present,
        })
    return rows


def render_md(form_id, title, rows, applies=True, missing_keys=()):
    lines = [f"# {form_id} — {title}", ""]
    if not applies:
        lines += ["> ⏸️ **Эта форма НЕ применяется к вашему кейсу в его текущем "
                  "состоянии.** Условие применимости из реестра (`applies_when`) "
                  "не выполнено: пусто " + ", ".join(f"`{k}`" for k in missing_keys)
                  + ". Поэтому лист ниже почти целиком в `[ТРЕБУЕТСЯ: …]` — это "
                  "**ожидаемо, а не пробел пакета**, и field-QA не считает это "
                  "пропусками. " + " ".join(gate_explanations(missing_keys)), ""]
    lines += ["> Сгенерировано из профиля по реестру. `[ТРЕБУЕТСЯ: …]` — нет данных "
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
                f"Профиль не найден: {pp}. Сначала соберите профиль кейса — "
                f"оно создаёт user/case-profile.json. (без профиля не генерирую.)"
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
            applies, missing_keys = form_applies(form, flat)
            safe_id = form_id.replace("/", "_")
            (out_dir / f"{safe_id}.md").write_text(
                render_md(form_id, form.get("title", ""), rows, applies, missing_keys),
                encoding="utf-8")
            missing = sum(1 for r in rows if not r["present"])
            summary.append((form_id, len(rows), missing, applies, missing_keys))

        (out_dir / "drafts.json").write_text(
            json.dumps(drafts, ensure_ascii=False, indent=1), encoding="utf-8")
    except SafeIOError as e:
        die(e)
    except json.JSONDecodeError as e:
        die(SafeIOError(f"Bad JSON: {e}"))

    for fid, n, miss, applies, missing_keys in summary:
        note = "" if applies else (
            "  ⏸️ не применяется (нет: " + ", ".join(missing_keys) + ")")
        print(f"  {fid}: {n} полей, {miss} [ТРЕБУЕТСЯ]{note}")
    if any(not applies for *_, applies, _ in summary):
        print("Формы, помеченные ⏸️, к этому кейсу в его текущем состоянии не "
              "относятся — их [ТРЕБУЕТСЯ] это не пробел пакета.")
    print(f"-> {out_dir} (drafts.json + per-form .md)")


if __name__ == "__main__":
    main()
