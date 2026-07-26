#!/usr/bin/env python3
"""
field_qa.py — exhaustive, deterministic field-QA BASELINE (the must-have layer
of dnv-review).

For EVERY field in the registry it emits an explicit verdict
(OK / WRONG / MISSING / UNCERTAIN) — silence is a review bug, so the count of
verdicts always equals the count of registry fields. It checks correctness, not
plausibility:

  * controlled-vocabulary (domain) violations -> WRONG  (catches sexo='indefinido')
  * profile-empty but draft has a value       -> WRONG  (catches hallucination)
  * draft value != re-derived profile value   -> WRONG  (catches a plausible-but-wrong value)
  * profile-empty & draft '[ТРЕБУЕТСЯ]'        -> MISSING (alta) / OK (media/baja)

STAGE GATING (`applies_when`): a form may not apply yet at the case's current
stage — EX-17 / tasa-790-012 only make sense after a resolución. The registry
declares that as `applies_when: <profile key>` (or a list, AND-ed); a form
without the key always applies. When a form does NOT apply, an empty field
correctly marked `[ТРЕБУЕТСЯ]` is OK regardless of criticality.

Why this is a gate and not a criticality tweak: criticality is static, but
whether a field is required depends on case STATE. The registry used to encode
"not yet" by demoting EX-17 fields to `media`, which silenced the false MISSINGs
— and MASKED the real ones (an empty spouse passport with family.present=true
scored OK). Non-applicability now suspends the REQUIREDNESS gate only; the
value checks above (domain, hallucination, mismatch) still run on every field of
every form, applicable or not.

ISOLATION: `rederive_expected()` reads ONLY the profile + registry — it
never looks at the draft. A separate step (`diff`) compares those expected values
with the draft. This is the deterministic baseline; the LLM re-derivation lives
in the field-qa-reviewer agent (two independent processes).

Usage:
  python field_qa.py [profile.json] [registry.json] [drafts.json] [--out-dir DIR] [--allowed-root DIR]
  # defaults: user/case-profile.json knowledge_base/forms/registry.json user/drafts/drafts.json
  #           --out-dir user/drafts  --allowed-root user
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

REQ_PREFIX = "[ТРЕБУЕТСЯ"


def flatten(obj, prefix=""):
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
    """Normalize a form's `applies_when` into a list of profile keys.

    Accepts a single key, a list of keys, or nothing at all. All keys are AND-ed.
    """
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
    is_empty(False) is False and would switch it ON.
    """
    if isinstance(v, bool):
        return v
    return not is_empty(v)


def form_applicability(registry, profile):
    """{form_id: (applies: bool, reason: str)} for every form in the registry.

    Reuses the same flatten() the value re-derivation uses — one profile parser,
    not two, so a form can never be gated on a key spelled differently from the
    key its fields are filled from.
    """
    flat = flatten(profile)
    out = {}
    for form_id, form in registry.get("forms", {}).items():
        missing = [k for k in applies_when_keys(form) if not gate_satisfied(flat.get(k))]
        if missing:
            out[form_id] = (False, "форма не применяется на этом этапе: пусто "
                                   + ", ".join(missing))
        else:
            out[form_id] = (True, "")
    return out


def rederive_expected(profile, registry):
    """Derive each field's expected value from profile + registry ONLY.
    Does NOT read the draft. Returns {(form, field_name): expected_or_None}."""
    flat = flatten(profile)
    expected = {}
    for form_id, form in registry.get("forms", {}).items():
        for field in form.get("fields", []):
            val = flat.get(field.get("profile_key"))
            expected[(form_id, field.get("name"))] = None if is_empty(val) else str(val)
    return expected


def diff(expected, registry, drafts, applicability=None):
    """Compare re-derived expectations with the draft.

    `applicability` is {form_id: (applies, reason)} from form_applicability().
    Omitted (None) means "every form applies" — backward-compatible with a
    registry that declares no `applies_when` anywhere.
    """
    vocab = registry.get("controlled_vocabularies", {})
    applicability = applicability or {}
    crit_of, domain_of = {}, {}
    for form_id, form in registry.get("forms", {}).items():
        for field in form.get("fields", []):
            crit_of[(form_id, field["name"])] = field.get("criticality", "media")
            domain_of[(form_id, field["name"])] = field.get("domain", "free")

    actual = {}
    for form_id, rows in drafts.items():
        for r in rows:
            actual[(form_id, r.get("name"))] = r.get("value")

    verdicts = []
    for key, exp in expected.items():
        form_id, name = key
        act = actual.get(key)
        dom = domain_of.get(key, "free")
        crit = crit_of.get(key, "media")
        allowed = vocab.get(dom)  # None unless an enum domain

        if act is None:
            verdicts.append((form_id, name, "UNCERTAIN", "поле есть в реестре, но отсутствует в черновике"))
            continue

        act_is_req = isinstance(act, str) and act.startswith(REQ_PREFIX)

        # 1) controlled-vocabulary violation (only for filled enum fields)
        if allowed is not None and not act_is_req and act not in allowed:
            verdicts.append((form_id, name, "WRONG", f"вне домена {dom}: '{act}' ∉ {allowed}"))
            continue

        # 2) profile empty
        if exp is None:
            if act_is_req:
                applies, why_not = applicability.get(form_id, (True, ""))
                if not applies:
                    # Stage gate, not a criticality question: the form is not in
                    # play yet, so an honest [ТРЕБУЕТСЯ] is the correct state.
                    verdicts.append((form_id, name, "OK", why_not))
                elif crit == "alta":
                    verdicts.append((form_id, name, "MISSING", "обязательное поле пусто в профиле"))
                else:
                    verdicts.append((form_id, name, "OK", "пусто в профиле и корректно помечено"))
            else:
                verdicts.append((form_id, name, "WRONG", f"профиль пуст, но в черновике значение '{act}' (галлюцинация)"))
            continue

        # 3) profile has a value
        if act_is_req:
            verdicts.append((form_id, name, "WRONG", f"в профиле есть значение '{exp}', но черновик помечен [ТРЕБУЕТСЯ]"))
        elif act == exp:
            verdicts.append((form_id, name, "OK", ""))
        else:
            verdicts.append((form_id, name, "WRONG", f"не совпадает: черновик '{act}' ≠ профиль '{exp}'"))
    return verdicts


