"""
Tests for the form-filler (fill_forms) and the field-QA baseline (field_qa).
Stdlib unittest, synthetic fixtures only.

    python -m unittest test_forms_qa -v
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import fill_forms as ff  # noqa: E402
import field_qa as fq  # noqa: E402

REGISTRY = {
    "controlled_vocabularies": {"sexo": ["Hombre", "Mujer"]},
    "forms": {
        "MI-T": {"title": "t", "fields": [
            {"name": "Nombre", "type": "text", "domain": "free", "profile_key": "applicant.first_name", "criticality": "alta"},
            {"name": "Sexo", "type": "enum", "domain": "sexo", "profile_key": "applicant.sexo", "criticality": "alta"},
            {"name": "Segundo apellido", "type": "text", "domain": "free", "profile_key": "applicant.second_last_name", "criticality": "media"},
            {"name": "RegTitular", "type": "text", "domain": "free", "profile_key": "family.titular_regage", "criticality": "alta"},
        ]},
    },
}
PROFILE = {"applicant": {"first_name": "Ivan", "sexo": "Hombre", "second_last_name": None},
           "family": {"titular_regage": None}}


class TestFill(unittest.TestCase):
    def test_present_and_missing(self):
        flat = ff.flatten(PROFILE)
        rows = ff.fill_form(REGISTRY["forms"]["MI-T"], flat)
        by = {r["name"]: r for r in rows}
        self.assertEqual(by["Nombre"]["value"], "Ivan")
        self.assertEqual(by["Sexo"]["value"], "Hombre")
        self.assertTrue(by["Segundo apellido"]["value"].startswith("[ТРЕБУЕТСЯ"))
        self.assertTrue(by["RegTitular"]["value"].startswith("[ТРЕБУЕТСЯ"))


class TestFieldQA(unittest.TestCase):
    def _run(self, drafts):
        expected = fq.rederive_expected(PROFILE, REGISTRY)
        applic = fq.form_applicability(REGISTRY, PROFILE)
        return {(f, n): (v, why)
                for f, n, v, why in fq.diff(expected, REGISTRY, drafts, applic)}

    def _drafts(self, **overrides):
        flat = ff.flatten(PROFILE)
        rows = ff.fill_form(REGISTRY["forms"]["MI-T"], flat)
        for r in rows:
            if r["name"] in overrides:
                r["value"] = overrides[r["name"]]
        return {"MI-T": rows}

    def test_clean_is_ok(self):
        v = self._run(self._drafts())
        self.assertEqual(v[("MI-T", "Nombre")][0], "OK")
        self.assertEqual(v[("MI-T", "Sexo")][0], "OK")
        # optional empty correctly marked -> OK; critical empty -> MISSING
        self.assertEqual(v[("MI-T", "Segundo apellido")][0], "OK")
        self.assertEqual(v[("MI-T", "RegTitular")][0], "MISSING")

    def test_out_of_domain_sexo(self):
        v = self._run(self._drafts(Sexo="indefinido"))
        self.assertEqual(v[("MI-T", "Sexo")][0], "WRONG")
        self.assertIn("домен", v[("MI-T", "Sexo")][1])

    def test_plausible_but_wrong_sexo(self):
        # Mujer is in-domain but wrong for a Hombre profile -> mismatch WRONG
        v = self._run(self._drafts(Sexo="Mujer"))
        self.assertEqual(v[("MI-T", "Sexo")][0], "WRONG")
        self.assertIn("не совпадает", v[("MI-T", "Sexo")][1])

    def test_value_mismatch(self):
        v = self._run(self._drafts(Nombre="Pedro"))
        self.assertEqual(v[("MI-T", "Nombre")][0], "WRONG")

    def test_hallucination_when_profile_empty(self):
        v = self._run(self._drafts(RegTitular="FAKE-123"))
        self.assertEqual(v[("MI-T", "RegTitular")][0], "WRONG")
        self.assertIn("галлюцинация", v[("MI-T", "RegTitular")][1])

    def test_exhaustive_one_verdict_per_field(self):
        v = self._run(self._drafts())
        n_fields = sum(len(f["fields"]) for f in REGISTRY["forms"].values())
        self.assertEqual(len(v), n_fields)

    def test_rederive_ignores_draft(self):
        # rederive_expected takes only (profile, registry) — structural isolation
        exp = fq.rederive_expected(PROFILE, REGISTRY)
        self.assertEqual(exp[("MI-T", "Sexo")], "Hombre")
        self.assertIsNone(exp[("MI-T", "RegTitular")])


# --- stage gating (`applies_when`) -------------------------------------------
# A registry with a form that only applies once the case reaches a later stage.
# Fields are HONESTLY `alta` — the stage, not the criticality, does the gating.
STAGED_REGISTRY = {
    "controlled_vocabularies": {"sexo": ["Hombre", "Mujer"]},
    "forms": {
        "MI-F": {"title": "f", "fields": [
            {"name": "Pasaporte", "type": "text", "domain": "free",
             "profile_key": "family.passport_number", "criticality": "alta"},
        ]},
        "EX-17-familiar": {"title": "x", "applies_when": ["case.resolution_notified",
                                                          "family.present"],
                           "fields": [
            {"name": "Nº pasaporte", "type": "text", "domain": "free",
             "profile_key": "family.passport_number", "criticality": "alta"},
            {"name": "Sexo", "type": "enum", "domain": "sexo",
             "profile_key": "family.sexo", "criticality": "alta"},
        ]},
    },
}


class TestAppliesWhen(unittest.TestCase):
    """The reviewer's counterexample, both directions.

    Before this gate the registry demoted EX-17 fields to `media` so that an
    empty pre-resolución profile would not sting — which also meant a genuinely
    missing spouse passport scored OK. The gate must kill the false MISSINGs
    WITHOUT resurrecting the masking.
    """

    PRE = {"case": {"resolution_notified": None}, "family": {"present": True,
           "passport_number": None, "sexo": None}}
    POST = {"case": {"resolution_notified": "2026-07-01"}, "family": {"present": True,
            "passport_number": None, "sexo": None}}
    SOLO = {"case": {"resolution_notified": "2026-07-01"}, "family": {"present": False,
            "passport_number": None, "sexo": None}}

    def _run(self, profile, drafts, registry=STAGED_REGISTRY):
        expected = fq.rederive_expected(profile, registry)
        applic = fq.form_applicability(registry, profile)
        return {(f, n): (v, why)
                for f, n, v, why in fq.diff(expected, registry, drafts, applic)}

    def _drafts(self, profile, overrides=None, registry=STAGED_REGISTRY):
        """overrides: {(form_id, field_name): value}"""
        overrides = overrides or {}
        flat = ff.flatten(profile)
        out = {}
        for fid, form in registry["forms"].items():
            rows = ff.fill_form(form, flat)
            for r in rows:
                if (fid, r["name"]) in overrides:
                    r["value"] = overrides[(fid, r["name"])]
            out[fid] = rows
        return out

    def test_form_not_applicable_empty_is_ok(self):
        v = self._run(self.PRE, self._drafts(self.PRE))
        self.assertEqual(v[("EX-17-familiar", "Nº pasaporte")][0], "OK")
        self.assertIn("не применяется", v[("EX-17-familiar", "Nº pasaporte")][1])

    def test_form_applicable_alta_empty_is_missing(self):
        # THE counterexample: family.present=true + resolución + empty passport
        v = self._run(self.POST, self._drafts(self.POST))
        self.assertEqual(v[("EX-17-familiar", "Nº pasaporte")][0], "MISSING")
        self.assertEqual(v[("EX-17-familiar", "Sexo")][0], "MISSING")

    def test_and_semantics_all_keys_required(self):
        # resolución arrived, but no family member -> still not applicable.
        # Note family.present is the BOOLEAN False, not an absent key: a filled-in
        # "no" must switch the form OFF, which is_empty() alone would not do.
        v = self._run(self.SOLO, self._drafts(self.SOLO))
        self.assertEqual(v[("EX-17-familiar", "Nº pasaporte")][0], "OK")

    def test_boolean_gate_false_is_not_satisfied(self):
        self.assertFalse(fq.gate_satisfied(False))
        self.assertTrue(fq.gate_satisfied(True))
        self.assertFalse(fq.gate_satisfied(None))
        self.assertFalse(fq.gate_satisfied(""))
        self.assertTrue(fq.gate_satisfied("2026-07-01"))
        # both scripts must agree, or the sheet and its QA would disagree
        for v in (False, True, None, "", "2026-07-01"):
            self.assertEqual(fq.gate_satisfied(v), ff.gate_satisfied(v))

    def test_no_noise_before_resolution(self):
        v = self._run(self.PRE, self._drafts(self.PRE))
        staged = [x for (f, _), x in v.items() if f == "EX-17-familiar"]
        self.assertTrue(all(x[0] == "OK" for x in staged), staged)
        # ...while a form with no applies_when still gates normally
        self.assertEqual(v[("MI-F", "Pasaporte")][0], "MISSING")

    def test_value_checks_still_run_on_inapplicable_form(self):
        # Non-applicability suspends REQUIREDNESS only, never correctness.
        d = self._drafts(self.PRE, {("EX-17-familiar", "Nº pasaporte"): "FAKE-1"})
        v = self._run(self.PRE, d)
        self.assertEqual(v[("EX-17-familiar", "Nº pasaporte")][0], "WRONG")
        self.assertIn("галлюцинация", v[("EX-17-familiar", "Nº pasaporte")][1])

    def test_out_of_domain_still_wrong_on_inapplicable_form(self):
        d = self._drafts(self.PRE, {("EX-17-familiar", "Sexo"): "indefinido"})
        v = self._run(self.PRE, d)
        self.assertEqual(v[("EX-17-familiar", "Sexo")][0], "WRONG")
        self.assertIn("домен", v[("EX-17-familiar", "Sexo")][1])

    def test_absent_applies_when_means_always_applicable(self):
        # backward compatibility: the old registry shape must behave as before
        applic = fq.form_applicability(REGISTRY, PROFILE)
        self.assertEqual(applic["MI-T"], (True, ""))
        expected = fq.rederive_expected(PROFILE, REGISTRY)
        flat = ff.flatten(PROFILE)
        drafts = {"MI-T": ff.fill_form(REGISTRY["forms"]["MI-T"], flat)}
        with_gate = fq.diff(expected, REGISTRY, drafts, applic)
        without_gate = fq.diff(expected, REGISTRY, drafts)   # applicability=None
        self.assertEqual(with_gate, without_gate)

    def test_fill_forms_flags_inapplicable_form(self):
        flat = ff.flatten(self.PRE)
        form = STAGED_REGISTRY["forms"]["EX-17-familiar"]
        applies, missing = ff.form_applies(form, flat)
        self.assertFalse(applies)
        self.assertIn("case.resolution_notified", missing)
        md = ff.render_md("EX-17-familiar", "x", ff.fill_form(form, flat),
                          applies, missing)
        self.assertIn("НЕ относится к текущему этапу", md)
        # ...and the applicable case carries no such banner
        flat_post = ff.flatten(self.POST)
        applies2, missing2 = ff.form_applies(form, flat_post)
        self.assertTrue(applies2)
        md2 = ff.render_md("EX-17-familiar", "x", ff.fill_form(form, flat_post),
                           applies2, missing2)
        self.assertNotIn("НЕ относится к текущему этапу", md2)


class TestRealRegistryStageGating(unittest.TestCase):
    """The shipped registry must actually carry the gate (not just the code)."""

    def setUp(self):
        import json
        reg_path = HERE.parent.parent.parent / "knowledge_base" / "forms" / "registry.json"
        if not reg_path.is_file():
            self.skipTest(f"registry not found at {reg_path}")
        self.registry = json.loads(reg_path.read_text(encoding="utf-8"))

    def test_tie_stage_forms_are_gated(self):
        forms = self.registry["forms"]
        self.assertEqual(fq.applies_when_keys(forms["EX-17"]),
                         ["case.resolution_notified"])
        self.assertEqual(fq.applies_when_keys(forms["tasa-790-012"]),
                         ["case.resolution_notified"])
        self.assertEqual(sorted(fq.applies_when_keys(forms["EX-17-familiar"])),
                         ["case.resolution_notified", "family.present"])

    def test_submission_forms_are_not_gated(self):
        for fid in ("MI-T", "MI-F", "tasa-790-052", "memoria"):
            self.assertEqual(fq.applies_when_keys(self.registry["forms"][fid]), [],
                             f"{fid} must apply at every stage")

    def test_family_passport_is_honestly_alta(self):
        """The masking is gone: the field the reviewer caught is `alta` again."""
        by_name = {f["name"]: f for f in
                   self.registry["forms"]["EX-17-familiar"]["fields"]}
        self.assertEqual(by_name["Nº pasaporte"]["criticality"], "alta")
        self.assertEqual(by_name["N.I.E."]["criticality"], "alta")
        self.assertEqual(by_name["Sexo"]["criticality"], "alta")

    def test_gate_keys_exist_in_the_profile_schema(self):
        """A gate on a key the schema does not define would silently never fire."""
        import json
        schema_path = (HERE.parent.parent.parent / ".claude" / "skills" /
                       "dnv-intake" / "profile.schema.json")
        if not schema_path.is_file():
            self.skipTest("profile schema not found")
        props = json.loads(schema_path.read_text(encoding="utf-8"))["properties"]
        for fid, form in self.registry["forms"].items():
            for key in fq.applies_when_keys(form):
                self.assertIn(key, props, f"{fid}.applies_when -> unknown key {key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
