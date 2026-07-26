"""
Tests for the privacy-critical chat scripts (anonymize_chat + build_digest +
_common). Stdlib unittest only — runnable from a clean clone with no deps:

    python -m unittest discover -s engine/scripts/chat -p "test_*.py"
    # or, from this directory:
    python -m unittest test_anonymize_digest -v

All fixtures are synthetic — there is NO real PII in this file.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402
import anonymize_chat as ac  # noqa: E402
import build_digest as bd  # noqa: E402

SALT = b"\x00" * 32  # fixed salt -> deterministic pseudonyms in tests

# Synthetic raw Telegram-style export (fictional names/ids only).
RAW = {
    "name": "Test Chat",
    "type": "public_supergroup",
    "id": 1,
    "messages": [
        {
            "id": 10, "type": "message", "date": "2025-10-01T10:00:00",
            "from": "Ivan Petrov", "from_id": "user111",
            "reactions": [{"emoji": "👍"}], "edited": "2025-10-01T10:05:00",
            "text": "Ivan Petrov: подал на продление в UGE, всё ок",
        },
        {
            "id": 11, "type": "message", "date": "2025-11-15T12:00:00",
            "from": "Ivan Petrov", "from_id": "user111",
            "text": [
                "Пишите мне ",
                {"type": "mention", "text": "@ivanp"},
                " или на ",
                {"type": "email", "text": "ivan@example.com"},
                " тел ",
                {"type": "phone", "text": "+34600111222"},
            ],
        },
        {
            "id": 12, "type": "message", "date": "2025-12-20T09:00:00",
            "from": "Maria", "from_id": "user222",
            "text": "UGE приняла выписку Wise, подтверждаю",
        },
        {
            "id": 13, "type": "message", "date": "2026-01-05T09:00:00",
            "from": "Sergey", "from_id": "user333",
            "text": "у меня тоже UGE приняла Wise без вопросов",
        },
        {
            "id": 14, "type": "service", "date": "2026-01-06T09:00:00",
            "actor": "Maria", "actor_id": "user222", "action": "invite_members",
            "members": ["Pavel Sidorov"], "text": "",
        },
        {
            "id": 15, "type": "message", "date": "2026-02-01T09:00:00",
            "from": "Pavel Sidorov", "from_id": "user444",
            "text": "ссылка на чат https://t.me/joinchat/secretXYZ заходите",
        },
    ],
}


class TestAnonymize(unittest.TestCase):
    def setUp(self):
        self.anon, self.roster, self.dropped, self.empty = ac.anonymize(
            RAW["messages"], SALT, min_token_len=4
        )
        self.by_id = {m["id"]: m for m in self.anon}

    def test_pseudonym_stability_and_distinctness(self):
        # same from_id (user111) on messages 10 & 11 -> same pseudonym
        self.assertEqual(self.by_id[10]["author"], self.by_id[11]["author"])
        # different from_id -> different pseudonym
        self.assertNotEqual(self.by_id[12]["author"], self.by_id[13]["author"])

    def test_keep_allowlist_only(self):
        allowed = {"id", "date", "text", "reply_to", "author", "topics"}
        for m in self.anon:
            self.assertTrue(set(m).issubset(allowed), f"unexpected keys: {set(m) - allowed}")
            # raw identity/metadata fields must be gone
            for forbidden in ("from", "from_id", "reactions", "edited", "actor"):
                self.assertNotIn(forbidden, m)

    def test_unknown_future_field_does_not_pass(self):
        msgs = [{"id": 99, "type": "message", "date": "2026-03-01T00:00:00",
                 "from": "X", "from_id": "user999", "text": "hi",
                 "some_future_identity_field": "LEAK"}]
        anon, *_ = ac.anonymize(msgs, SALT, 4)
        self.assertNotIn("some_future_identity_field", anon[0])

    def test_roster_name_stripped_from_text(self):
        # "Ivan Petrov" is in the roster (it's a 'from'); must be redacted in body
        self.assertNotIn("Ivan", self.by_id[10]["text"])
        self.assertNotIn("Petrov", self.by_id[10]["text"])
        self.assertIn("[имя]", self.by_id[10]["text"])

    def test_entity_redaction(self):
        t = self.by_id[11]["text"]
        self.assertIn("[@user]", t)
        self.assertIn("[email]", t)
        self.assertIn("[phone]", t)
        self.assertNotIn("ivan@example.com", t)
        self.assertNotIn("+34600111222", t)

    def test_service_message_dropped(self):
        self.assertNotIn(14, self.by_id)
        self.assertEqual(self.dropped, 1)

    def test_deeplink_redacted(self):
        self.assertNotIn("t.me/joinchat", self.by_id[15]["text"])
        self.assertIn("[ссылка]", self.by_id[15]["text"])

    def test_plaintext_email_phone_backstop(self):
        # Contact PII that appears as PLAIN text (no entity tag) must still go.
        t = ac.flatten_and_redact_text("пишите someone@example.com или +34 600 111 222")
        self.assertNotIn("someone@example.com", t)
        self.assertNotIn("600 111 222", t)
        self.assertIn("[email]", t)
        self.assertIn("[phone]", t)

    def test_phone_backstop_keeps_legal_refs(self):
        # No leading '+' -> not a phone; legal refs / money must survive intact.
        t = ac.flatten_and_redact_text("Ley 14/2013, art. 74, доход €2400 в месяц")
        self.assertIn("14/2013", t)
        self.assertIn("€2400", t)
        self.assertNotIn("[phone]", t)

    def test_idempotent(self):
        anon2, *_ = ac.anonymize(RAW["messages"], SALT, 4)
        self.assertEqual(self.anon, anon2)


class TestDigest(unittest.TestCase):
    def setUp(self):
        self.anon, *_ = ac.anonymize(RAW["messages"], SALT, 4)

    def _curation(self):
        return {
            "last_covered_date": "2026-02-01",
            "source": "synthetic test slices",
            "claims": [
                {"topic": "UGE_подача", "tag": "практика — Telegram",
                 "statement": "UGE принимает выписку Wise.",
                 "match": [r"UGE.*Wise|Wise.*UGE"]},
                {"topic": "доход_IPREM", "tag": "практика — Telegram",
                 "statement": "Единичное мнение по доходу.",
                 "supporting_ids": [10]},  # one author only -> must suppress
            ],
        }

    def test_single_author_claim_suppressed(self):
        pub, sup = bd.aggregate(self._curation(), self.anon, min_authors=2)
        statements = [r["statement"] for r in pub]
        self.assertIn("UGE принимает выписку Wise.", statements)
        self.assertNotIn("Единичное мнение по доходу.", statements)
        self.assertEqual(len(sup), 1)

    def test_published_has_no_raw_pii(self):
        pub, _ = bd.aggregate(self._curation(), self.anon, min_authors=2)
        blob = json.dumps(pub, ensure_ascii=False)
        # no message ids, no author pseudonyms, no raw text leak
        for leak in ("u_", '"id"', '"author"', "supporting_ids", "Wise приняла"):
            self.assertNotIn(leak, blob, f"leak in published digest: {leak}")
        self.assertIn("support", pub[0])
        self.assertIn("period", pub[0])

    def test_counts_reproducible(self):
        a, _ = bd.aggregate(self._curation(), self.anon, min_authors=2)
        b, _ = bd.aggregate(self._curation(), self.anon, min_authors=2)
        self.assertEqual(a, b)

    def test_band_reflects_distinct_authors(self):
        pub, _ = bd.aggregate(self._curation(), self.anon, min_authors=2)
        # messages 12 & 13 match (Maria, Sergey) -> 2 distinct -> "немного (2–4 чел.)"
        uge = next(r for r in pub if r["topic"] == "UGE_подача")
        self.assertEqual(uge["support"], "немного (2–4 чел.)")

    def test_load_slices_refuses_non_anonymized(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "raw.json"
            p.write_text(json.dumps([{"id": 1, "from_id": "user1", "text": "x"}]), encoding="utf-8")
            with self.assertRaises(_common.SafeIOError):
                bd.load_slices([str(p)], _common.DEFAULT_MAX_BYTES, _common.DEFAULT_MAX_DEPTH)


class TestLastCoveredDate(unittest.TestCase):
    """LAST_COVERED_DATE is DERIVED from the corpus, not copied from curation.

    The manual constant had already drifted from the data (curation said
    2026-06, the corpus reached 2026-07) — an internal contradiction inside one
    publication. Curation may only assert a FLOOR.
    """

    def _msgs(self, *dates):
        return [{"id": i, "author": f"u_{i}", "date": d, "text": "x"}
                for i, d in enumerate(dates, start=1)]

    def test_corpus_date_wins_over_older_curation(self):
        msgs = self._msgs("2026-05-02T10:00:00", "2026-07-24T18:30:00")
        lcd, warn = bd.resolve_last_covered({"last_covered_date": "2026-04-30"}, msgs)
        self.assertEqual(lcd, "2026-07-24")
        self.assertIsNone(warn)

    def test_curation_claiming_more_than_corpus_warns(self):
        msgs = self._msgs("2026-07-24T18:30:00")
        lcd, warn = bd.resolve_last_covered({"last_covered_date": "2026-09-01"}, msgs)
        self.assertEqual(lcd, "2026-07-24")          # data wins
        self.assertIsNotNone(warn)                    # but the drift is reported
        self.assertIn("2026-09-01", warn)
        self.assertIn("2026-07-24", warn)

    def test_curation_without_the_field(self):
        msgs = self._msgs("2026-03-01T00:00:00")
        lcd, warn = bd.resolve_last_covered({}, msgs)
        self.assertEqual(lcd, "2026-03-01")
        self.assertIsNone(warn)

    def test_no_parseable_dates_falls_back_deterministically(self):
        junk = [{"id": 1, "author": "u_1", "date": None, "text": "x"},
                {"id": 2, "author": "u_2", "date": "вчера", "text": "y"}]
        # curation value is the documented fallback...
        lcd, _ = bd.resolve_last_covered({"last_covered_date": "2026-04-30"}, junk)
        self.assertEqual(lcd, "2026-04-30")
        # ...and without one, the module's "no dates" marker — never "" and never a crash
        lcd2, _ = bd.resolve_last_covered({}, junk)
        self.assertEqual(lcd2, "—")

    def _run_main(self, curation, out="out"):
        """Run build_digest end-to-end in a temp cwd; return (out_dir, stdout)."""
        anon, *_ = ac.anonymize(RAW["messages"], SALT, 4)
        Path("slice.json").write_text(json.dumps(anon, ensure_ascii=False), encoding="utf-8")
        Path("cur.json").write_text(json.dumps(curation, ensure_ascii=False), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bd.main(["--curation", "cur.json", "--slices", "slice.json", "--out-dir", out])
        return Path(out), buf.getvalue()

    def _curation_for_main(self, **extra):
        c = {"source": "synthetic",
             "claims": [{"topic": "UGE_подача", "tag": "практика — Telegram",
                         "statement": "UGE принимает выписку Wise.",
                         "match": [r"UGE.*Wise|Wise.*UGE"]}]}
        c.update(extra)
        return c

    def test_end_to_end_writes_derived_date_and_is_reproducible(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            old = os.getcwd()
            try:
                os.chdir(d)
                cur = self._curation_for_main(last_covered_date="2025-01-01")
                out, _ = self._run_main(cur)
                first = {f: (out / f).read_bytes()
                         for f in ("LAST_COVERED_DATE", "digest.md", "digest.json")}
                # RAW's newest message is 2026-02-01 — NOT the curation constant
                self.assertEqual(first["LAST_COVERED_DATE"].decode("utf-8").strip(), "2026-02-01")
                self.assertIn("2026-02-01", first["digest.md"].decode("utf-8"))
                self._run_main(cur)  # byte-identical on re-run
                for f, blob in first.items():
                    self.assertEqual((out / f).read_bytes(), blob, f"{f} not reproducible")
            finally:
                os.chdir(old)

    def test_end_to_end_overclaiming_curation_warns_but_exits_clean(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            old = os.getcwd()
            try:
                os.chdir(d)
                # curation claims coverage the corpus does not have -> warn, don't fail
                out, stdout = self._run_main(self._curation_for_main(last_covered_date="2026-09-01"))
                self.assertEqual((out / "LAST_COVERED_DATE").read_text(encoding="utf-8").strip(),
                                 "2026-02-01")
                self.assertIn("2026-09-01", stdout)
            finally:
                os.chdir(old)


class TestCommonGuards(unittest.TestCase):
    def test_depth_guard(self):
        with self.assertRaises(_common.SafeIOError):
            _common.check_json_depth("[" * 500 + "]" * 500, max_depth=200)

    def test_depth_ignores_braces_in_strings(self):
        _common.check_json_depth('{"a": "[[[[[[[[[["}', max_depth=3)  # must not raise

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "big.json"
            p.write_text("[]", encoding="utf-8")
            with self.assertRaises(_common.SafeIOError):
                _common.load_json_safe(str(p), max_bytes=1)

    def test_output_containment_rejects_escape(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            old = os.getcwd()
            try:
                os.chdir(d)
                # legit nested path under the root is allowed
                ok = _common.resolve_output("sub/out.json", ".")
                self.assertTrue(str(ok).startswith(str(Path(d).resolve())))
                # `..` escape rejected
                with self.assertRaises(_common.SafeIOError):
                    _common.resolve_output("../../escape.json", ".")
                # absolute outside root rejected
                with self.assertRaises(_common.SafeIOError):
                    _common.resolve_output(str(Path(d).resolve().parent / "evil.json"), ".")
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main(verbosity=2)
