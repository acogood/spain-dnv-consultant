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
        return {(f, n): (v, why) for f, n, v, why in fq.diff(expected, REGISTRY, drafts)}

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