def render(verdicts, applicability=None):
    counts = {}
    for *_ , v, _ in [(f, n, ver, why) for f, n, ver, why in verdicts]:
        counts[v] = counts.get(v, 0) + 1
    lines = ["# Field-QA baseline (механический, исчерпывающий)", "",
             "> Один вердикт на КАЖДОЕ поле реестра (count==полей). Проверяется "
             "корректность, не правдоподобие. Это must-have baseline; независимая "
             "ре-деривация и official-review — отдельные слои.", ""]
    inactive = sorted(f for f, (ok, _) in (applicability or {}).items() if not ok)
    if inactive:
        lines += ["> **Не применяются на этом этапе кейса** (`applies_when`): "
                  + ", ".join(f"`{f}`" for f in inactive) + ". Их пустые поля с "
                  "`[ТРЕБУЕТСЯ]` дают OK — это не пробел пакета. Проверка "
                  "значений (домены, галлюцинации, расхождение с профилем) для "
                  "них всё равно выполнена.", ""]
    lines += ["| Форма | Поле | Вердикт | Причина |", "|---|---|---|---|"]
    for f, n, v, why in verdicts:
        mark = {"OK": "✅", "WRONG": "❌", "MISSING": "⚠️", "UNCERTAIN": "❔"}.get(v, "")
        lines.append(f"| {f} | {n} | {mark} {v} | {why} |")
    lines += ["", "## Сводка", "", "| Вердикт | Кол-во |", "|---|---|"]
    for v in ("OK", "WRONG", "MISSING", "UNCERTAIN"):
        lines.append(f"| {v} | {counts.get(v, 0)} |")
    lines.append(f"| **Всего полей** | **{len(verdicts)}** |")
    return "\n".join(lines), counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Exhaustive field-QA baseline.")
    ap.add_argument("profile", nargs="?", default="user/case-profile.json")
    ap.add_argument("registry", nargs="?", default="knowledge_base/forms/registry.json")
    ap.add_argument("drafts", nargs="?", default="user/drafts/drafts.json")
    ap.add_argument("--out-dir", "--out", dest="out_dir", default="user/drafts",
                    help="output directory (alias: --out)")
    ap.add_argument("--allowed-root", default="user")
    args = ap.parse_args(argv)

    try:
        for p in (args.profile, args.registry, args.drafts):
            if not Path(p).is_file():
                raise SafeIOError(f"Не найдено: {p}. Сначала /dnv-intake и /dnv-documents.")
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        drafts = json.loads(Path(args.drafts).read_text(encoding="utf-8"))

        expected = rederive_expected(profile, registry)    # no draft here
        applicability = form_applicability(registry, profile)  # nor here
        verdicts = diff(expected, registry, drafts, applicability)  # compare with draft
        report, counts = render(verdicts, applicability)

        out_dir = resolve_output(args.out_dir, args.allowed_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "field_qa_report.md").write_text(report, encoding="utf-8")
        (out_dir / "field_qa_report.json").write_text(
            json.dumps([{"form": f, "field": n, "verdict": v, "reason": w} for f, n, v, w in verdicts],
                       ensure_ascii=False, indent=1), encoding="utf-8")
    except SafeIOError as e:
        die(e)
    except json.JSONDecodeError as e:
        die(SafeIOError(f"Bad JSON: {e}"))

    print(f"fields={len(verdicts)} OK={counts.get('OK',0)} WRONG={counts.get('WRONG',0)} "
          f"MISSING={counts.get('MISSING',0)} UNCERTAIN={counts.get('UNCERTAIN',0)}")
    inactive = sorted(f for f, (ok, _) in applicability.items() if not ok)
    if inactive:
        print("не применяются на этом этапе (applies_when): " + ", ".join(inactive))
    print(f"-> {out_dir}/field_qa_report.md")
    # Non-zero exit if any hard error verdict, so CI / the gate can branch on it.
    sys.exit(1 if counts.get("WRONG", 0) else 0)


if __name__ == "__main__":
    main()
