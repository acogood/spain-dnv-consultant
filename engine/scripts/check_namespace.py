#!/usr/bin/env python3
"""
check_namespace.py — coherence guard for the profile <-> form-registry namespace.

Invariant: every profile key referenced by the form registry MUST exist in the
case-profile schema. Two kinds of reference are checked:

  * `profile_key` on a field — otherwise a form field maps to a key the intake
    never collects -> a guaranteed gap or a hallucinated value at draft time;
  * `applies_when` on a form (stage gate) — a gate on an undeclared key is worse
    than no gate: it reads as empty forever, so the form silently never applies
    and its missing required fields are never reported.

The registry (knowledge_base/forms/registry.json) is the canonical source of
field->key mappings; the profile schema declares the available keys. This script
validates registry_keys ⊆ schema_keys and exits non-zero on any drift.

Usage:
  python check_namespace.py [registry.json] [profile.schema.json]
  # defaults: knowledge_base/forms/registry.json
  #           .claude/skills/dnv-intake/profile.schema.json
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


def registry_profile_keys(registry: dict) -> set[str]:
    keys = set()
    for form in registry.get("forms", {}).values():
        for field in form.get("fields", []):
            k = field.get("profile_key")
            if k:
                keys.add(k)
    return keys


def registry_gate_keys(registry: dict) -> set[str]:
    """Profile keys referenced by any form's `applies_when` (string or list)."""
    keys = set()
    for form in registry.get("forms", {}).values():
        raw = form.get("applies_when")
        if raw is None:
            continue
        for k in ([raw] if isinstance(raw, str) else raw):
            if isinstance(k, str):
                keys.add(k)
    return keys


def schema_keys(schema: dict) -> set[str]:
    """Collect declared keys from the profile schema. Accepts either a flat
    {"keys": ["a.b", ...]} list or a {"properties": {...}} dotted map."""
    if isinstance(schema.get("keys"), list):
        return set(schema["keys"])
    if isinstance(schema.get("properties"), dict):
        return set(schema["properties"].keys())
    raise SystemExit("error: profile schema must declare 'keys' (list) or 'properties' (object)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check registry<->profile namespace coherence.")
    ap.add_argument("registry", nargs="?", default="knowledge_base/forms/registry.json")
    ap.add_argument("schema", nargs="?", default=".claude/skills/dnv-intake/profile.schema.json")
    ap.add_argument("--list", action="store_true", help="just list registry profile keys and exit")
    args = ap.parse_args(argv)

    reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    reg_keys = registry_profile_keys(reg)
    gate_keys = registry_gate_keys(reg)

    if args.list:
        for k in sorted(reg_keys):
            print(k)
        for k in sorted(gate_keys):
            print(f"{k}  (applies_when)")
        return

    sp = Path(args.schema)
    if not sp.is_file():
        print(f"error: profile schema not found: {sp}", file=sys.stderr)
        sys.exit(2)
    sch = json.loads(sp.read_text(encoding="utf-8"))
    sk = schema_keys(sch)

    missing = sorted(reg_keys - sk)
    missing_gates = sorted(gate_keys - sk)
    if missing or missing_gates:
        print("NAMESPACE DRIFT — registry keys not declared in profile schema:", file=sys.stderr)
        for k in missing:
            print(f"  - {k}", file=sys.stderr)
        for k in missing_gates:
            print(f"  - {k}  (applies_when — the gate would never fire)", file=sys.stderr)
        sys.exit(1)

    print(f"OK: all {len(reg_keys)} registry profile keys and {len(gate_keys)} "
          f"applies_when gate key(s) exist in the profile schema ({len(sk)} declared).")


if __name__ == "__main__":
    main()
